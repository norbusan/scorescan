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
        enable_deskew: bool = True,
        enable_perspective_correction: bool = True,
        enable_denoising: bool = True,
        enable_binarization: bool = True,
    ):
        """
        Initialize the preprocessor with configuration options.

        Args:
            target_dpi: Target DPI for output (higher = better quality, slower)
            enable_deskew: Enable rotation correction
            enable_perspective_correction: Enable perspective/dewarp correction
            enable_denoising: Enable noise reduction
            enable_binarization: Enable adaptive binarization
        """
        self.target_dpi = target_dpi
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

            # Step 2: Denoise (optional)
            if self.enable_denoising:
                logger.info("Applying denoising")
                gray = self._denoise(gray)

            # Step 3: Deskew (rotation correction)
            if self.enable_deskew:
                logger.info("Detecting and correcting skew")
                gray, angle = self._deskew(gray)
                if angle != 0:
                    logger.info(f"Corrected skew angle: {angle:.2f} degrees")

            # Step 4: Perspective correction (if enabled)
            if self.enable_perspective_correction:
                logger.info("Attempting perspective correction")
                corrected = self._correct_perspective(gray)
                if corrected is not None:
                    gray = corrected
                    logger.info("Perspective correction applied")

            # Step 5: Contrast enhancement
            logger.info("Enhancing contrast")
            gray = self._enhance_contrast(gray)

            # Step 6: Adaptive binarization
            if self.enable_binarization:
                logger.info("Applying adaptive binarization")
                gray = self._binarize(gray)

            # Step 7: Ensure minimum resolution
            logger.info("Checking resolution")
            gray = self._ensure_resolution(gray)

            # Save the preprocessed image
            success = cv2.imwrite(output_path, gray)
            if not success:
                return False, f"Failed to write preprocessed image to {output_path}"

            final_shape = gray.shape
            logger.info(f"Preprocessing complete. Final shape: {final_shape}")
            logger.info(f"Saved to: {output_path}")

            return True, None

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
        Detect and correct image skew (rotation).

        Uses Hough Line Transform to detect dominant line angles,
        which correspond to staff lines in music scores.

        Args:
            image: Grayscale image

        Returns:
            Tuple of (deskewed image, rotation angle in degrees)
        """
        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Detect lines using Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)

        if lines is None or len(lines) == 0:
            logger.info("No lines detected for deskewing")
            return image, 0.0

        # Calculate angles of detected lines
        angles = []
        for line in lines:
            rho, theta = line[0]
            # Convert to degrees and normalize to [-90, 90]
            angle = np.degrees(theta) - 90
            # Filter out near-vertical lines (staff lines are horizontal)
            if -45 < angle < 45:
                angles.append(angle)

        if not angles:
            logger.info("No horizontal lines detected")
            return image, 0.0

        # Use median angle to avoid outliers
        median_angle = np.median(angles)

        # Only correct if angle is significant (> 0.5 degrees)
        if abs(median_angle) < 0.5:
            return image, 0.0

        # Rotate image to correct skew
        height, width = image.shape
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)

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

        return rotated, median_angle

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

        # Reshape the contour to 4 points
        points = document_contour.reshape(4, 2)

        # Order points: top-left, top-right, bottom-right, bottom-left
        rect = self._order_points(points)

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

    def _ensure_resolution(self, image: np.ndarray) -> np.ndarray:
        """
        Ensure the image has sufficient resolution for OMR.

        Upscales if necessary to target DPI (assuming 8.5x11" page).

        Args:
            image: Grayscale image

        Returns:
            Image with sufficient resolution
        """
        height, width = image.shape

        # Assume standard letter size (8.5 x 11 inches)
        # Calculate current approximate DPI based on width
        # (assuming landscape orientation is more common for music)
        assumed_width_inches = 11.0
        current_dpi = width / assumed_width_inches

        if current_dpi < self.target_dpi:
            # Need to upscale
            scale_factor = self.target_dpi / current_dpi
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            logger.info(
                f"Upscaling from ~{current_dpi:.0f} DPI to {self.target_dpi} DPI"
            )
            logger.info(f"New size: {new_width}x{new_height}")

            # Use INTER_CUBIC for upscaling (better quality)
            upscaled = cv2.resize(
                image, (new_width, new_height), interpolation=cv2.INTER_CUBIC
            )

            return upscaled

        return image


def preprocess_for_omr(
    input_path: str, output_path: str, target_dpi: int = 300, enable_all: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to preprocess an image with default settings.

    Args:
        input_path: Path to input image
        output_path: Path to save preprocessed image
        target_dpi: Target DPI for output (default: 300)
        enable_all: Enable all preprocessing steps (default: True)

    Returns:
        Tuple of (success, error_message)
    """
    preprocessor = ImagePreprocessor(
        target_dpi=target_dpi,
        enable_deskew=enable_all,
        enable_perspective_correction=enable_all,
        enable_denoising=enable_all,
        enable_binarization=enable_all,
    )

    return preprocessor.preprocess(input_path, output_path)
