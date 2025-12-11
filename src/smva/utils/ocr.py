"""OCR processing utilities."""

import re
import os
import pytesseract
import cv2
import numpy as np
from typing import Optional, Dict, Any

# Configure Tesseract path for Windows
if os.name == "nt":  # Windows
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


def preprocess_image_for_ocr(image: cv2.Mat) -> cv2.Mat:
    """
    Preprocess image to improve OCR accuracy.

    Args:
        image: Input image

    Returns:
        Preprocessed image
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Optional: denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

    return denoised


def extract_text_from_roi(roi_image: cv2.Mat) -> str:
    """
    Extract text from ROI image using OCR.

    Args:
        roi_image: Cropped ROI image

    Returns:
        Extracted text string
    """
    processed = preprocess_image_for_ocr(roi_image)
    text = pytesseract.image_to_string(processed, config="--psm 6")
    return text


def parse_mri_data(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse four values from OCR text in fixed order:
    1. ACTUAL CURRENT → value (A)
    2. MPS VOLTS → value (V)
    3. MAG VOLTS → value (V)
    4. Elapsed Time → hh:mm:ss

    Args:
        text: OCR extracted text

    Returns:
        Dictionary with parsed values or None if parsing failed
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Try to find the four values
    current_a = None
    mps_v = None
    mag_v = None
    time_str = None

    # Pattern for current: "ACTUAL CURRENT" followed by number and "A"
    current_pattern = r"ACTUAL\s+CURRENT.*?([\d.]+)\s*A"
    # Pattern for MPS volts: "MPS VOLTS" followed by optional sign, number and "V"
    mps_pattern = r"MPS\s+VOLTS.*?([+-]?[\d.]+)\s*V"
    # Pattern for MAG volts: "MAG VOLTS" followed by optional sign, number and "V"
    mag_pattern = r"MAG\s+VOLTS.*?([+-]?[\d.]+)\s*V"
    # Pattern for time: "Elapsed Time" followed by hh:mm:ss
    time_pattern = r"Elapsed\s+Time.*?(\d{2}:\d{2}:\d{2})"

    full_text = " ".join(lines)

    # Search for patterns
    current_match = re.search(current_pattern, full_text, re.IGNORECASE)
    mps_match = re.search(mps_pattern, full_text, re.IGNORECASE)
    mag_match = re.search(mag_pattern, full_text, re.IGNORECASE)
    time_match = re.search(time_pattern, full_text, re.IGNORECASE)

    if current_match:
        try:
            current_a = float(current_match.group(1))
        except ValueError:
            pass

    if mps_match:
        try:
            mps_v = float(mps_match.group(1))
        except ValueError:
            pass

    if mag_match:
        try:
            mag_v = float(mag_match.group(1))
        except ValueError:
            pass

    if time_match:
        time_str = time_match.group(1)

    # Alternative: try to parse from lines if patterns don't match
    if not all([current_a is not None, mps_v is not None, mag_v is not None, time_str]):
        # Try simpler patterns - look for numbers with units
        for line in lines:
            # Current
            if "CURRENT" in line.upper() and current_a is None:
                match = re.search(r"([\d.]+)\s*A", line, re.IGNORECASE)
                if match:
                    try:
                        current_a = float(match.group(1))
                    except ValueError:
                        pass

            # MPS
            if "MPS" in line.upper() and mps_v is None:
                match = re.search(r"([+-]?[\d.]+)\s*V", line, re.IGNORECASE)
                if match:
                    try:
                        mps_v = float(match.group(1))
                    except ValueError:
                        pass

            # MAG
            if "MAG" in line.upper() and mag_v is None:
                match = re.search(r"([+-]?[\d.]+)\s*V", line, re.IGNORECASE)
                if match:
                    try:
                        mag_v = float(match.group(1))
                    except ValueError:
                        pass

            # Time
            if "TIME" in line.upper() and time_str is None:
                match = re.search(r"(\d{2}:\d{2}:\d{2})", line)
                if match:
                    time_str = match.group(1)

    if all([current_a is not None, mps_v is not None, mag_v is not None, time_str]):
        return {
            "current_A": current_a,
            "mps_V": mps_v,
            "mag_V": mag_v,
            "time": time_str,
        }

    return None


def time_string_to_seconds(time_str: str) -> float:
    """
    Convert time string (hh:mm:ss) to seconds.

    Args:
        time_str: Time string in format hh:mm:ss

    Returns:
        Time in seconds
    """
    parts = time_str.split(":")
    if len(parts) != 3:
        return 0.0

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return 0.0

