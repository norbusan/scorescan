import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid
import json

from app.database import get_db
from app.models.job import Job, JobStatus
from app.models.user import User
from app.schemas.job import JobResponse, JobListResponse, TransposeOptions
from app.routers.auth import get_current_user
from app.utils.storage import (
    save_upload_file,
    validate_file_extension,
    get_file_path,
    delete_file,
)
from app.config import get_settings
from app.tasks.process_score import process_score_task

router = APIRouter(prefix="/jobs", tags=["Jobs"])
settings = get_settings()


def job_to_response(job: Job) -> JobResponse:
    """Convert Job model to JobResponse schema."""
    return JobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        original_filename=job.original_filename,
        transpose_semitones=job.transpose_semitones,
        transpose_from_key=job.transpose_from_key,
        transpose_to_key=job.transpose_to_key,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        has_pdf=job.pdf_path is not None,
        has_musicxml=job.musicxml_path is not None,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    file: UploadFile = File(...),
    transpose_semitones: Optional[int] = Form(None),
    transpose_from_key: Optional[str] = Form(None),
    transpose_to_key: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new score processing job.

    Upload a music score image and optionally specify transposition settings.
    The score will be processed asynchronously.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    # Check file size (read content to check)
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    if file_size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    # Reset file position after reading
    await file.seek(0)

    # Validate transposition options
    if transpose_semitones is not None:
        if transpose_semitones < -12 or transpose_semitones > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transpose semitones must be between -12 and +12",
            )

    if (transpose_from_key and not transpose_to_key) or (
        transpose_to_key and not transpose_from_key
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both from_key and to_key must be provided for key-based transposition",
        )

    # Create job record
    job_id = str(uuid.uuid4())

    # Save uploaded file
    upload_path = await save_upload_file(file, current_user.id, job_id)

    # Create job in database
    job = Job(
        id=job_id,
        user_id=current_user.id,
        status=JobStatus.PENDING.value,
        original_filename=file.filename,
        upload_path=upload_path,
        transpose_semitones=transpose_semitones,
        transpose_from_key=transpose_from_key,
        transpose_to_key=transpose_to_key,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Queue the processing task
    task = process_score_task.delay(
        job_id=job_id,
        user_id=current_user.id,
        upload_path=upload_path,
        transpose_semitones=transpose_semitones,
        transpose_from_key=transpose_from_key,
        transpose_to_key=transpose_to_key,
    )

    # Update job with celery task ID
    job.celery_task_id = task.id
    db.commit()

    return job_to_response(job)


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all jobs for the current user with pagination."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 10

    # Get total count
    total = db.query(Job).filter(Job.user_id == current_user.id).count()

    # Get paginated jobs
    jobs = (
        db.query(Job)
        .filter(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    total_pages = (total + page_size - 1) // page_size

    return JobListResponse(
        jobs=[job_to_response(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific job."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return job_to_response(job)


@router.get("/{job_id}/download/pdf")
def download_pdf(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the generated PDF for a completed job."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not completed"
        )

    if not job.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not available"
        )

    file_path = get_file_path(job.pdf_path)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found"
        )

    # Generate download filename
    original_name = os.path.splitext(job.original_filename)[0]
    download_name = f"{original_name}_processed.pdf"

    return FileResponse(
        path=file_path, filename=download_name, media_type="application/pdf"
    )


@router.get("/{job_id}/download/musicxml")
def download_musicxml(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the generated MusicXML for a completed job."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if not job.musicxml_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="MusicXML not available"
        )

    file_path = get_file_path(job.musicxml_path)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="MusicXML file not found"
        )

    # Generate download filename
    original_name = os.path.splitext(job.original_filename)[0]
    download_name = f"{original_name}.musicxml"

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type="application/vnd.recordare.musicxml+xml",
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a job and all associated files."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Delete associated files
    if job.upload_path:
        delete_file(job.upload_path)
    if job.musicxml_path:
        delete_file(job.musicxml_path)
    if job.pdf_path:
        delete_file(job.pdf_path)

    # Delete job record
    db.delete(job)
    db.commit()

    return None
