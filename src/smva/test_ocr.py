"""Test OCR: OCR processing of video frames for verification."""

import json
import cv2
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import List, Dict, Any, Optional

from smva.utils.video import get_video_metadata
from smva.utils.roi import load_roi_config
from smva.utils.ocr import extract_text_from_roi, parse_mri_data, time_string_to_seconds


def select_video_file() -> Optional[Path]:
    """
    Open file dialog to select video file.

    Returns:
        Path to selected video or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Video File",
        filetypes=[
            ("Video files", "*.mp4 *.avi *.mov *.mkv"),
            ("All files", "*.*"),
        ],
    )

    root.destroy()

    if file_path:
        return Path(file_path)
    return None


def process_test_frames(video_path: Path, config_path: Path, num_frames: int = 5) -> None:
    """
    Process test frames with OCR for verification.
    Extracts evenly spaced frames and displays results.

    Args:
        video_path: Path to video file
        config_path: Path to ROI config file
        num_frames: Number of test frames to extract
    """
    # Load ROI configuration
    config = load_roi_config(config_path)
    roi = config["roi"]
    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]

    # Get video metadata
    width, height, fps, frame_count = get_video_metadata(video_path)

    print(f"Test processing video: {video_path.name}")
    print(f"Total frames: {frame_count}")
    print(f"ROI: x={x}, y={y}, w={w}, h={h}")
    print(f"Extracting {num_frames} test frames evenly spaced...\n")

    # Calculate frame indices (evenly spaced: start, middle, end)
    frame_indices = [
        int(frame_count * i / (num_frames + 1)) for i in range(1, num_frames + 1)
    ]

    # Create output directory for test frames
    test_frames_dir = Path("result/test_frames")
    test_frames_dir.mkdir(parents=True, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    results: List[Dict[str, Any]] = []

    print("=" * 70)
    print(f"{'Frame':<10} {'Time':<12} {'Current (A)':<15} {'MPS (V)':<12} {'MAG (V)':<12} {'Status':<10}")
    print("=" * 70)

    for idx, frame_num in enumerate(frame_indices):
        # Seek to frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()

        if not ret:
            print(f"Frame {frame_num:<10} {'ERROR':<12} {'Could not read frame':<15}")
            continue

        # Crop ROI
        roi_image = frame[y : y + h, x : x + w]

        # Save ROI image for verification
        roi_image_path = test_frames_dir / f"frame_{frame_num:06d}_roi.jpg"
        cv2.imwrite(str(roi_image_path), roi_image)

        # Also save full frame with ROI rectangle marked
        frame_with_roi = frame.copy()
        cv2.rectangle(frame_with_roi, (x, y), (x + w, y + h), (0, 255, 0), 2)
        full_frame_path = test_frames_dir / f"frame_{frame_num:06d}_full.jpg"
        cv2.imwrite(str(full_frame_path), frame_with_roi)

        # Perform OCR
        text = extract_text_from_roi(roi_image)

        # Parse data
        parsed_data = parse_mri_data(text)

        if parsed_data:
            current_a = parsed_data["current_A"]
            time_sec = time_string_to_seconds(parsed_data["time"])

            # Check if should skip (current > 550)
            skip_status = "SKIPPED" if current_a > 550 else "OK"

            result = {
                "frame": frame_num,
                "time_sec": time_sec,
                "current_A": current_a,
                "mps_V": parsed_data["mps_V"],
                "mag_V": parsed_data["mag_V"],
                "time": parsed_data["time"],
                "status": skip_status,
                "roi_image": str(roi_image_path),
                "full_frame": str(full_frame_path),
            }

            results.append(result)

            # Display result
            print(
                f"{frame_num:<10} "
                f"{parsed_data['time']:<12} "
                f"{current_a:<15.2f} "
                f"{parsed_data['mps_V']:<12.4f} "
                f"{parsed_data['mag_V']:<12.4f} "
                f"{skip_status:<10}"
            )
        else:
            print(f"{frame_num:<10} {'FAILED':<12} {'OCR parsing failed':<15}")

    cap.release()

    print("=" * 70)
    print(f"\nTest Results Summary:")
    print(f"  Total test frames: {num_frames}")
    print(f"  Successfully parsed: {len(results)}")
    print(f"  Failed to parse: {num_frames - len(results)}")
    print(f"  Would be skipped (current > 550A): {sum(1 for r in results if r.get('status') == 'SKIPPED')}")
    print(f"\n  Test frames saved to: {test_frames_dir.absolute()}")

    # Display detailed results
    print("\n" + "=" * 70)
    print("Detailed Results:")
    print("=" * 70)
    for result in results:
        print(f"\nFrame {result['frame']}:")
        print(f"  Time: {result['time']} ({result['time_sec']:.1f} seconds)")
        print(f"  ACTUAL CURRENT: {result['current_A']:.2f} A")
        print(f"  MPS VOLTS: {result['mps_V']:.4f} V")
        print(f"  MAG VOLTS: {result['mag_V']:.4f} V")
        print(f"  Status: {result['status']}")
        print(f"  ROI image: {result.get('roi_image', 'N/A')}")
        print(f"  Full frame: {result.get('full_frame', 'N/A')}")


def run_test_ocr() -> None:
    """Run Test OCR: Test OCR processing on sample frames."""
    print("Test OCR: Test OCR Processing")
    print("=" * 50)

    # Select video file
    video_path = select_video_file()
    if not video_path:
        print("No video file selected. Exiting.")
        return

    # Load ROI config
    config_path = Path("config/roi.yaml")
    if not config_path.exists():
        print(f"ROI configuration not found: {config_path}")
        print("Please run 'smva setup-roi' first to select ROI.")
        return

    # Process test frames
    try:
        process_test_frames(video_path, config_path, num_frames=5)
        print("\nTest OCR completed successfully!")
    except Exception as e:
        print(f"Error processing video: {e}")
        raise

