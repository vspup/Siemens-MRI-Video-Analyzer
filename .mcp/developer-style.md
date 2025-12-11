# Developer Style Guide

## Python Version

- Use **Python 3.11+**
- Leverage modern Python features (type hints, pathlib, etc.)

## Code Style

- Follow **PEP 8** formatting
- Use **type hints** for all function parameters and return values
- Add **docstrings** to all public functions and classes
- Keep functions **small and readable**
- Use descriptive variable names

## Type Hints

```python
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

def process_video(
    video_path: Path,
    config_path: Path,
    output_path: Path
) -> None:
    """Process video with OCR."""
    ...
```

## Docstrings

Use Google-style docstrings:

```python
def extract_text_from_roi(roi_image: cv2.Mat) -> str:
    """
    Extract text from ROI image using OCR.

    Args:
        roi_image: Cropped ROI image

    Returns:
        Extracted text string
    """
    ...
```

## Error Handling

- Use specific exception types
- Provide clear error messages
- Handle file I/O errors gracefully

## Dependencies

- Use well-established packages:
  - `opencv-python` for video/image processing
  - `pytesseract` for OCR
  - `pyyaml` for configuration
  - `click` for CLI
  - `numpy` for numerical operations

## Code Organization

- One class/function per logical unit
- Group related functions in modules
- Use utilities for reusable code
- Keep CLI thin - delegate to stage modules

