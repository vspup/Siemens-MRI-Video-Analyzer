"""Video processing utilities."""

import cv2
from pathlib import Path
from typing import Tuple, Optional


def get_video_metadata(video_path: Path) -> Tuple[int, int, float, int]:
    """
    Extract video metadata.

    Args:
        video_path: Path to video file

    Returns:
        Tuple of (width, height, fps, frame_count)
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()
    return width, height, fps, frame_count


def extract_preview_frames(
    video_path: Path, output_dir: Path, num_frames: int = 5
) -> list[Path]:
    """
    Extract evenly spaced preview frames from video.

    Args:
        video_path: Path to video file
        output_dir: Directory to save preview frames
        num_frames: Number of frames to extract

    Returns:
        List of paths to saved frame images
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_indices = [
        int(frame_count * i / (num_frames + 1)) for i in range(1, num_frames + 1)
    ]

    saved_paths = []
    for idx, frame_num in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if ret:
            output_path = output_dir / f"preview_frame_{idx + 1:02d}.jpg"
            cv2.imwrite(str(output_path), frame)
            saved_paths.append(output_path)

    cap.release()
    return saved_paths


def load_frame(video_path: Path, frame_number: int) -> Optional[cv2.Mat]:
    """
    Load a specific frame from video.

    Args:
        video_path: Path to video file
        frame_number: Frame number to load (0-indexed)

    Returns:
        Frame image or None if failed
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()

    return frame if ret else None

