import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.config import get_settings

settings = get_settings()


def ensure_directories():
    """Ensure all storage directories exist."""
    os.makedirs(settings.upload_path, exist_ok=True)
    os.makedirs(settings.musicxml_path, exist_ok=True)
    os.makedirs(settings.pdf_path, exist_ok=True)


async def save_upload_file(file: UploadFile, user_id: str, job_id: str) -> str:
    """
    Save an uploaded file to the storage directory.
    Returns the relative path to the saved file.
    """
    ensure_directories()

    # Create user-specific directory
    user_dir = os.path.join(settings.upload_path, user_id)
    os.makedirs(user_dir, exist_ok=True)

    # Get file extension
    original_filename = file.filename or "upload"
    ext = Path(original_filename).suffix.lower()

    # Generate unique filename
    filename = f"{job_id}{ext}"
    filepath = os.path.join(user_dir, filename)

    # Save file
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Return relative path
    return os.path.join("uploads", user_id, filename)


def get_file_path(relative_path: str) -> str:
    """Convert a relative storage path to absolute path."""
    return os.path.join(settings.storage_path, relative_path)


def get_absolute_path(relative_path: str) -> str:
    """Alias for get_file_path."""
    return get_file_path(relative_path)


def delete_file(relative_path: str) -> bool:
    """Delete a file from storage. Returns True if successful."""
    try:
        filepath = get_file_path(relative_path)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception:
        return False


def get_musicxml_path(user_id: str, job_id: str) -> str:
    """Generate the MusicXML output path for a job."""
    user_dir = os.path.join(settings.musicxml_path, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join("musicxml", user_id, f"{job_id}.musicxml")


def get_pdf_output_path(user_id: str, job_id: str) -> str:
    """Generate the PDF output path for a job."""
    user_dir = os.path.join(settings.pdf_path, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join("pdf", user_id, f"{job_id}.pdf")


def validate_file_extension(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext in settings.allowed_extensions


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    return os.path.getsize(filepath) / (1024 * 1024)
