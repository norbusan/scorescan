import subprocess
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

from app.config import get_settings
from app.utils.storage import get_file_path, get_musicxml_path

settings = get_settings()
logger = logging.getLogger(__name__)


class OMRService:
    """
    Optical Music Recognition service using Audiveris.
    Converts music score images to MusicXML format.
    """

    def __init__(self):
        self.audiveris_path = settings.audiveris_path

    def process_image(
        self, input_path: str, user_id: str, job_id: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process an image file with Audiveris to generate MusicXML.

        Args:
            input_path: Relative path to the input image file
            user_id: User ID for organizing output
            job_id: Job ID for naming the output file

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            # Get absolute paths
            abs_input_path = get_file_path(input_path)
            output_rel_path = get_musicxml_path(user_id, job_id)
            abs_output_dir = os.path.dirname(get_file_path(output_rel_path))

            # Ensure output directory exists
            os.makedirs(abs_output_dir, exist_ok=True)

            logger.info(f"Starting OMR processing for {abs_input_path}")

            # Run Audiveris in batch mode
            # Audiveris outputs to a directory, we need to find the .mxl or .musicxml file
            result = subprocess.run(
                [
                    self.audiveris_path,
                    "-batch",
                    "-export",
                    "-output",
                    abs_output_dir,
                    abs_input_path,
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = f"Audiveris failed: {result.stderr}"
                logger.error(error_msg)
                return False, None, error_msg

            # Find the output file (Audiveris names it based on input filename)
            input_stem = Path(abs_input_path).stem
            possible_outputs = [
                os.path.join(abs_output_dir, f"{input_stem}.mxl"),
                os.path.join(abs_output_dir, f"{input_stem}.musicxml"),
                os.path.join(abs_output_dir, f"{input_stem}.xml"),
            ]

            output_file = None
            for path in possible_outputs:
                if os.path.exists(path):
                    output_file = path
                    break

            if not output_file:
                # Check for any musicxml-like file in the output dir
                for f in os.listdir(abs_output_dir):
                    if f.endswith((".mxl", ".musicxml", ".xml")):
                        output_file = os.path.join(abs_output_dir, f)
                        break

            if not output_file:
                return False, None, "No MusicXML output file found"

            # Rename to our standard naming convention
            final_output = get_file_path(output_rel_path)
            if output_file != final_output:
                os.rename(output_file, final_output)

            logger.info(f"OMR processing complete: {output_rel_path}")
            return True, output_rel_path, None

        except subprocess.TimeoutExpired:
            error_msg = "OMR processing timed out (exceeded 5 minutes)"
            logger.error(error_msg)
            return False, None, error_msg
        except FileNotFoundError:
            error_msg = f"Audiveris not found at {self.audiveris_path}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"OMR processing error: {str(e)}"
            logger.exception(error_msg)
            return False, None, error_msg

    def is_available(self) -> bool:
        """Check if Audiveris is available and working."""
        try:
            result = subprocess.run(
                [self.audiveris_path, "-help"], capture_output=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
