"""Setup ROI: ROI selection tool."""

import cv2
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional, Tuple

from smva.utils.video import get_video_metadata, extract_preview_frames, load_frame
from smva.utils.roi import save_roi_config


class ROISelector:
    """Interactive ROI selector using OpenCV."""

    def __init__(self, image: cv2.Mat):
        """
        Initialize ROI selector.

        Args:
            image: Image to select ROI from
        """
        self.image = image.copy()
        self.display_image = image.copy()
        self.roi_start = None
        self.roi_end = None
        self.roi_selected = False
        self.window_name = "Select ROI - Click and drag, press SPACE to confirm, ESC to cancel"

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for ROI selection."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.roi_start = (x, y)
            self.roi_selected = False

        elif event == cv2.EVENT_MOUSEMOVE and self.roi_start is not None:
            self.display_image = self.image.copy()
            cv2.rectangle(
                self.display_image,
                self.roi_start,
                (x, y),
                (0, 255, 0),
                2,
            )
            cv2.imshow(self.window_name, self.display_image)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.roi_start is not None:
                self.roi_end = (x, y)
                self.roi_selected = True
                self.display_image = self.image.copy()
                cv2.rectangle(
                    self.display_image,
                    self.roi_start,
                    self.roi_end,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow(self.window_name, self.display_image)

    def select_roi(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Interactive ROI selection.

        Returns:
            Tuple of (x, y, width, height) or None if cancelled
        """
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        cv2.imshow(self.window_name, self.display_image)

        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                cv2.destroyAllWindows()
                return None

            elif key == 32:  # SPACE
                if self.roi_selected and self.roi_start and self.roi_end:
                    x1, y1 = self.roi_start
                    x2, y2 = self.roi_end

                    # Ensure x1 < x2 and y1 < y2
                    x = min(x1, x2)
                    y = min(y1, y2)
                    w = abs(x2 - x1)
                    h = abs(y2 - y1)

                    cv2.destroyAllWindows()
                    return (x, y, w, h)

    def get_roi(self) -> Optional[Tuple[int, int, int, int]]:
        """Get selected ROI."""
        return self.select_roi()


def select_video_file() -> Optional[Path]:
    """
    Open file dialog to select video file.

    Returns:
        Path to selected video or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide main window

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


def run_setup_roi() -> None:
    """Run Setup ROI: ROI selection."""
    print("Setup ROI: ROI Selection")
    print("=" * 50)

    # Select video file
    video_path = select_video_file()
    if not video_path:
        print("No video file selected. Exiting.")
        return

    print(f"Selected video: {video_path}")

    # Get video metadata
    try:
        width, height, fps, frame_count = get_video_metadata(video_path)
        print(f"Video metadata:")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps:.2f}")
        print(f"  Frame count: {frame_count}")
    except Exception as e:
        print(f"Error reading video metadata: {e}")
        return

    # Extract preview frames
    output_dir = Path("result/frames_preview")
    print(f"\nExtracting 5 preview frames to {output_dir}...")
    try:
        preview_frames = extract_preview_frames(video_path, output_dir, num_frames=5)
        print(f"Extracted {len(preview_frames)} preview frames")
    except Exception as e:
        print(f"Error extracting preview frames: {e}")
        return

    # Load first preview frame for ROI selection
    if preview_frames:
        preview_image = cv2.imread(str(preview_frames[0]))
        if preview_image is None:
            print(f"Error loading preview frame: {preview_frames[0]}")
            return

        print("\n" + "=" * 50)
        print("ROI Selection Instructions:")
        print("1. Click and drag to draw a rectangle around the data block")
        print("2. The block should include all 4 lines:")
        print("   - ACTUAL CURRENT")
        print("   - MPS VOLTS")
        print("   - MAG VOLTS")
        print("   - Elapsed Time")
        print("3. Press SPACE to confirm, ESC to cancel")
        print("=" * 50)

        # Select ROI
        selector = ROISelector(preview_image)
        roi = selector.get_roi()

        if roi is None:
            print("ROI selection cancelled.")
            return

        x, y, w, h = roi
        print(f"\nSelected ROI: x={x}, y={y}, w={w}, h={h}")

        # Save ROI configuration
        config_path = Path("config/roi.yaml")
        roi_dict = {"x": x, "y": y, "w": w, "h": h}
        video_metadata = {
            "width": width,
            "height": height,
            "fps": fps,
        }

        save_roi_config(config_path, roi_dict, video_metadata)
        print(f"ROI configuration saved to {config_path}")
        print("\nSetup ROI completed successfully!")

    else:
        print("No preview frames extracted.")

