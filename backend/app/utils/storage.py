import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from PIL import Image, ImageSequence

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


# Magic numbers of the accepted formats, keyed by file extension
_SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "pdf": (b"%PDF-",),
    "tif": (b"II*\x00", b"MM\x00*"),
    "tiff": (b"II*\x00", b"MM\x00*"),
}


def validate_file_signature(filename: str, header: bytes) -> bool:
    """Check that the file content starts with the magic number of its extension."""
    ext = Path(filename).suffix.lower().lstrip(".")
    return any(header.startswith(sig) for sig in _SIGNATURES.get(ext, ()))


def check_input_limits(path: str) -> Optional[str]:
    """Return a user-facing error if the file has too many pages or pixels."""
    max_pages = settings.max_pages
    max_mp = settings.max_image_megapixels
    try:
        if path.lower().endswith(".pdf"):
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(path)
            try:
                n_pages = len(pdf)
            finally:
                pdf.close()
            if n_pages == 0:
                return "The PDF has no pages."
            if n_pages > max_pages:
                return f"The PDF has {n_pages} pages; the maximum is {max_pages}."
            # Page pixel size is capped at render time instead
            return None

        with Image.open(path) as im:
            n_pages = getattr(im, "n_frames", 1)
            if n_pages > max_pages:
                return f"The file has {n_pages} pages; the maximum is {max_pages}."
            for frame in ImageSequence.Iterator(im):
                w, h = frame.size
                if w * h > max_mp * 1_000_000:
                    return (
                        f"The image is too large ({w}x{h}); the maximum is "
                        f"{max_mp} megapixels."
                    )
        return None
    except Image.DecompressionBombError:
        return f"The image is too large; the maximum is {max_mp} megapixels."
    except Exception:
        return "The file could not be read as an image or PDF."


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    return os.path.getsize(filepath) / (1024 * 1024)
