from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.models.user import User
from app.schemas.auth import UserCreate
from app.utils.security import verify_password, get_password_hash
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Verified against when the user does not exist, so failed logins take the
# same time for unknown and known emails
_DUMMY_HASH = get_password_hash("timing-equalizer-not-a-password")


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] Looking up user by email: {email}")

        user = self.db.query(User).filter(User.email == email).first()

        if settings.debug:
            if user:
                logger.debug(
                    f"[AUTH DEBUG] User found: id={user.id}, email={user.email}, "
                    f"is_active={user.is_active}, is_approved={user.is_approved}, "
                    f"is_superuser={user.is_superuser}"
                )
            else:
                logger.debug(f"[AUTH DEBUG] User not found for email: {email}")

        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] Looking up user by ID: {user_id}")

        user = self.db.query(User).filter(User.id == user_id).first()

        if settings.debug:
            if user:
                logger.debug(
                    f"[AUTH DEBUG] User found: id={user.id}, email={user.email}, "
                    f"is_active={user.is_active}, is_approved={user.is_approved}, "
                    f"is_superuser={user.is_superuser}"
                )
            else:
                logger.debug(f"[AUTH DEBUG] User not found for ID: {user_id}")

        return user

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] Creating new user: email={user_data.email}")

        hashed_password = get_password_hash(user_data.password)
        user = User(email=user_data.email, hashed_password=hashed_password)

        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] New user defaults: is_active={user.is_active}, "
                f"is_approved={user.is_approved}, is_superuser={user.is_superuser}"
            )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] User created successfully: id={user.id}, email={user.email}, "
                f"is_approved={user.is_approved}"
            )

        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] Authenticating user: {email}")

        user = self.get_user_by_email(email)
        if not user:
            verify_password(password, _DUMMY_HASH)
            if settings.debug:
                logger.debug(f"[AUTH DEBUG] Authentication failed: user not found")
            return None

        if settings.debug:
            logger.debug(f"[AUTH DEBUG] User found, verifying password...")

        if not verify_password(password, user.hashed_password):
            if settings.debug:
                logger.debug(f"[AUTH DEBUG] Authentication failed: invalid password")
            return None

        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] Password verified successfully for user: {email}"
            )

        return user

    @staticmethod
    def burn_password_hash(password: str) -> None:
        """Hash and discard, to match the timing of creating a user."""
        get_password_hash(password)

    def is_email_registered(self, email: str) -> bool:
        """Check if an email is already registered."""
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] Checking if email is registered: {email}")

        is_registered = self.get_user_by_email(email) is not None

        if settings.debug:
            logger.debug(f"[AUTH DEBUG] Email {email} registered: {is_registered}")

        return is_registered

    def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password.

        Args:
            user: The user whose password to change
            current_password: The user's current password
            new_password: The new password to set

        Returns:
            True if password changed successfully, False if current password is incorrect
        """
        if settings.debug:
            logger.debug(f"[AUTH DEBUG] Changing password for user: {user.email}")

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            if settings.debug:
                logger.debug(
                    f"[AUTH DEBUG] Password change failed: incorrect current password"
                )
            return False

        # Update password
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()

        if settings.debug:
            logger.debug(
                f"[AUTH DEBUG] Password changed successfully for user: {user.email}"
            )

        return True
