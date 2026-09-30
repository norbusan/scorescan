import subprocess
import os
import logging
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from app.config import get_settings
from app.utils.storage import get_file_path
from app.services.image_preprocessing import preprocess_for_omr

settings = get_settings()
logger = logging.getLogger(__name__)


# Audiveris warning/error patterns we surface to the user. Audiveris logs look
# like "12:34:56 WARN  [sheet#1] No staff found in system X" — we match on the
# severity token and the bracketed context when present.
_AUDIVERIS_WARN_RE = re.compile(r"\b(WARN|ERROR|SEVERE)\b(.*)", re.IGNORECASE)
_MUSICXML_NS = {
    "": "",  # default empty namespace
}
# Audiveris names split movements <stem>.mvt<N>.mxl
_MOVEMENT_RE = re.compile(r"\.mvt(\d+)\.")


def get_musicxml_path_with_ext(user_id: str, job_id: str, ext: str) -> str:
    """Generate the MusicXML output path for a job with specific extension."""
    user_dir = os.path.join(settings.musicxml_path, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join("musicxml", user_id, f"{job_id}{ext}")


class OMRService:
    """
    Optical Music Recognition service using Audiveris 5.10.
    Converts music score images to MusicXML format.
    """

    def __init__(
        self,
        enable_preprocessing: bool = True,
        enable_ocr: bool = False,
        interline_range: Optional[Tuple[int, int]] = None,
        audiveris_options: Optional[Dict[str, str]] = None,
        audiveris_steps: Optional[List[str]] = None,
    ):
        """Create an OMR service.

        Args:
            enable_preprocessing: Run our preprocessing pipeline first.
            enable_ocr: Enable Audiveris's Tesseract OCR for lyrics/text.
            interline_range: Override Audiveris's staff-size search, as
                (min, max) interline distance in pixels. Useful for unusually
                small or large staves.
            audiveris_options: Extra `-option key=value` pairs passed raw.
                These win over any of the convenience kwargs above.
            audiveris_steps: Pipeline steps to run (e.g. ["PAGE"]). Defaults
                to the full pipeline.
        """
        self.audiveris_path = settings.audiveris_path
        self.enable_preprocessing = enable_preprocessing
        self.enable_ocr = enable_ocr
        self.interline_range = interline_range
        self.audiveris_options = dict(audiveris_options or {})
        self.audiveris_steps = list(audiveris_steps or [])

    def _build_audiveris_options(self) -> Dict[str, str]:
        """Merge convenience kwargs into the final Audiveris -option map."""
        options: Dict[str, str] = {}
        if self.enable_ocr:
            options["org.audiveris.omr.text.OCR.useOCR"] = "true"
        if self.interline_range is not None:
            lo, hi = self.interline_range
            options["org.audiveris.omr.sheet.Scale.minInterline"] = str(lo)
            options["org.audiveris.omr.sheet.Scale.maxInterline"] = str(hi)
        # User-provided options override the convenience ones
        options.update(self.audiveris_options)
        return options

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

    def _render_pdf_pages(self, pdf_path: str, out_dir: str, dpi: int = 300) -> List[str]:
        """Render each PDF page to a PNG at the given DPI. Returns list of PNG paths."""
        import pypdfium2 as pdfium

        scale = dpi / 72.0
        pdf = pdfium.PdfDocument(pdf_path)
        try:
            paths: List[str] = []
            for i, page in enumerate(pdf):
                bitmap = page.render(scale=scale, rotation=0)
                pil = bitmap.to_pil()
                page_path = os.path.join(out_dir, f"page_{i + 1:03d}.png")
                pil.save(page_path, "PNG")
                paths.append(page_path)
            return paths
        finally:
            pdf.close()

    def _combine_pages_to_pdf(self, image_paths: List[str], out_pdf: str) -> None:
        """Combine preprocessed page images back into a single multi-page PDF for Audiveris."""
        images = [Image.open(p) for p in image_paths]
        try:
            rgb_images = [im.convert("RGB") for im in images]
            rgb_images[0].save(
                out_pdf,
                "PDF",
                resolution=300.0,
                save_all=True,
                append_images=rgb_images[1:],
            )
        finally:
            for im in images:
                im.close()

    def _preprocess_pdf(self, pdf_path: str, work_dir: str) -> Optional[str]:
        """Render PDF pages, preprocess each, and reassemble into a multi-page PDF.

        Returns the path to the preprocessed PDF, or None on failure (caller should
        fall back to the original PDF).
        """
        try:
            pages_dir = os.path.join(work_dir, "pages")
            os.makedirs(pages_dir, exist_ok=True)

            page_paths = self._render_pdf_pages(pdf_path, pages_dir, dpi=300)
            if not page_paths:
                logger.warning(f"PDF {pdf_path} produced no pages")
                return None

            logger.info(f"Rendered {len(page_paths)} PDF page(s) for preprocessing")

            processed_paths: List[str] = []
            for p in page_paths:
                processed = p.replace(".png", "_pp.png")
                success, err = preprocess_for_omr(p, processed)
                if success:
                    processed_paths.append(processed)
                else:
                    logger.warning(f"Preprocess failed for {p}: {err}; using raw page")
                    processed_paths.append(p)

            out_pdf = os.path.join(work_dir, "preprocessed.pdf")
            self._combine_pages_to_pdf(processed_paths, out_pdf)
            return out_pdf
        except Exception as e:
            logger.exception(f"PDF preprocessing failed: {e}")
            return None

    def _prepare_input(self, abs_input_path: str, work_dir: str) -> str:
        """Preprocess the input into work_dir. Returns the path to feed Audiveris."""
        if not self.enable_preprocessing:
            return abs_input_path

        input_path_obj = Path(abs_input_path)
        if input_path_obj.suffix.lower() == ".pdf":
            logger.info("Preprocessing PDF by rendering pages at 300 DPI")
            pp_pdf = self._preprocess_pdf(abs_input_path, work_dir)
            if pp_pdf:
                logger.info(f"PDF preprocessing successful: {pp_pdf}")
                return pp_pdf
            logger.warning("PDF preprocessing failed; using original PDF")
            return abs_input_path

        logger.info("Preprocessing image for improved OMR accuracy")
        preprocessed_path = os.path.join(
            work_dir, f"{input_path_obj.stem}_preprocessed{input_path_obj.suffix}"
        )
        success, error = preprocess_for_omr(abs_input_path, preprocessed_path)
        if success:
            logger.info(f"Image preprocessing successful: {preprocessed_path}")
            return preprocessed_path
        logger.warning(f"Image preprocessing failed: {error}; using original image")
        return abs_input_path

    @staticmethod
    def _collect_outputs(work_dir: str) -> List[str]:
        """Return the MusicXML exports in work_dir, ordered by movement.

        Audiveris writes <stem>.mxl for a single-movement score and
        <stem>.mvt1.mxl, <stem>.mvt2.mxl, ... when it splits the score.
        """
        found: List[str] = []
        for root, _, files in os.walk(work_dir):
            for f in files:
                if f.endswith((".mxl", ".musicxml")) or (
                    f.endswith(".xml") and not f.startswith("container")
                ):
                    found.append(os.path.join(root, f))

        def movement_index(path: str) -> int:
            m = _MOVEMENT_RE.search(os.path.basename(path))
            return int(m.group(1)) if m else 0

        return sorted(found, key=movement_index)

    @staticmethod
    def _merge_movements(paths: List[str], out_path: str) -> List[str]:
        """Concatenate movement files into one score. Returns warnings."""
        from music21 import converter, stream

        warnings: List[str] = []
        base = converter.parse(paths[0])
        for n, path in enumerate(paths[1:], start=2):
            movement = converter.parse(path)
            if len(movement.parts) != len(base.parts):
                warnings.append(
                    f"Movement {n} has a different number of parts than the "
                    "first movement and was dropped."
                )
                continue
            for base_part, mv_part in zip(base.parts, movement.parts):
                existing = list(base_part.getElementsByClass(stream.Measure))
                next_number = (existing[-1].number if existing else 0) + 1
                offset = base_part.highestTime
                measures = [
                    (m.getOffsetBySite(mv_part), m)
                    for m in mv_part.getElementsByClass(stream.Measure)
                ]
                for i, (m_offset, m) in enumerate(measures):
                    m.number = next_number + i
                    base_part.insert(offset + m_offset, m)
        base.write("musicxml", fp=out_path)
        return warnings

    def process_image(
        self, input_path: str, user_id: str, job_id: str
    ) -> Tuple[bool, Optional[str], Optional[str], List[str]]:
        """
        Process an image file with Audiveris to generate MusicXML.

        Returns:
            Tuple of (success, output_path, error_message, quality_warnings).
            quality_warnings is a possibly-empty list of human-readable strings
            derived from Audiveris output and the resulting MusicXML.
        """
        work_dir: Optional[str] = None
        try:
            abs_input_path = get_file_path(input_path)
            abs_output_dir = get_file_path(os.path.join("musicxml", user_id))
            os.makedirs(abs_output_dir, exist_ok=True)

            # Per-job scratch dir: Audiveris writes its exports, .omr project and
            # log here, so outputs of other jobs of the same user are never
            # picked up, and everything is removed when the job is done.
            work_dir = tempfile.mkdtemp(
                prefix=f"scorescan_{job_id}_", dir=abs_output_dir
            )

            logger.info(f"Starting OMR processing for {abs_input_path}")
            processed_input_path = self._prepare_input(abs_input_path, work_dir)

            # Run Audiveris in batch mode with xvfb-run for headless operation
            # Audiveris 5.10 CLI: -batch -export -output <dir> [-option ...] [-step ...] <input>
            cmd: List[str] = [
                "xvfb-run",
                "-a",  # Auto-select display number
                self.audiveris_path,
                "-batch",
                "-export",
                "-output",
                work_dir,
            ]
            for key, value in self._build_audiveris_options().items():
                cmd.extend(["-option", f"{key}={value}"])
            for step in self.audiveris_steps:
                cmd.extend(["-step", step])
            cmd.append(processed_input_path)

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

            # Collect quality signals from Audiveris logs; useful even on
            # success because Audiveris often returns partial results with
            # warnings that affect usability of the output.
            warnings = self._collect_audiveris_warnings(
                result.stdout, result.stderr
            )

            # Audiveris may return non-zero even on partial success, so look
            # at what it exported rather than at the return code.
            outputs = self._collect_outputs(work_dir)
            if not outputs:
                error_msg = f"No MusicXML output file found. Audiveris return code: {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr[:500]}"
                return False, None, error_msg, warnings

            logger.info(f"Found output file(s): {outputs}")

            final_rel_path = get_musicxml_path_with_ext(user_id, job_id, ".musicxml")
            final_abs_path = get_file_path(final_rel_path)

            if len(outputs) > 1:
                warnings.append(
                    f"Audiveris split the score into {len(outputs)} movements; "
                    "they were joined into a single score."
                )
                warnings.extend(self._merge_movements(outputs, final_abs_path))
            elif outputs[0].endswith(".mxl"):
                # Extract compressed MusicXML so music21 can parse it reliably
                logger.info(f"Extracting compressed MXL to {final_abs_path}")
                if not self._extract_mxl_to_musicxml(outputs[0], final_abs_path):
                    # Keep the .mxl as-is; MuseScore and music21 can read it
                    final_rel_path = get_musicxml_path_with_ext(user_id, job_id, ".mxl")
                    final_abs_path = get_file_path(final_rel_path)
                    shutil.move(outputs[0], final_abs_path)
            else:
                shutil.move(outputs[0], final_abs_path)

            logger.info(f"OMR processing complete: {final_rel_path}")

            # Score-level quality checks on the MusicXML
            warnings.extend(self._inspect_musicxml_quality(final_abs_path))
            if warnings:
                logger.warning(
                    f"OMR produced {len(warnings)} quality warning(s) for job {job_id}"
                )

            return True, final_rel_path, None, warnings

        except subprocess.TimeoutExpired:
            error_msg = "OMR processing timed out (exceeded 5 minutes)"
            logger.error(error_msg)
            return False, None, error_msg, []
        except FileNotFoundError as e:
            error_msg = f"Audiveris not found at {self.audiveris_path}: {e}"
            logger.error(error_msg)
            return False, None, error_msg, []
        except Exception as e:
            error_msg = f"OMR processing error: {str(e)}"
            logger.exception(error_msg)
            return False, None, error_msg, []
        finally:
            if work_dir:
                shutil.rmtree(work_dir, ignore_errors=True)

    def _collect_audiveris_warnings(self, stdout: str, stderr: str) -> List[str]:
        """Extract a capped list of WARN/ERROR lines from Audiveris output."""
        warnings: List[str] = []
        seen: set[str] = set()
        max_warnings = 20

        # Phrases that are noisy but harmless — don't surface to end users
        ignore_substrings = (
            "JavaFX",  # Headless startup noise
            "display :0",
            "Could not load library",  # Often benign
        )

        for stream in (stdout or "", stderr or ""):
            for raw_line in stream.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                if any(snippet in line for snippet in ignore_substrings):
                    continue
                if not _AUDIVERIS_WARN_RE.search(line):
                    continue
                # Deduplicate — Audiveris often repeats the same issue per page
                key = line[:200]
                if key in seen:
                    continue
                seen.add(key)
                warnings.append(line[:300])
                if len(warnings) >= max_warnings:
                    warnings.append(
                        f"(truncated; {max_warnings}+ Audiveris warnings emitted)"
                    )
                    return warnings
        return warnings

    def _inspect_musicxml_quality(self, musicxml_path: str) -> List[str]:
        """Derive score-level quality signals from the final MusicXML.

        These are the cheap checks that catch the common failure modes: empty
        output, a single-measure fragment, or no notes recognized at all.
        """
        notes: List[str] = []
        try:
            tree = ET.parse(musicxml_path)
        except (ET.ParseError, OSError) as e:
            notes.append(f"MusicXML could not be parsed: {e}")
            return notes

        root = tree.getroot()
        # MusicXML uses no namespace by default; handle either shape.
        def local(tag: str) -> str:
            return tag.split("}", 1)[1] if "}" in tag else tag

        measures = [el for el in root.iter() if local(el.tag) == "measure"]
        note_elems = [el for el in root.iter() if local(el.tag) == "note"]
        parts = [el for el in root.iter() if local(el.tag) == "part"]

        if not parts:
            notes.append("No parts/instruments detected in the score.")
        if not measures:
            notes.append("No measures detected — OMR likely failed.")
        elif len(measures) < 2:
            notes.append(
                f"Only {len(measures)} measure detected — the scan may be "
                "incomplete or unreadable."
            )
        if not note_elems:
            notes.append(
                "No notes detected — try a higher-resolution scan or better lighting."
            )

        return notes

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
