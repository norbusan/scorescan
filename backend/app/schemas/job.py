from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.job import JobStatus


class TransposeOptions(BaseModel):
    """Options for transposing the score."""

    # Semitone-based transposition (-12 to +12)
    semitones: Optional[int] = Field(None, ge=-12, le=12)

    # Key-based transposition
    from_key: Optional[str] = Field(None, pattern=r"^[A-G][b#]?(m|min|maj)?$")
    to_key: Optional[str] = Field(None, pattern=r"^[A-G][b#]?(m|min|maj)?$")


class JobCreate(BaseModel):
    """Request body for creating a new job (metadata only, file is separate)."""

    transpose: Optional[TransposeOptions] = None


class JobResponse(BaseModel):
    """Response model for a single job."""

    id: str
    status: str
    progress: int
    original_filename: str
    transpose_semitones: Optional[int] = None
    transpose_from_key: Optional[str] = None
    transpose_to_key: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    has_pdf: bool = False
    has_musicxml: bool = False

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response model for listing jobs."""

    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobStatusUpdate(BaseModel):
    """Internal model for updating job status."""

    status: JobStatus
    progress: Optional[int] = None
    error_message: Optional[str] = None
    musicxml_path: Optional[str] = None
    pdf_path: Optional[str] = None
