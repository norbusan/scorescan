import subprocess
import os
import logging
from typing import Optional, Tuple

from app.config import get_settings
from app.utils.storage import get_file_path, get_pdf_output_path

settings = get_settings()
logger = logging.getLogger(__name__)


class PDFService:
    """
    Service for converting MusicXML files to PDF using MuseScore.
    """

    def __init__(self):
        self.musescore_path = settings.musescore_path

    def convert_to_pdf(
        self, musicxml_path: str, user_id: str, job_id: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convert a MusicXML file to PDF using MuseScore.

        Args:
            musicxml_path: Relative path to MusicXML file
            user_id: User ID for organizing output
            job_id: Job ID for naming the output file

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            abs_input = get_file_path(musicxml_path)
            output_rel_path = get_pdf_output_path(user_id, job_id)
            abs_output = get_file_path(output_rel_path)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(abs_output), exist_ok=True)

            logger.info(f"Converting {musicxml_path} to PDF")

            # Run MuseScore in batch mode
            # MuseScore 4 command line: musescore -o output.pdf input.musicxml
            result = subprocess.run(
                [
                    self.musescore_path,
                    "--appimage-extract-and-run",  # For AppImage
                    "-o",
                    abs_output,
                    abs_input,
                ],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},  # Headless mode
            )

            # MuseScore may return non-zero but still produce output
            if not os.path.exists(abs_output):
                # Try alternative command without appimage flag
                result = subprocess.run(
                    [self.musescore_path, "-o", abs_output, abs_input],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                )

            if os.path.exists(abs_output):
                logger.info(f"PDF conversion complete: {output_rel_path}")
                return True, output_rel_path, None
            else:
                error_msg = f"MuseScore failed to produce PDF: {result.stderr}"
                logger.error(error_msg)
                return False, None, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "PDF conversion timed out (exceeded 2 minutes)"
            logger.error(error_msg)
            return False, None, error_msg
        except FileNotFoundError:
            error_msg = f"MuseScore not found at {self.musescore_path}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"PDF conversion error: {str(e)}"
            logger.exception(error_msg)
            return False, None, error_msg

    def is_available(self) -> bool:
        """Check if MuseScore is available and working."""
        try:
            result = subprocess.run(
                [self.musescore_path, "--version"], capture_output=True, timeout=10
            )
            return True  # MuseScore may return non-zero for --version
        except Exception:
            return False
