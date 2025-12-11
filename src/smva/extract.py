"""Extract: Full video processing with frame sampling and fallback."""

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


def try_parse_frame(
    cap: cv2.VideoCapture,
    frame_num: int,
    roi: Dict[str, int],
) -> Optional[Dict[str, Any]]:
    """
    Try to parse data from a specific frame.

    Args:
        cap: Video capture object
        frame_num: Frame number to process
        roi: ROI coordinates (x, y, w, h)

    Returns:
        Parsed data dictionary or None if failed
    """
    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]

    # Seek to frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()

    if not ret:
        return None

    # Crop ROI
    roi_image = frame[y : y + h, x : x + w]

    # Perform OCR
    text = extract_text_from_roi(roi_image)

    # Parse data
    parsed_data = parse_mri_data(text)

    if parsed_data:
        current_a = parsed_data["current_A"]

        # Skip frames where current_A > 550
        if current_a > 550:
            return None

        time_sec = time_string_to_seconds(parsed_data["time"])

        return {
            "frame": frame_num,
            "time_sec": time_sec,
            "current_A": current_a,
            "mps_V": parsed_data["mps_V"],
            "mag_V": parsed_data["mag_V"],
            "time": parsed_data["time"],
        }

    return None


def process_frame_with_fallback(
    cap: cv2.VideoCapture,
    target_frame: int,
    roi: Dict[str, int],
    max_fallback_range: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    Process frame with fallback to neighboring frames if parsing fails.

    Args:
        cap: Video capture object
        target_frame: Target frame number
        roi: ROI coordinates
        max_fallback_range: Maximum range to search for fallback frames

    Returns:
        Parsed data dictionary or None if all attempts failed
    """
    # Try target frame first
    result = try_parse_frame(cap, target_frame, roi)
    if result:
        return result

    # Try neighboring frames: +1, -1, +2, -2, ...
    for offset in range(1, max_fallback_range + 1):
        # Try frame after
        frame_after = target_frame + offset
        result = try_parse_frame(cap, frame_after, roi)
        if result:
            result["original_frame"] = target_frame
            result["fallback_offset"] = offset
            return result

        # Try frame before
        frame_before = target_frame - offset
        if frame_before >= 0:
            result = try_parse_frame(cap, frame_before, roi)
            if result:
                result["original_frame"] = target_frame
                result["fallback_offset"] = -offset
                return result

    return None


def process_full_video(
    video_path: Path,
    config_path: Path,
    output_path: Path,
    frame_interval: int = 10,
    max_fallback_range: int = 5,
) -> None:
    """
    Process full video with frame sampling and fallback.

    Args:
        video_path: Path to video file
        config_path: Path to ROI config file
        output_path: Path to output JSON file
        frame_interval: Process every Nth frame (default: 10)
        max_fallback_range: Maximum range for fallback frames (default: 5)
    """
    # Load ROI configuration
    config = load_roi_config(config_path)
    roi = config["roi"]

    # Get video metadata
    width, height, fps, frame_count = get_video_metadata(video_path)

    print(f"Processing full video: {video_path.name}")
    print(f"Total frames: {frame_count}")
    print(f"Frame interval: every {frame_interval} frames")
    print(f"Max fallback range: ±{max_fallback_range} frames")
    print(f"ROI: x={roi['x']}, y={roi['y']}, w={roi['w']}, h={roi['h']}")

    # Calculate target frames (every Nth frame)
    target_frames = list(range(0, frame_count, frame_interval))

    print(f"\nProcessing {len(target_frames)} target frames...")

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    results: List[Dict[str, Any]] = []
    processed_count = 0
    failed_count = 0
    fallback_used_count = 0

    for idx, target_frame in enumerate(target_frames):
        # Process frame with fallback
        result = process_frame_with_fallback(
            cap, target_frame, roi, max_fallback_range
        )

        if result:
            # Check if fallback was used
            if "fallback_offset" in result:
                fallback_used_count += 1
                original_frame = result.pop("original_frame")
                fallback_offset = result.pop("fallback_offset")
                print(
                    f"  Frame {target_frame}: used fallback frame {target_frame + fallback_offset} "
                    f"(offset: {fallback_offset:+d})"
                )

            results.append(result)
            processed_count += 1

            if processed_count % 50 == 0:
                print(f"  Processed {processed_count}/{len(target_frames)} frames...")
        else:
            failed_count += 1
            if failed_count % 10 == 0:
                print(f"  Failed to parse {failed_count} frames so far...")

    cap.release()

    # Sort results by frame number
    results.sort(key=lambda x: x["frame"])

    # Save results
    output_data = {
        "video": video_path.name,
        "fps": fps,
        "frame_interval": frame_interval,
        "total_frames": frame_count,
        "processed_frames": len(target_frames),
        "successful_parses": len(results),
        "failed_parses": failed_count,
        "fallback_used": fallback_used_count,
        "data": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nProcessing complete!")
    print(f"  Target frames processed: {len(target_frames)}")
    print(f"  Successfully parsed: {len(results)}")
    print(f"  Failed to parse: {failed_count}")
    print(f"  Fallback used: {fallback_used_count}")
    print(f"  Output saved to: {output_path}")


def run_extract() -> None:
    """Run Extract: Full video processing with sampling and fallback."""
    print("Extract: Full Video Processing")
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

    # Process full video
    output_path = Path("result/output.json")
    try:
        process_full_video(
            video_path,
            config_path,
            output_path,
            frame_interval=10,
            max_fallback_range=5,
        )
        print("\nExtract completed successfully!")
    except Exception as e:
        print(f"Error processing video: {e}")
        raise

