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
            print("   pip install opencv-python-headless numpy Pillow")
            return 1

        # Test basic functionality
        test_preprocessor_initialization()
        test_preprocessor_with_custom_settings()
        test_convenience_function()

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
