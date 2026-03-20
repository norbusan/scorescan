from typing import Optional
import logging
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    RefreshToken,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
)
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.utils.token_blacklist import (
    blacklist_token,
    increment_password_generation,
    create_download_token,
    validate_download_token,
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)


def _remaining_ttl(payload: dict) -> int:
    """Seconds until the token expires (min 0)."""
    exp = payload.get("exp", 0)
    return max(0, int(exp - datetime.utcnow().timestamp()))


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = verify_token(token, "access")
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is pending approval",
        )

    return user


def _get_current_user_token_pair(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Return (user, raw_token, payload) so the caller can blacklist the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = verify_token(token, "access")
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    if not user.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is pending approval")

    return user, token, payload


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/hour")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    auth_service = AuthService(db)

    if auth_service.is_email_registered(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = auth_service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login and get access/refresh tokens."""
    auth_service = AuthService(db)

    user = auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an administrator",
        )

    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email})

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
def refresh_token(
    request: Request, refresh_data: RefreshToken, db: Session = Depends(get_db)
):
    """Get new access token using refresh token."""
    payload = verify_token(refresh_data.refresh_token, "refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    email = payload.get("email")

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is pending approval",
        )

    # Blacklist the old refresh token so it can't be reused
    old_jti = payload.get("jti")
    if old_jti:
        blacklist_token(old_jti, _remaining_ttl(payload))

    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email})

    return Token(
        access_token=access_token, refresh_token=new_refresh_token, token_type="bearer"
    )


@router.post("/logout")
def logout(
    data: tuple = Depends(_get_current_user_token_pair),
):
    """Logout — blacklist the current access token server-side."""
    user, token, payload = data
    jti = payload.get("jti")
    if jti:
        blacklist_token(jti, _remaining_ttl(payload))
    return {"message": "Successfully logged out"}


@router.post("/password-reset/request")
@limiter.limit("3/hour")
def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset. Sends an email with reset link.
    Always returns success even if email not found (security best practice).
    """
    from app.models.password_reset import PasswordResetToken
    from app.services.email import email_service

    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(reset_request.email)

    if user:
        # Invalidate all existing reset tokens for this user before creating a new one
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == "0",
        ).update({"used": "1"})
        db.flush()

        token = PasswordResetToken.generate_token()
        expires_at = datetime.utcnow() + timedelta(
            hours=settings.password_reset_token_expire_hours
        )

        reset_token = PasswordResetToken(
            user_id=user.id, token=token, expires_at=expires_at
        )

        db.add(reset_token)
        db.commit()

        email_service.send_password_reset_email(user.email, token)

    # Always return success to prevent email enumeration
    return {
        "message": "If the email exists, a password reset link has been sent",
        "success": True,
    }


@router.post("/password-reset/confirm")
@limiter.limit("5/minute")
def confirm_password_reset(
    request: Request,
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Confirm password reset with token and set new password."""
    from app.models.password_reset import PasswordResetToken
    from passlib.context import CryptContext

    # Find the token
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == reset_confirm.token)
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if reset_token.is_expired():
        db.delete(reset_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    if reset_token.is_used():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used",
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(reset_token.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
        )

    # Update password
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.hashed_password = pwd_context.hash(reset_confirm.new_password)

    # Mark token as used
    reset_token.mark_as_used()

    # Invalidate all remaining reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == "0",
    ).update({"used": "1"})

    db.commit()

    # Invalidate all existing JWT tokens by bumping password generation
    increment_password_generation(user.id)

    return {"message": "Password has been reset successfully", "success": True}


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the current user's password.
    Requires authentication and current password verification.
    """
    auth_service = AuthService(db)

    success = auth_service.change_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Invalidate all existing JWT tokens by bumping password generation
    increment_password_generation(current_user.id)

    return {"message": "Password changed successfully", "success": True}


# --- Download token endpoint (replaces JWT-in-URL pattern) ---


@router.post("/download-token/{job_id}")
def generate_download_token(
    job_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a short-lived, single-use download token for a specific job.
    Used by the frontend to construct download URLs without exposing the JWT.
    """
    from app.models.job import Job

    # Verify the user owns this job
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    token = create_download_token(current_user.id, job_id)
    return {"download_token": token, "expires_in": 60}
