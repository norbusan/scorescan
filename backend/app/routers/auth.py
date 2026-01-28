from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    RefreshToken,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Dependency to get the current authenticated user."""
    if settings.debug:
        logger.debug(f"[AUTH DEBUG] get_current_user: Validating access token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] get_current_user: No token provided")
        raise credentials_exception

    payload = verify_token(token, "access")
    if payload is None:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] get_current_user: Invalid or expired token")
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] get_current_user: Token missing 'sub' claim")
        raise credentials_exception

    if settings.debug:
        logger.debug(f"[AUTH DEBUG] get_current_user: Token valid, user_id={user_id}")

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)

    if user is None:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] get_current_user: User not found in database")
        raise credentials_exception

    if not user.is_active:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] get_current_user: User account is disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    if not user.is_approved:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] get_current_user: User account pending approval"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is pending approval",
        )

    if settings.debug:
        logger.debug(f"[AUTH DEBUG] get_current_user: Success - user={user.email}")

    return user


def get_current_user_from_token_or_query(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    query_token: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
):
    """
    Dependency to get the current authenticated user from either:
    - Authorization header (Bearer token)
    - Query parameter (?token=...)

    This is useful for file downloads where the browser can't easily set headers.
    """
    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] get_current_user_from_token_or_query: Validating token"
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try header token first, then query parameter
    actual_token = token or query_token

    if settings.debug:
        token_source = "header" if token else ("query" if query_token else "none")
        logger.debug(
            f"[AUTH DEBUG] get_current_user_from_token_or_query: Token source={token_source}"
        )

    if actual_token is None:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] get_current_user_from_token_or_query: No token provided"
            )
        raise credentials_exception

    payload = verify_token(actual_token, "access")
    if payload is None:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] get_current_user_from_token_or_query: Invalid token"
            )
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] get_current_user_from_token_or_query: Missing user_id"
            )
        raise credentials_exception

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] get_current_user_from_token_or_query: user_id={user_id}"
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)

    if user is None:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] get_current_user_from_token_or_query: User not found"
            )
        raise credentials_exception

    if not user.is_active:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] get_current_user_from_token_or_query: User inactive"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    if not user.is_approved:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] get_current_user_from_token_or_query: User not approved"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is pending approval",
        )

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] get_current_user_from_token_or_query: Success - user={user.email}"
        )

    return user


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /register: Attempting to register user: {user_data.email}"
        )

    auth_service = AuthService(db)

    if auth_service.is_email_registered(user_data.email):
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] /register: Email already registered: {user_data.email}"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = auth_service.create_user(user_data)

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /register: User registered successfully: {user.email}, "
            f"is_approved={user.is_approved}, requires approval"
        )

    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login and get access/refresh tokens."""
    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /login: Login attempt for user: {form_data.username}"
        )

    auth_service = AuthService(db)

    user = auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] /login: Authentication failed for: {form_data.username}"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if settings.debug:
        logger.debug(f"[AUTH DEBUG] /login: User authenticated, checking status...")
        logger.debug(
            f"[AUTH DEBUG] /login: is_active={user.is_active}, "
            f"is_approved={user.is_approved}, is_superuser={user.is_superuser}"
        )

    if not user.is_active:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /login: Account disabled for: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    if not user.is_approved:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] /login: Account pending approval for: {user.email}"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an administrator",
        )

    if settings.debug:
        logger.debug(f"[AUTH DEBUG] /login: Creating tokens for user: {user.email}")

    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email})

    if settings.debug:
        logger.debug(f"[AUTH DEBUG] /login: Login successful for: {user.email}")

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
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
def refresh_token(refresh_data: RefreshToken, db: Session = Depends(get_db)):
    """Get new access token using refresh token."""
    if settings.debug:
        logger.debug(f"[AUTH DEBUG] /refresh: Attempting to refresh token")

    payload = verify_token(refresh_data.refresh_token, "refresh")

    if payload is None:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /refresh: Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    email = payload.get("email")

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /refresh: Token valid for user_id={user_id}, email={email}"
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)

    if not user or not user.is_active:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /refresh: User not found or inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if not user.is_approved:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /refresh: User account pending approval")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is pending approval",
        )

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /refresh: Creating new tokens for user: {user.email}"
        )

    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email})

    if settings.debug:
        logger.debug(f"[AUTH DEBUG] /refresh: Token refresh successful")

    return Token(
        access_token=access_token, refresh_token=new_refresh_token, token_type="bearer"
    )


@router.post("/logout")
def logout():
    """Logout (client should discard tokens)."""
    # JWT tokens are stateless, so we just return success
    # Client is responsible for discarding tokens
    return {"message": "Successfully logged out"}


@router.post("/password-reset/request")
def request_password_reset(
    reset_request: PasswordResetRequest, db: Session = Depends(get_db)
):
    """
    Request a password reset. Sends an email with reset link.
    Always returns success even if email not found (security best practice).
    """
    from datetime import datetime, timedelta
    from app.models.password_reset import PasswordResetToken
    from app.services.email import email_service

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /password-reset/request: Request for email: {reset_request.email}"
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(reset_request.email)

    if user:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] /password-reset/request: User found, creating token"
            )

        # Create password reset token
        token = PasswordResetToken.generate_token()
        expires_at = datetime.utcnow() + timedelta(
            hours=settings.password_reset_token_expire_hours
        )

        reset_token = PasswordResetToken(
            user_id=user.id, token=token, expires_at=expires_at
        )

        db.add(reset_token)
        db.commit()

        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] /password-reset/request: Token created, sending email"
            )

        # Send email
        email_service.send_password_reset_email(user.email, token)

        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] /password-reset/request: Email sent to {user.email}"
            )
    else:
        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] /password-reset/request: User not found (returning success anyway)"
            )

    # Always return success to prevent email enumeration
    return {
        "message": "If the email exists, a password reset link has been sent",
        "success": True,
    }


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_confirm: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """
    Confirm password reset with token and set new password.
    """
    from datetime import datetime
    from app.models.password_reset import PasswordResetToken
    from passlib.context import CryptContext

    if settings.debug:
        logger.debug(f"[AUTH DEBUG] /password-reset/confirm: Validating token")

    # Find the token
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == reset_confirm.token)
        .first()
    )

    if not reset_token:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /password-reset/confirm: Token not found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if token is expired
    if reset_token.is_expired():
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /password-reset/confirm: Token expired")
        db.delete(reset_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Check if token is already used
    if reset_token.is_used():
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /password-reset/confirm: Token already used")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used",
        )

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /password-reset/confirm: Token valid, updating password"
        )

    # Get the user
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(reset_token.user_id)

    if not user:
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] /password-reset/confirm: User not found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
        )

    # Update password
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.hashed_password = pwd_context.hash(reset_confirm.new_password)

    # Mark token as used
    reset_token.mark_as_used()

    db.commit()

    if settings.debug:
        logger.debug(
            f"[AUTH DEBUG] /password-reset/confirm: Password updated successfully for {user.email}"
        )

    return {"message": "Password has been reset successfully", "success": True}
