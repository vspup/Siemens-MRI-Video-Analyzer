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


def calculate_time_from_frame(frame_num: int, fps: float) -> tuple[float, int]:
    """
    Calculate precise time from frame number.

    Args:
        frame_num: Frame number
        fps: Frames per second

    Returns:
        Tuple of (time_sec_precise, time_ms) where:
        - time_sec_precise: Precise time in seconds with milliseconds
        - time_ms: Milliseconds part (0-999)
    """
    time_sec_precise = frame_num / fps
    time_ms = int((time_sec_precise % 1) * 1000)
    return time_sec_precise, time_ms


def extract_time_from_frames(
    cap: cv2.VideoCapture,
    frame_numbers: List[int],
    roi: Dict[str, int],
) -> Optional[float]:
    """
    Extract and average time from multiple frames.

    Args:
        cap: Video capture object
        frame_numbers: List of frame numbers to sample
        roi: ROI coordinates (x, y, w, h)

    Returns:
        Average time in seconds or None if extraction failed
    """
    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
    times = []

    for frame_num in frame_numbers:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()

        if not ret:
            continue

        # Crop ROI
        roi_image = frame[y : y + h, x : x + w]

        # Perform OCR
        text = extract_text_from_roi(roi_image)

        # Parse data
        parsed_data = parse_mri_data(text)

        if parsed_data:
            time_sec = time_string_to_seconds(parsed_data["time"])
            times.append(time_sec)

    if len(times) == 0:
        return None

    # Return median to avoid outliers
    times.sort()
    return times[len(times) // 2]


def validate_extracted_data(
    parsed_data: Dict[str, Any],
    frame_num: int,
    fps: float,
    validation_config: Dict[str, float],
    previous_data: Optional[Dict[str, Any]] = None,
    max_pause_threshold: Optional[float] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate extracted data against configured limits.

    Args:
        parsed_data: Parsed data dictionary with current_A, mps_V, mag_V, time
        frame_num: Frame number
        fps: Frames per second
        validation_config: Validation configuration with limits
        previous_data: Previous frame data for time consistency check
        max_pause_threshold: Maximum allowed pause duration in seconds (auto-calculated from experiment)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Extract validation limits
    current_min = validation_config.get("current_min", -10)
    current_max = validation_config.get("current_max", 600)
    voltage_min = validation_config.get("voltage_min", -10)
    voltage_max = validation_config.get("voltage_max", 15)
    time_tolerance = validation_config.get("time_tolerance_sec", 0.5)

    # Validate current
    current_a = parsed_data["current_A"]
    if not (current_min <= current_a <= current_max):
        return False, f"Current {current_a}A out of range [{current_min}, {current_max}]"

    # Validate MPS voltage
    mps_v = parsed_data["mps_V"]
    if not (voltage_min <= mps_v <= voltage_max):
        return False, f"MPS voltage {mps_v}V out of range [{voltage_min}, {voltage_max}]"

    # Validate MAG voltage
    mag_v = parsed_data["mag_V"]
    if not (voltage_min <= mag_v <= voltage_max):
        return False, f"MAG voltage {mag_v}V out of range [{voltage_min}, {voltage_max}]"

    # Validate time consistency with previous frame (if available)
    # TEMPORARILY DISABLED - Skip time validation to see results without it
    # if previous_data is not None:
    #     time_sec_ocr = time_string_to_seconds(parsed_data["time"])
    #     prev_time_sec_ocr = time_string_to_seconds(previous_data["time"])
    #     
    #     # STRICT CHECK: Time should NEVER go backwards
    #     if time_sec_ocr < prev_time_sec_ocr:
    #         return False, f"Time went backwards: {prev_time_sec_ocr}s -> {time_sec_ocr}s"
    #     
    #     # Calculate expected time difference based on frame interval
    #     frame_diff = frame_num - previous_data["frame"]
    #     expected_time_diff = frame_diff / fps
    #     actual_time_diff = time_sec_ocr - prev_time_sec_ocr
    #     
    #     # FLEXIBLE CHECK for time consistency
    #     # Allow for pauses in recording: if actual time jump is larger than threshold,
    #     # it's likely a pause, not an error - so we skip detailed validation
    #     pause_threshold = max_pause_threshold if max_pause_threshold else expected_time_diff * 2
    #     
    #     if actual_time_diff > pause_threshold:
    #         # Detected possible pause/gap in recording
    #         # Skip detailed consistency check, only ensured time didn't go backwards
    #         pass
    #     else:
    #         # Normal operation: check time consistency with tolerance
    #         # (accounting for 1-second display update granularity)
    #         time_diff_error = abs(actual_time_diff - expected_time_diff)
    #         
    #         if time_diff_error > time_tolerance:
    #             return False, f"Time inconsistency: expected diff={expected_time_diff:.2f}s, actual diff={actual_time_diff:.2f}s, error={time_diff_error:.2f}s"

    return True, None


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
    fps: float,
    validation_config: Dict[str, float],
    previous_data: Optional[Dict[str, Any]] = None,
    max_pause_threshold: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Try to parse data from a specific frame.

    Args:
        cap: Video capture object
        frame_num: Frame number to process
        roi: ROI coordinates (x, y, w, h)
        fps: Frames per second
        validation_config: Validation configuration with limits
        previous_data: Previous successfully parsed frame data for validation
        max_pause_threshold: Maximum allowed pause duration in seconds

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
        # Validate extracted data
        is_valid, error_msg = validate_extracted_data(
            parsed_data, frame_num, fps, validation_config, previous_data, max_pause_threshold
        )

        if not is_valid:
            # Optionally log validation failure for debugging
            # print(f"  Validation failed for frame {frame_num}: {error_msg}")
            return None

        # Calculate precise time from frame number
        time_sec_precise, time_ms = calculate_time_from_frame(frame_num, fps)
        time_sec = time_string_to_seconds(parsed_data["time"])

        return {
            "frame": frame_num,
            "time_sec": time_sec,
            "time_sec_precise": round(time_sec_precise, 3),
            "time_ms": time_ms,
            "current_A": parsed_data["current_A"],
            "mps_V": parsed_data["mps_V"],
            "mag_V": parsed_data["mag_V"],
            "time": parsed_data["time"],
        }

    return None


def process_frame_with_fallback(
    cap: cv2.VideoCapture,
    target_frame: int,
    roi: Dict[str, int],
    fps: float,
    validation_config: Dict[str, float],
    previous_data: Optional[Dict[str, Any]] = None,
    max_pause_threshold: Optional[float] = None,
    max_fallback_range: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    Process frame with fallback to neighboring frames if parsing fails.

    Args:
        cap: Video capture object
        target_frame: Target frame number
        roi: ROI coordinates
        fps: Frames per second
        validation_config: Validation configuration with limits
        previous_data: Previous successfully parsed frame data for validation
        max_pause_threshold: Maximum allowed pause duration in seconds
        max_fallback_range: Maximum range to search for fallback frames

    Returns:
        Parsed data dictionary or None if all attempts failed
    """
    # Try target frame first
    result = try_parse_frame(cap, target_frame, roi, fps, validation_config, previous_data, max_pause_threshold)
    if result:
        return result

    # Try neighboring frames: +1, -1, +2, -2, ...
    for offset in range(1, max_fallback_range + 1):
        # Try frame after
        frame_after = target_frame + offset
        result = try_parse_frame(cap, frame_after, roi, fps, validation_config, previous_data, max_pause_threshold)
        if result:
            result["original_frame"] = target_frame
            result["fallback_offset"] = offset
            return result

        # Try frame before
        frame_before = target_frame - offset
        if frame_before >= 0:
            result = try_parse_frame(cap, frame_before, roi, fps, validation_config, previous_data, max_pause_threshold)
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
    validation_config = config["validation"]

    # Get video metadata
    width, height, fps, frame_count = get_video_metadata(video_path)

    print(f"Processing full video: {video_path.name}")
    print(f"Total frames: {frame_count}")
    print(f"Frame interval: every {frame_interval} frames")
    print(f"Max fallback range: ±{max_fallback_range} frames")
    print(f"ROI: x={roi['x']}, y={roi['y']}, w={roi['w']}, h={roi['h']}")
    
    # Open video for time extraction
    cap_temp = cv2.VideoCapture(str(video_path))
    if not cap_temp.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    # Extract experiment start and end times
    print(f"\nExtracting experiment time range...")
    
    # Sample frames from different parts of the video to find meaningful start/end times
    # Start: sample from 5-20% of video (skip very beginning where experiment may not have started)
    # End: sample from last 5% of video
    start_sample_frames = [
        int(frame_count * 0.05 + i * frame_interval) for i in range(5)
    ]
    end_sample_frames = [
        max(frame_count - 1 - i * frame_interval, 0) for i in range(5)
    ]
    
    start_time = extract_time_from_frames(cap_temp, start_sample_frames, roi)
    end_time = extract_time_from_frames(cap_temp, end_sample_frames, roi)
    cap_temp.release()
    
    # Calculate max pause threshold (75% of experiment duration)
    max_pause_threshold = None
    if start_time is not None and end_time is not None and end_time > start_time:
        experiment_duration = end_time - start_time
        max_pause_threshold = experiment_duration * 0.75
        print(f"Experiment time range: {start_time:.0f}s - {end_time:.0f}s (duration: {experiment_duration:.0f}s)")
        print(f"Max pause threshold: {max_pause_threshold:.0f}s (75% of experiment duration)")
    else:
        print(f"Could not extract experiment time range, using default pause detection")
    
    print(f"\nValidation: Current [{validation_config['current_min']}, {validation_config['current_max']}]A, "
          f"Voltage [{validation_config['voltage_min']}, {validation_config['voltage_max']}]V, "
          f"Time tolerance {validation_config['time_tolerance_sec']}s")

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
    previous_result = None

    for idx, target_frame in enumerate(target_frames):
        # Process frame with fallback, using previous successful frame for validation
        result = process_frame_with_fallback(
            cap, target_frame, roi, fps, validation_config, previous_result, max_pause_threshold, max_fallback_range
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
            previous_result = result  # Update previous result for next frame validation

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
        "validation_config": validation_config,
        "experiment_start_time": start_time,
        "experiment_end_time": end_time,
        "max_pause_threshold": max_pause_threshold,
        "data": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nProcessing complete!")
    print(f"  Target frames processed: {len(target_frames)}")
    print(f"  Successfully parsed: {len(results)}")
    print(f"  Failed to parse (including validation failures): {failed_count}")
    print(f"  Fallback used: {fallback_used_count}")
    print(f"  Success rate: {len(results)/len(target_frames)*100:.1f}%")
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

