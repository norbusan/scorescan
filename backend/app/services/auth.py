from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User
from app.schemas.auth import UserCreate
from app.utils.security import verify_password, get_password_hash


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(user_data.password)
        user = User(email=user_data.email, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_email_registered(self, email: str) -> bool:
        """Check if an email is already registered."""
        return self.get_user_by_email(email) is not None
