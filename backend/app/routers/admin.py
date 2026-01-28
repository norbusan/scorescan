"""
Admin router for user management.

Only accessible by superusers.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.user import UserResponse
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_current_superuser(current_user: User = Depends(get_current_user)):
    """Dependency to ensure the current user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can access this endpoint",
        )
    return current_user


class UserApprovalRequest(BaseModel):
    """Request to approve or reject a user."""

    approved: bool


class UserListResponse(BaseModel):
    """Response for user list with statistics."""

    users: List[UserResponse]
    total: int
    pending: int
    approved: int
    superusers: int


@router.get("/users", response_model=UserListResponse)
def list_all_users(
    current_user: User = Depends(get_current_superuser), db: Session = Depends(get_db)
):
    """
    Get all users in the system.

    Only accessible by superusers.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()

    # Calculate statistics
    total = len(users)
    pending = sum(1 for u in users if not u.is_approved)
    approved = sum(1 for u in users if u.is_approved)
    superusers = sum(1 for u in users if u.is_superuser)

    return UserListResponse(
        users=users,
        total=total,
        pending=pending,
        approved=approved,
        superusers=superusers,
    )


@router.get("/users/pending", response_model=List[UserResponse])
def list_pending_users(
    current_user: User = Depends(get_current_superuser), db: Session = Depends(get_db)
):
    """
    Get all users pending approval.

    Only accessible by superusers.
    """
    users = (
        db.query(User)
        .filter(User.is_approved == False)
        .order_by(User.created_at.desc())
        .all()
    )

    return users


@router.post("/users/{user_id}/approve")
def approve_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """
    Approve a user account.

    Only accessible by superusers.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_approved:
        return {"message": "User is already approved"}

    user.is_approved = True
    db.commit()
    db.refresh(user)

    return {
        "message": f"User {user.email} has been approved",
        "user": UserResponse.model_validate(user),
    }


@router.post("/users/{user_id}/reject")
def reject_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """
    Reject a user account (deletes the user).

    Only accessible by superusers.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject a superuser account",
        )

    email = user.email
    db.delete(user)
    db.commit()

    return {"message": f"User {email} has been rejected and deleted"}


@router.patch("/users/{user_id}/approval", response_model=UserResponse)
def update_user_approval(
    user_id: str,
    approval_data: UserApprovalRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """
    Update user approval status.

    Only accessible by superusers.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_approved = approval_data.approved
    db.commit()
    db.refresh(user)

    return user


@router.post("/users/{user_id}/make-superuser")
def make_superuser(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """
    Grant superuser privileges to a user.

    Only accessible by superusers.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_superuser:
        return {"message": "User is already a superuser"}

    user.is_superuser = True
    user.is_approved = True  # Superusers must be approved
    db.commit()
    db.refresh(user)

    return {
        "message": f"User {user.email} is now a superuser",
        "user": UserResponse.model_validate(user),
    }


@router.delete("/users/{user_id}/superuser")
def revoke_superuser(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """
    Revoke superuser privileges from a user.

    Only accessible by superusers.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot revoke your own superuser privileges",
        )

    if not user.is_superuser:
        return {"message": "User is not a superuser"}

    user.is_superuser = False
    db.commit()
    db.refresh(user)

    return {
        "message": f"Superuser privileges revoked from {user.email}",
        "user": UserResponse.model_validate(user),
    }
