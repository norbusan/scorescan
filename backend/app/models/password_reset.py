from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import secrets

from app.database import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(
        String(1), default="0"
    )  # SQLite doesn't have native boolean, use "0"/"1"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User")

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    def is_expired(self) -> bool:
        """Check if the token has expired"""
        return datetime.utcnow() > self.expires_at

    def is_used(self) -> bool:
        """Check if the token has been used"""
        return self.used == "1"

    def mark_as_used(self):
        """Mark the token as used"""
        self.used = "1"

    def __repr__(self):
        return f"<PasswordResetToken {self.token[:8]}... for user {self.user_id}>"
