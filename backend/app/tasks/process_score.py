import logging
from datetime import datetime
from celery import current_task

from app.tasks import celery_app
from app.database import SessionLocal
from app.models.job import Job, JobStatus
from app.services.omr import OMRService
from app.services.transpose import TransposeService
from app.services.pdf import PDFService

logger = logging.getLogger(__name__)


def update_job_status(
    job_id: str,
    status: JobStatus,
    progress: int = 0,
    error_message: str = None,
    musicxml_path: str = None,
    pdf_path: str = None,
):
    """Update job status in database."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status.value
            job.progress = progress
            if error_message:
                job.error_message = error_message
            if musicxml_path:
                job.musicxml_path = musicxml_path
            if pdf_path:
                job.pdf_path = pdf_path
            if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@celery_app.task(bind=True, name="process_score")
def process_score_task(
    self,
    job_id: str,
    user_id: str,
    upload_path: str,
    transpose_semitones: int = None,
    transpose_from_key: str = None,
    transpose_to_key: str = None,
):
    """
    Main task for processing a music score image.

    Pipeline:
    1. Run OMR (Audiveris) to convert image to MusicXML
    2. Transpose if requested
    3. Convert to PDF (MuseScore)

    Args:
        job_id: Job identifier
        user_id: User identifier
        upload_path: Relative path to uploaded image
        transpose_semitones: Semitones to transpose (optional)
        transpose_from_key: Source key for key-based transposition (optional)
        transpose_to_key: Target key for key-based transposition (optional)
    """
    logger.info(f"Starting processing for job {job_id}")

    try:
        # Update status to processing
        update_job_status(job_id, JobStatus.PROCESSING, progress=0)

        # Step 1: OMR - Convert image to MusicXML (0-50%)
        logger.info(f"Step 1: Running OMR on {upload_path}")
        update_job_status(job_id, JobStatus.PROCESSING, progress=10)

        omr_service = OMRService()
        success, musicxml_path, error = omr_service.process_image(
            upload_path, user_id, job_id
        )

        if not success:
            logger.error(f"OMR failed for job {job_id}: {error}")
            update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=f"Score recognition failed: {error}",
            )
            return {"success": False, "error": error}

        update_job_status(
            job_id, JobStatus.PROCESSING, progress=50, musicxml_path=musicxml_path
        )

        # Step 2: Transpose if requested (50-70%)
        if transpose_semitones or (transpose_from_key and transpose_to_key):
            logger.info(f"Step 2: Transposing score for job {job_id}")
            update_job_status(job_id, JobStatus.PROCESSING, progress=55)

            transpose_service = TransposeService()

            if transpose_semitones:
                success, _, error = transpose_service.transpose_by_semitones(
                    musicxml_path, transpose_semitones
                )
            else:
                success, _, error = transpose_service.transpose_by_key(
                    musicxml_path, transpose_from_key, transpose_to_key
                )

            if not success:
                logger.error(f"Transposition failed for job {job_id}: {error}")
                update_job_status(
                    job_id,
                    JobStatus.FAILED,
                    error_message=f"Transposition failed: {error}",
                )
                return {"success": False, "error": error}

        update_job_status(job_id, JobStatus.PROCESSING, progress=70)

        # Step 3: Convert to PDF (70-100%)
        logger.info(f"Step 3: Converting to PDF for job {job_id}")
        update_job_status(job_id, JobStatus.PROCESSING, progress=75)

        pdf_service = PDFService()
        success, pdf_path, error = pdf_service.convert_to_pdf(
            musicxml_path, user_id, job_id
        )

        if not success:
            logger.error(f"PDF conversion failed for job {job_id}: {error}")
            update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=f"PDF conversion failed: {error}",
            )
            return {"success": False, "error": error}

        # Success!
        logger.info(f"Job {job_id} completed successfully")
        update_job_status(job_id, JobStatus.COMPLETED, progress=100, pdf_path=pdf_path)

        return {
            "success": True,
            "job_id": job_id,
            "musicxml_path": musicxml_path,
            "pdf_path": pdf_path,
        }

    except Exception as e:
        logger.exception(f"Unexpected error processing job {job_id}")
        update_job_status(
            job_id, JobStatus.FAILED, error_message=f"Processing error: {str(e)}"
        )
        return {"success": False, "error": str(e)}
