"""Deep-learning OMR fallback using oemer.

Oemer is a standalone pip-installable tool that handles handwritten and
low-quality scans better than Audiveris. It is ~500MB (TensorFlow + model
weights) so it is not installed in the default backend/worker image; enable it
by installing the `oemer` extra group (`uv sync --group oemer`) and setting
`OEMER_ENABLED=true`.

This service is meant as a *fallback*, invoked when Audiveris produces no
usable output. For that reason the API mirrors ``OMRService.process_image``.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

from app.config import get_settings
from app.services.image_preprocessing import preprocess_for_omr
from app.utils.storage import get_file_path

settings = get_settings()
logger = logging.getLogger(__name__)


class OemerService:
    """OMR using the oemer deep-learning engine."""

    def __init__(self, enable_preprocessing: bool = True):
        self.oemer_path = settings.oemer_path
        self.enable_preprocessing = enable_preprocessing

    def is_available(self) -> bool:
        """Return True if the oemer CLI is callable.

        Oemer is a TensorFlow app and imports can be slow, so we prefer a
        ``shutil.which`` check over actually invoking ``--help``.
        """
        if not settings.oemer_enabled:
            return False
        return shutil.which(self.oemer_path) is not None

    def _render_first_pdf_page(self, pdf_path: str, out_dir: str) -> Optional[str]:
        """Render the first page of a PDF to PNG. Oemer is single-page only."""
        try:
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(pdf_path)
            try:
                if len(pdf) == 0:
                    return None
                bitmap = pdf[0].render(scale=300 / 72.0, rotation=0)
                out = os.path.join(out_dir, "page.png")
                bitmap.to_pil().save(out, "PNG")
                return out
            finally:
                pdf.close()
        except Exception as e:
            logger.exception(f"Failed to render PDF first page: {e}")
            return None

    def _prepare_input(self, abs_input_path: str, work_dir: str) -> Optional[str]:
        """Return a PNG path ready to feed to oemer, or None on failure."""
        is_pdf = abs_input_path.lower().endswith(".pdf")

        if is_pdf:
            page = self._render_first_pdf_page(abs_input_path, work_dir)
            if not page:
                return None
            source = page
        else:
            source = abs_input_path

        if not self.enable_preprocessing:
            return source

        preprocessed = os.path.join(work_dir, "input_pp.png")
        success, err = preprocess_for_omr(source, preprocessed)
        if not success:
            logger.warning(f"Preprocess failed for oemer: {err}; using raw input")
            return source
        return preprocessed

    def process_image(
        self, input_path: str, user_id: str, job_id: str
    ) -> Tuple[bool, Optional[str], Optional[str], List[str]]:
        """Run oemer on the input and return the same tuple shape as OMRService."""
        if not self.is_available():
            return (
                False,
                None,
                "Oemer is not enabled or not installed on this server",
                [],
            )

        abs_input_path = get_file_path(input_path)
        output_dir_rel = os.path.join("musicxml", user_id)
        abs_output_dir = get_file_path(output_dir_rel)
        os.makedirs(abs_output_dir, exist_ok=True)

        warnings: List[str] = []
        work_dir = tempfile.mkdtemp(
            prefix=f"scorescan_oemer_{job_id}_", dir=abs_output_dir
        )
        try:
            prepared = self._prepare_input(abs_input_path, work_dir)
            if not prepared:
                return False, None, "Could not prepare input for oemer", []

            # Note first-page-only behavior so the user isn't surprised
            if abs_input_path.lower().endswith(".pdf"):
                warnings.append(
                    "Oemer processed only the first page of a multi-page PDF."
                )

            cmd = [self.oemer_path, "-o", work_dir, prepared]
            logger.info(f"Running oemer: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,  # TF startup can be slow; allow 10 minutes
                )
            except subprocess.TimeoutExpired:
                return False, None, "Oemer timed out (exceeded 10 minutes)", warnings
            except FileNotFoundError:
                return False, None, f"Oemer not found at {self.oemer_path}", warnings

            if result.stdout:
                logger.info(f"Oemer stdout: {result.stdout[-2000:]}")
            if result.stderr:
                logger.info(f"Oemer stderr: {result.stderr[-2000:]}")

            # Oemer writes <stem>.musicxml next to the input (or in -o dir).
            produced = self._find_output(work_dir)
            if not produced:
                err = f"Oemer produced no MusicXML (returncode={result.returncode})"
                if result.stderr:
                    err += f"; stderr tail: {result.stderr[-300:]}"
                return False, None, err, warnings

            from app.services.omr import get_musicxml_path_with_ext

            final_rel = get_musicxml_path_with_ext(user_id, job_id, ".musicxml")
            final_abs = get_file_path(final_rel)
            shutil.move(produced, final_abs)
            logger.info(f"Oemer OMR complete: {final_rel}")
            return True, final_rel, None, warnings
        except Exception as e:
            logger.exception(f"Oemer processing error: {e}")
            return False, None, f"Oemer processing error: {e}", warnings
        finally:
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    @staticmethod
    def _find_output(directory: str) -> Optional[str]:
        """Locate the .musicxml file oemer emitted into ``directory``."""
        for name in os.listdir(directory):
            if name.endswith(".musicxml"):
                return os.path.join(directory, name)
        return None
