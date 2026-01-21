from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(String(20), default=JobStatus.PENDING.value)
    progress = Column(Integer, default=0)  # 0-100

    # File paths
    original_filename = Column(String(255), nullable=False)
    upload_path = Column(String(500), nullable=False)
    musicxml_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)

    # Transposition settings
    transpose_semitones = Column(Integer, nullable=True)  # -12 to +12
    transpose_from_key = Column(String(10), nullable=True)  # e.g., "C", "Bb"
    transpose_to_key = Column(String(10), nullable=True)  # e.g., "F", "Eb"

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Celery task ID for tracking
    celery_task_id = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")

    def __repr__(self):
        return f"<Job {self.id} - {self.status}>"
