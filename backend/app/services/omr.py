import subprocess
import os
import logging
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Tuple

from app.config import get_settings
from app.utils.storage import get_file_path
from app.services.image_preprocessing import preprocess_for_omr

settings = get_settings()
logger = logging.getLogger(__name__)


def get_musicxml_path_with_ext(user_id: str, job_id: str, ext: str) -> str:
    """Generate the MusicXML output path for a job with specific extension."""
    user_dir = os.path.join(settings.musicxml_path, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join("musicxml", user_id, f"{job_id}{ext}")


class OMRService:
    """
    Optical Music Recognition service using Audiveris 5.9.
    Converts music score images to MusicXML format.
    """

    def __init__(self, enable_preprocessing: bool = True):
        self.audiveris_path = settings.audiveris_path
        self.enable_preprocessing = enable_preprocessing

    def _extract_mxl_to_musicxml(self, mxl_path: str, output_path: str) -> bool:
        """
        Extract a .mxl file (compressed MusicXML) to uncompressed .musicxml.

        Args:
            mxl_path: Path to the .mxl file
            output_path: Path for the output .musicxml file

        Returns:
            True if successful, False otherwise
        """
        try:
            with zipfile.ZipFile(mxl_path, "r") as zf:
                # Look for the main musicxml file inside the archive
                # Usually named something like 'score.xml' or in a subdirectory
                xml_files = [
                    f
                    for f in zf.namelist()
                    if f.endswith(".xml") and not f.startswith("META-INF")
                ]

                if not xml_files:
                    logger.error(f"No XML file found in {mxl_path}")
                    return False

                # Prefer files that look like the main score
                main_xml = None
                for f in xml_files:
                    if "container" not in f.lower():
                        main_xml = f
                        break

                if not main_xml:
                    main_xml = xml_files[0]

                logger.info(f"Extracting {main_xml} from {mxl_path}")

                # Extract the XML content
                with zf.open(main_xml) as xml_file:
                    with open(output_path, "wb") as out_file:
                        out_file.write(xml_file.read())

                return True

        except zipfile.BadZipFile:
            logger.error(f"{mxl_path} is not a valid ZIP/MXL file")
            return False
        except Exception as e:
            logger.exception(f"Error extracting MXL file: {e}")
            return False

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

            # Create output directory
            output_dir_rel = os.path.join("musicxml", user_id)
            abs_output_dir = get_file_path(output_dir_rel)
            os.makedirs(abs_output_dir, exist_ok=True)

            logger.info(f"Starting OMR processing for {abs_input_path}")

            # Preprocess the image if enabled
            processed_input_path = abs_input_path
            if self.enable_preprocessing:
                logger.info("Preprocessing image for improved OMR accuracy")

                # Create a temporary file for the preprocessed image
                input_path_obj = Path(abs_input_path)
                preprocessed_filename = (
                    f"{input_path_obj.stem}_preprocessed{input_path_obj.suffix}"
                )
                preprocessed_path = os.path.join(abs_output_dir, preprocessed_filename)

                success, error = preprocess_for_omr(abs_input_path, preprocessed_path)

                if success:
                    logger.info(f"Image preprocessing successful: {preprocessed_path}")
                    processed_input_path = preprocessed_path
                else:
                    logger.warning(f"Image preprocessing failed: {error}")
                    logger.warning("Falling back to original image")
                    # Continue with original image if preprocessing fails

            # Run Audiveris in batch mode with xvfb-run for headless operation
            # Audiveris 5.9 CLI: -batch -export -output <dir> <input_file>
            # Use the preprocessed image if available
            cmd = [
                "xvfb-run",
                "-a",  # Auto-select display number
                self.audiveris_path,
                "-batch",
                "-export",
                "-output",
                abs_output_dir,
                processed_input_path,
            ]

            logger.info(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env={**os.environ, "DISPLAY": ""},
            )

            logger.info(f"Audiveris stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Audiveris stderr: {result.stderr}")

            # Audiveris may return non-zero even on partial success, check for output files
            # Find the output file (Audiveris names it based on input filename)
            # Use the processed input path stem (which may be the preprocessed file)
            input_stem = Path(processed_input_path).stem
            possible_outputs = [
                (os.path.join(abs_output_dir, f"{input_stem}.mxl"), ".mxl"),
                (os.path.join(abs_output_dir, f"{input_stem}.musicxml"), ".musicxml"),
                (os.path.join(abs_output_dir, f"{input_stem}.xml"), ".xml"),
            ]

            output_file = None
            output_ext = None
            for path, ext in possible_outputs:
                if os.path.exists(path):
                    output_file = path
                    output_ext = ext
                    break

            if not output_file:
                # Check for any musicxml-like file in the output dir
                for f in os.listdir(abs_output_dir):
                    if f.endswith(".mxl"):
                        output_file = os.path.join(abs_output_dir, f)
                        output_ext = ".mxl"
                        break
                    elif f.endswith(".musicxml"):
                        output_file = os.path.join(abs_output_dir, f)
                        output_ext = ".musicxml"
                        break
                    elif f.endswith(".xml") and not f.startswith("container"):
                        output_file = os.path.join(abs_output_dir, f)
                        output_ext = ".xml"
                        break

            if not output_file:
                error_msg = f"No MusicXML output file found. Audiveris return code: {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr[:500]}"
                return False, None, error_msg

            logger.info(f"Found output file: {output_file} with extension {output_ext}")

            # If it's a .mxl (compressed MusicXML), extract it to .musicxml
            # This ensures music21 can parse it correctly
            final_rel_path = get_musicxml_path_with_ext(user_id, job_id, ".musicxml")
            final_abs_path = get_file_path(final_rel_path)

            if output_ext == ".mxl":
                logger.info(f"Extracting compressed MXL to {final_abs_path}")
                if not self._extract_mxl_to_musicxml(output_file, final_abs_path):
                    # If extraction fails, try to use the file directly
                    # (maybe music21 can handle it)
                    final_rel_path = get_musicxml_path_with_ext(user_id, job_id, ".mxl")
                    final_abs_path = get_file_path(final_rel_path)
                    shutil.move(output_file, final_abs_path)
                else:
                    # Remove the original .mxl file after successful extraction
                    os.remove(output_file)
            else:
                # Just move/rename the file
                if output_file != final_abs_path:
                    shutil.move(output_file, final_abs_path)

            logger.info(f"OMR processing complete: {final_rel_path}")

            # Clean up preprocessed file if it was created
            if processed_input_path != abs_input_path and os.path.exists(
                processed_input_path
            ):
                try:
                    os.remove(processed_input_path)
                    logger.info(f"Cleaned up preprocessed file: {processed_input_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up preprocessed file: {e}")

            return True, final_rel_path, None

        except subprocess.TimeoutExpired:
            error_msg = "OMR processing timed out (exceeded 5 minutes)"
            logger.error(error_msg)
            return False, None, error_msg
        except FileNotFoundError as e:
            error_msg = f"Audiveris not found at {self.audiveris_path}: {e}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"OMR processing error: {str(e)}"
            logger.exception(error_msg)
            return False, None, error_msg

    def is_available(self) -> bool:
        """Check if Audiveris is available and working."""
        try:
            # Check if the binary exists
            if not os.path.exists(self.audiveris_path):
                logger.warning(f"Audiveris binary not found at {self.audiveris_path}")
                return False

            result = subprocess.run(
                ["xvfb-run", "-a", self.audiveris_path, "-help"],
                capture_output=True,
                timeout=30,
            )
            # Audiveris may return non-zero for -help but still be working
            return True
        except Exception as e:
            logger.warning(f"Audiveris availability check failed: {e}")
            return False
