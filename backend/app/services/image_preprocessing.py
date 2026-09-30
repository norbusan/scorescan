"""
Image preprocessing service for improving OMR accuracy.

This module provides comprehensive image preprocessing specifically designed
for music score photos, including:
- Deskewing (rotation correction)
- Perspective correction
- Adaptive binarization
- Contrast enhancement
- Noise reduction

These preprocessing steps significantly improve Audiveris recognition accuracy,
especially for mobile photos of printed scores.
"""

import cv2
import numpy as np
import logging
from celery.exceptions import SoftTimeLimitExceeded
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Preprocesses music score images to improve OMR accuracy.

    Optimized for mobile photos of printed scores with common issues:
    - Perspective distortion
    - Uneven lighting
    - Low contrast
    - Shadows
    - Slight blur
    """

    def __init__(
        self,
        target_dpi: int = 300,
        target_interline: int = 20,
        enable_deskew: bool = True,
        enable_perspective_correction: bool = True,
        enable_denoising: bool = True,
        enable_binarization: bool = False,
    ):
        """
        Initialize the preprocessor with configuration options.

        Args:
            target_dpi: Fallback target DPI, used when no staves can be measured
            target_interline: Target distance between staff lines in pixels.
                Audiveris sizes its analysis by the interline; 20 px matches a
                standard staff scanned at 300 DPI.
            enable_deskew: Enable rotation correction
            enable_perspective_correction: Enable perspective/dewarp correction
            enable_denoising: Enable noise reduction
            enable_binarization: Enable adaptive binarization
        """
        self.target_dpi = target_dpi
        self.target_interline = target_interline
        self.enable_deskew = enable_deskew
        self.enable_perspective_correction = enable_perspective_correction
        self.enable_denoising = enable_denoising
        self.enable_binarization = enable_binarization

    def preprocess(
        self, input_path: str, output_path: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Preprocess an image for OMR.

        Args:
            input_path: Path to the input image
            output_path: Path to save the preprocessed image

        Returns:
            Tuple of (success, error_message)
        """
        try:
            logger.info(f"Starting image preprocessing: {input_path}")

            # Load image
            image = cv2.imread(input_path)
            if image is None:
                return False, f"Failed to load image: {input_path}"

            original_shape = image.shape
            logger.info(f"Original image shape: {original_shape}")

            # Step 1: Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Step 2: Perspective correction first: unwarping the page also
            # removes most of its rotation, and deskew pads the canvas with
            # white, which hides the page edges the contour detector needs.
            if self.enable_perspective_correction:
                logger.info("Attempting perspective correction")
                corrected = self._correct_perspective(gray)
                if corrected is not None:
                    gray = corrected
                    logger.info("Perspective correction applied")

            # Step 3: Deskew on sharp edges (before denoising blurs staff lines)
            if self.enable_deskew:
                logger.info("Detecting and correcting skew")
                gray, angle = self._deskew(gray)
                if angle != 0:
                    logger.info(f"Corrected skew angle: {angle:.2f} degrees")

            # Steps 4-5: Denoise and enhance contrast, unless the page is
            # already clean (scanner output, rendered PDF). There they only
            # amplify paper texture.
            if self._is_clean(gray):
                logger.info("Image is clean; skipping denoising and contrast")
            else:
                if self.enable_denoising:
                    logger.info("Applying denoising")
                    gray = self._denoise(gray)
                logger.info("Enhancing contrast")
                gray = self._enhance_contrast(gray)

            # Step 6: Adaptive binarization
            if self.enable_binarization:
                logger.info("Applying adaptive binarization")
                gray = self._binarize(gray)

            # Step 7: Scale so the staff interline suits Audiveris
            logger.info("Normalizing scale")
            gray = self._normalize_scale(gray)

            # Save the preprocessed image
            success = cv2.imwrite(output_path, gray)
            if not success:
                return False, f"Failed to write preprocessed image to {output_path}"

            final_shape = gray.shape
            logger.info(f"Preprocessing complete. Final shape: {final_shape}")
            logger.info(f"Saved to: {output_path}")

            return True, None

        except SoftTimeLimitExceeded:
            raise
        except Exception as e:
            error_msg = f"Image preprocessing error: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg

    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction using Non-local Means Denoising.

        Args:
            image: Grayscale image

        Returns:
            Denoised image
        """
        # Use fastNlMeansDenoising for grayscale images
        # h: filter strength (higher = more denoising but may blur)
        # templateWindowSize: should be odd
        # searchWindowSize: should be odd
        return cv2.fastNlMeansDenoising(
            image, None, h=10, templateWindowSize=7, searchWindowSize=21
        )

    def _deskew(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Detect and correct image skew using the horizontal projection-profile method.

        For each candidate angle, rotate a downsampled binary version of the image
        and compute the variance of the row-wise pixel sum. At the correct angle,
        staff lines align with rows and produce sharp horizontal bands — i.e. the
        projection profile has the highest variance. This is more robust than
        Hough-on-Canny, which mixes in text, barlines, and slurs.
        """
        height, width = image.shape

        # Work on a thumbnail for speed; deskew angle is scale-invariant
        max_dim = 1000
        scale = min(1.0, max_dim / max(height, width))
        if scale < 1.0:
            thumb = cv2.resize(
                image,
                (int(width * scale), int(height * scale)),
                interpolation=cv2.INTER_AREA,
            )
        else:
            thumb = image

        # Binarize so dark ink = 1, paper = 0 (Otsu handles varied lighting)
        _, binary = cv2.threshold(
            thumb, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        def profile_variance(rotated: np.ndarray) -> float:
            projection = rotated.sum(axis=1, dtype=np.int64)
            return float(projection.var())

        # Coarse search: -15 to +15 degrees in 0.5 degree steps (handheld
        # photos are often tilted by more than a few degrees)
        coarse = np.arange(-15.0, 15.01, 0.5)
        best_angle = 0.0
        best_score = profile_variance(binary)
        h, w = binary.shape
        center = (w / 2, h / 2)
        for angle in coarse:
            if angle == 0.0:
                continue
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                binary, M, (w, h), flags=cv2.INTER_NEAREST, borderValue=0
            )
            score = profile_variance(rotated)
            if score > best_score:
                best_score = score
                best_angle = angle

        # Fine search around the coarse winner in 0.1° steps
        fine = np.arange(best_angle - 0.5, best_angle + 0.51, 0.1)
        for angle in fine:
            M = cv2.getRotationMatrix2D(center, float(angle), 1.0)
            rotated = cv2.warpAffine(
                binary, M, (w, h), flags=cv2.INTER_NEAREST, borderValue=0
            )
            score = profile_variance(rotated)
            if score > best_score:
                best_score = score
                best_angle = float(angle)

        # Only correct if the angle is significant
        if abs(best_angle) < 0.3:
            return image, 0.0

        # Rotate the full-resolution image
        height, width = image.shape
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, best_angle, 1.0)

        # Calculate new image size to avoid cropping
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))

        # Adjust rotation matrix for new size
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]

        # Apply rotation with white background
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (new_width, new_height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )

        return rotated, best_angle

    def _correct_perspective(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Attempt to correct perspective distortion.

        Tries to detect the document boundary and unwarp it to a rectangle.

        Args:
            image: Grayscale image

        Returns:
            Perspective-corrected image, or None if correction failed
        """
        # Apply edge detection
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        # Sort contours by area and take the largest
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        document_contour = None
        for contour in contours:
            # Approximate the contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            # If the contour has 4 points, assume it's the document
            if len(approx) == 4:
                document_contour = approx
                break

        if document_contour is None:
            logger.info("Could not detect document boundary for perspective correction")
            return None

        # Gate: the candidate quad must cover most of the image. Without this,
        # the detector frequently latches onto a staff bounding box or a single
        # system and destructively warps the score.
        image_area = float(image.shape[0] * image.shape[1])
        contour_area = float(cv2.contourArea(document_contour))
        coverage = contour_area / image_area if image_area > 0 else 0.0
        if coverage < 0.5:
            logger.info(
                f"Perspective correction skipped: candidate quad covers "
                f"only {coverage:.1%} of the image (need >=50%)"
            )
            return None

        # Reshape the contour to 4 points
        points = document_contour.reshape(4, 2)

        # Order points: top-left, top-right, bottom-right, bottom-left
        rect = self._order_points(points)

        # Reject extreme aspect ratios (likely latched onto a staff, not a page)
        w_top = np.linalg.norm(rect[1] - rect[0])
        w_bot = np.linalg.norm(rect[2] - rect[3])
        h_left = np.linalg.norm(rect[3] - rect[0])
        h_right = np.linalg.norm(rect[2] - rect[1])
        avg_w = (w_top + w_bot) / 2
        avg_h = (h_left + h_right) / 2
        if avg_h <= 0 or avg_w <= 0:
            return None
        aspect = max(avg_w / avg_h, avg_h / avg_w)
        if aspect > 3.0:
            logger.info(
                f"Perspective correction skipped: aspect ratio {aspect:.2f} "
                f"is implausible for a score page"
            )
            return None

        # Calculate the width and height of the new image
        (tl, tr, br, bl) = rect

        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_width = max(int(width_a), int(width_b))

        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_height = max(int(height_a), int(height_b))

        # Construct destination points
        dst = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1],
            ],
            dtype="float32",
        )

        # Calculate perspective transform matrix
        matrix = cv2.getPerspectiveTransform(rect, dst)

        # Apply perspective transformation
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height))

        return warped

    def _order_points(self, points: np.ndarray) -> np.ndarray:
        """
        Order points in clockwise order: top-left, top-right, bottom-right, bottom-left.

        Args:
            points: Array of 4 points

        Returns:
            Ordered array of points
        """
        rect = np.zeros((4, 2), dtype="float32")

        # Sum and diff to find corners
        s = points.sum(axis=1)
        rect[0] = points[np.argmin(s)]  # Top-left has smallest sum
        rect[2] = points[np.argmax(s)]  # Bottom-right has largest sum

        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]  # Top-right has smallest diff
        rect[3] = points[np.argmax(diff)]  # Bottom-left has largest diff

        return rect

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).

        CLAHE is better than regular histogram equalization for images with
        varying lighting conditions.

        Args:
            image: Grayscale image

        Returns:
            Contrast-enhanced image
        """
        # Create CLAHE object
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        # Apply CLAHE
        enhanced = clahe.apply(image)

        return enhanced

    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert to binary (black and white) using adaptive thresholding.

        Adaptive thresholding is better than global thresholding for images
        with uneven lighting or shadows.

        Args:
            image: Grayscale image

        Returns:
            Binary image
        """
        # Apply adaptive thresholding
        # ADAPTIVE_THRESH_GAUSSIAN_C: threshold value is weighted sum of neighborhood
        # THRESH_BINARY: output is either 0 or 255
        # Block size: size of neighborhood area (must be odd)
        # C: constant subtracted from weighted mean
        binary = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=10,
        )

        return binary

    @staticmethod
    def _is_clean(image: np.ndarray) -> bool:
        """True if the page is already close to black ink on uniform paper."""
        midtones = np.count_nonzero((image > 64) & (image < 192)) / image.size
        paper = image[image >= 192]
        paper_noise = float(paper.std()) if paper.size else 255.0
        return midtones < 0.03 and paper_noise < 8.0

    @staticmethod
    def estimate_interline(image: np.ndarray) -> Optional[float]:
        """Estimate the staff interline (line-to-line distance) in pixels.

        Samples columns of the ink mask and histograms the distance between the
        starts of consecutive vertical ink runs. Staff lines cross nearly every
        column, so their spacing dominates the histogram. Returns None when no
        clear peak exists (no staves found).
        """
        _, ink = cv2.threshold(
            image, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        h, w = ink.shape
        n_cols = min(w, 200)
        cols = ink[:, np.linspace(0, w - 1, n_cols).astype(int)].astype(np.int8)
        padded = np.pad(cols, ((1, 0), (0, 0)))
        max_spacing = min(200, h // 4)
        hist = np.zeros(max_spacing + 1, dtype=np.int64)
        for c in range(n_cols):
            starts = np.flatnonzero(np.diff(padded[:, c]) == 1)
            spacing = np.diff(starts)
            spacing = spacing[(spacing >= 4) & (spacing <= max_spacing)]
            hist += np.bincount(spacing, minlength=max_spacing + 1)
        # Merge neighbouring bins so a spacing jittering between n and n+1
        # still forms one peak
        smoothed = np.convolve(hist, np.ones(3, dtype=np.int64), mode="same")
        peak = int(smoothed.argmax())
        # A staff gives 4 spacings per column; require about one staff's worth
        if smoothed[peak] < 4 * n_cols:
            return None
        window = hist[max(peak - 1, 0) : peak + 2]
        bins = np.arange(max(peak - 1, 0), max(peak - 1, 0) + len(window))
        return float((window * bins).sum() / window.sum())

    def _normalize_scale(self, image: np.ndarray) -> np.ndarray:
        """Rescale so the staff interline is close to target_interline.

        Falls back to a DPI estimate (short side = 8.5 inches, upscale only)
        when no staves can be measured.
        """
        height, width = image.shape
        interline = self.estimate_interline(image)

        if interline is not None:
            logger.info(f"Estimated staff interline: {interline:.1f} px")
            t = self.target_interline
            if 0.8 * t <= interline <= 2 * t:
                return image
            scale = t / interline
        else:
            current_dpi = min(height, width) / 8.5
            logger.info(f"No staves measured; estimated ~{current_dpi:.0f} DPI")
            if current_dpi >= self.target_dpi:
                return image
            scale = self.target_dpi / current_dpi

        # ponytail: fixed clamps; make configurable if real inputs hit them
        scale = min(max(scale, 0.25), 4.0)
        scale = min(scale, 12000 / max(height, width))
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
        logger.info(f"Rescaling by {scale:.2f} to {new_size[0]}x{new_size[1]}")
        return cv2.resize(image, new_size, interpolation=interp)


def preprocess_for_omr(
    input_path: str, output_path: str, target_dpi: int = 300, enable_all: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to preprocess an image with default settings.

    Note: binarization is intentionally left off by default. Audiveris applies its
    own music-aware binarization (Sauvola) and feeding it a pre-binarized image
    typically hurts recognition. Pass a preprocessor with enable_binarization=True
    only for already-clean printed scans.
    """
    preprocessor = ImagePreprocessor(
        target_dpi=target_dpi,
        enable_deskew=enable_all,
        enable_perspective_correction=enable_all,
        enable_denoising=enable_all,
        enable_binarization=False,
    )

    return preprocessor.preprocess(input_path, output_path)
