#!/usr/bin/env python3
"""
Test script for image preprocessing functionality.

This script tests the image preprocessing pipeline without requiring
a full Docker environment or Audiveris installation.
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.image_preprocessing import ImagePreprocessor, preprocess_for_omr


def test_preprocessor_initialization():
    """Test that the preprocessor can be initialized."""
    print("Testing preprocessor initialization...")

    preprocessor = ImagePreprocessor()
    assert preprocessor.target_dpi == 300
    assert preprocessor.enable_deskew is True
    assert preprocessor.enable_perspective_correction is True

    print("✓ Preprocessor initialization successful")


def test_preprocessor_with_custom_settings():
    """Test preprocessor with custom settings."""
    print("\nTesting preprocessor with custom settings...")

    preprocessor = ImagePreprocessor(
        target_dpi=400,
        enable_deskew=False,
        enable_perspective_correction=False,
    )

    assert preprocessor.target_dpi == 400
    assert preprocessor.enable_deskew is False
    assert preprocessor.enable_perspective_correction is False

    print("✓ Custom settings applied successfully")


def test_convenience_function():
    """Test the convenience function."""
    print("\nTesting convenience function...")

    # Just verify it can be called (won't actually process without a file)
    try:
        preprocess_for_omr
        print("✓ Convenience function is accessible")
    except Exception as e:
        print(f"✗ Failed to access convenience function: {e}")
        return False

    return True


def _synthetic_page(interline: int, width: int = 2000, height: int = 2600, noise: float = 0.0):
    """White page with 6 five-line staves spaced `interline` px apart."""
    import numpy as np

    page = np.full((height, width), 245, np.uint8)
    thickness = max(1, interline // 10)
    staff_gap = interline * 8
    for s in range(6):
        top = 150 + s * staff_gap
        for line in range(5):
            y = top + line * interline
            if y + thickness < height:
                page[y : y + thickness, 100 : width - 100] = 20
    if noise:
        rng = np.random.default_rng(0)
        page = np.clip(page + rng.normal(0, noise, page.shape), 0, 255).astype(np.uint8)
    return page


def test_interline_and_scaling():
    """Interline estimate, clean detection, and scale normalization."""
    print("\nTesting interline estimation and scaling...")

    import numpy as np

    for interline in (8, 12, 20, 33):
        est = ImagePreprocessor.estimate_interline(_synthetic_page(interline))
        assert est is not None and abs(est - interline) <= 1, (interline, est)
    assert ImagePreprocessor.estimate_interline(np.full((1000, 800), 255, np.uint8)) is None

    assert ImagePreprocessor._is_clean(_synthetic_page(20))
    assert not ImagePreprocessor._is_clean(_synthetic_page(20, noise=20))

    pre = ImagePreprocessor()
    small = _synthetic_page(10, width=1000, height=1300)
    scaled = pre._normalize_scale(small)
    assert abs(scaled.shape[1] - 2000) <= 2, scaled.shape
    ok = _synthetic_page(20)
    assert pre._normalize_scale(ok) is ok

    print("OK interline estimation and scaling")


def test_deskew_large_angle():
    """Deskew recovers rotations beyond the old +-5 degree search range."""
    print("\nTesting deskew of an 8 degree rotation...")

    import cv2

    page = _synthetic_page(20)
    h, w = page.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), -8.0, 1.0)
    rotated = cv2.warpAffine(page, m, (w, h), borderValue=245)
    _, angle = ImagePreprocessor()._deskew(rotated)
    assert abs(angle - 8.0) <= 0.3, angle

    print("OK deskew")


def test_imports():
    """Test that all required dependencies are available."""
    print("\nTesting imports...")

    try:
        import cv2

        print(f"✓ OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False

    try:
        import numpy as np

        print(f"✓ NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False

    try:
        from PIL import Image

        print(f"✓ Pillow is available")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Image Preprocessing Test Suite")
    print("=" * 60)

    try:
        # Test imports first
        if not test_imports():
            print("\n❌ Import tests failed. Please install required dependencies:")
            print("   uv sync  (from the backend/ directory)")
            return 1

        # Test basic functionality
        test_preprocessor_initialization()
        test_preprocessor_with_custom_settings()
        test_convenience_function()
        test_interline_and_scaling()
        test_deskew_large_angle()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nPreprocessing is ready to use.")
        print("Next steps:")
        print("  1. Rebuild Docker containers: docker-compose build")
        print("  2. Restart services: docker-compose up")
        print("  3. Upload a music score image to test end-to-end")

        return 0

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
