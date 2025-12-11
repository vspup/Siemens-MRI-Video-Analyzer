"""Plot: Plot graphs from extracted data."""

import json
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import numpy as np


def load_output_data(output_path: Path) -> Dict[str, Any]:
    """
    Load output data from JSON file.

    Args:
        output_path: Path to output JSON file

    Returns:
        Dictionary with video data
    """
    if not output_path.exists():
        raise FileNotFoundError(f"Output file not found: {output_path}")

    with open(output_path, "r") as f:
        data = json.load(f)

    if "data" not in data:
        raise ValueError("Invalid output file format: missing 'data' key")

    return data


def plot_graphs(data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot graphs with current on left axis and voltages on right axis.

    Args:
        data: Dictionary with video data
        output_path: Path to save the plot
    """
    video_data = data["data"]

    if not video_data:
        raise ValueError("No data to plot")

    # Extract data and filter invalid points
    # Physical limits:
    # Current: -10A to 600A
    # Voltages: -10V to 12V
    filtered_data = []
    filtered_indices = []
    for idx, item in enumerate(video_data):
        current_a = item["current_A"]
        mps_v = item["mps_V"]
        mag_v = item["mag_V"]
        
        # Skip points with invalid values
        if current_a < -10.0 or current_a > 600.0:
            continue
        if mps_v < -10.0 or mps_v > 12.0:
            continue
        if mag_v < -10.0 or mag_v > 12.0:
            continue
        
        filtered_data.append(item)
        filtered_indices.append(idx)
    
    if not filtered_data:
        raise ValueError("No valid data points after filtering")
    
    # Report filtering statistics
    original_count = len(video_data)
    filtered_count = len(filtered_data)
    skipped_count = original_count - filtered_count
    if skipped_count > 0:
        print(f"Filtered out {skipped_count} invalid data points ({filtered_count}/{original_count} valid)")
    
    # Extract filtered data
    time_sec = np.array([item["time_sec"] for item in filtered_data])
    current_a = np.array([item["current_A"] for item in filtered_data])
    mps_v = np.array([item["mps_V"] for item in filtered_data])
    mag_v = np.array([item["mag_V"] for item in filtered_data])
    filtered_indices = np.array(filtered_indices)
    
    # Additional filtering: remove spikes and outliers
    if len(current_a) > 2:
        valid_mask = np.ones(len(current_a), dtype=bool)
        
        # Filter 0: Remove points with invalid time jumps (backwards or too large forward)
        # This catches OCR errors that cause time to jump incorrectly
        dt = np.diff(time_sec)
        max_time_jump = 300.0  # Maximum allowed time jump in seconds (5 minutes)
        time_jump_filtered = 0
        
        for i in range(len(dt)):
            # Remove points where time goes backwards significantly
            if dt[i] < -10.0:  # Time goes backwards more than 10 seconds
                valid_mask[i + 1] = False
                time_jump_filtered += 1
            # Remove points where time jumps forward too much (likely OCR error)
            elif dt[i] > max_time_jump:
                valid_mask[i + 1] = False
                time_jump_filtered += 1
        
        if time_jump_filtered > 0:
            print(f"Filtered out {time_jump_filtered} points with invalid time jumps")
        
        # Filter 1: Remove points with excessive rate of change
        # This catches sudden spikes
        dt = np.diff(time_sec)
        dt = np.where(dt == 0, 1.0, dt)  # Avoid division by zero
        
        current_diff = np.abs(np.diff(current_a)) / dt
        mps_diff = np.abs(np.diff(mps_v)) / dt
        mag_diff = np.abs(np.diff(mag_v)) / dt
        
        max_current_rate = 50.0  # A/s
        max_voltage_rate = 5.0   # V/s
        
        for i in range(len(current_diff)):
            if current_diff[i] > max_current_rate or \
               mps_diff[i] > max_voltage_rate or \
               mag_diff[i] > max_voltage_rate:
                valid_mask[i + 1] = False
        
        # Filter 2: Remove isolated outliers (points that differ significantly from neighbors on both sides)
        # This catches single-point spikes that might pass rate-of-change filter
        for i in range(1, len(current_a) - 1):
            if not valid_mask[i]:
                continue
            
            # Check if current point is an outlier compared to neighbors
            prev_current = current_a[i - 1]
            curr_current = current_a[i]
            next_current = current_a[i + 1]
            
            prev_mps = mps_v[i - 1]
            curr_mps = mps_v[i]
            next_mps = mps_v[i + 1]
            
            prev_mag = mag_v[i - 1]
            curr_mag = mag_v[i]
            next_mag = mag_v[i + 1]
            
            # Calculate if current point is isolated (differs from both neighbors)
            current_is_isolated = (
                abs(curr_current - prev_current) > 100 and
                abs(curr_current - next_current) > 100 and
                abs(prev_current - next_current) < 50  # Neighbors are similar
            )
            
            mps_is_isolated = (
                abs(curr_mps - prev_mps) > 2.0 and
                abs(curr_mps - next_mps) > 2.0 and
                abs(prev_mps - next_mps) < 1.0  # Neighbors are similar
            )
            
            mag_is_isolated = (
                abs(curr_mag - prev_mag) > 2.0 and
                abs(curr_mag - next_mag) > 2.0 and
                abs(prev_mag - next_mag) < 1.0  # Neighbors are similar
            )
            
            if current_is_isolated or mps_is_isolated or mag_is_isolated:
                valid_mask[i] = False
        
        # Apply mask
        time_sec = time_sec[valid_mask]
        current_a = current_a[valid_mask]
        mps_v = mps_v[valid_mask]
        mag_v = mag_v[valid_mask]
        filtered_indices = filtered_indices[valid_mask]
        
        rate_filtered_count = np.sum(~valid_mask)
        if rate_filtered_count > 0:
            print(f"Filtered out {rate_filtered_count} spike/outlier points")
    
    # Apply median filter to smooth remaining data
    # Window size of 3 for light smoothing
    def median_filter(data: np.ndarray, window_size: int = 3) -> np.ndarray:
        """Simple median filter implementation."""
        if len(data) < window_size:
            return data
        filtered = np.zeros_like(data)
        half = window_size // 2
        for i in range(len(data)):
            start = max(0, i - half)
            end = min(len(data), i + half + 1)
            filtered[i] = np.median(data[start:end])
        return filtered
    
    if len(current_a) > 3:
        window_size = 3
        current_a = median_filter(current_a, window_size=window_size)
        mps_v = median_filter(mps_v, window_size=window_size)
        mag_v = median_filter(mag_v, window_size=window_size)
        print(f"Applied median filter (window size: {window_size})")
    
    # Convert back to lists for plotting
    time_sec = time_sec.tolist()
    current_a = current_a.tolist()
    mps_v = mps_v.tolist()
    mag_v = mag_v.tolist()
    
    # Prepare cleaned data for saving
    cleaned_data = []
    for i in range(len(time_sec)):
        # Get original data point
        original_idx = int(filtered_indices[i])
        original_item = video_data[original_idx]
        
        # Calculate time string from seconds
        total_seconds = int(time_sec[i])
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Build cleaned item with all original fields plus filtered values
        cleaned_item = {
            "time_sec": time_sec[i],
            "current_A": current_a[i],
            "mps_V": mps_v[i],
            "mag_V": mag_v[i],
            "time": time_str
        }
        
        # Add optional fields if they exist in original data
        if "time_sec_precise" in original_item:
            cleaned_item["time_sec_precise"] = original_item["time_sec_precise"]
        if "frame" in original_item:
            cleaned_item["frame"] = original_item["frame"]
        if "time_ms" in original_item:
            cleaned_item["time_ms"] = original_item["time_ms"]
        
        cleaned_data.append(cleaned_item)

    # Create figure and axes
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Left axis for current (red)
    color_current = "red"
    ax1.set_xlabel("Time (seconds)", fontsize=12)
    ax1.set_ylabel("Current (A)", color=color_current, fontsize=12)
    line1 = ax1.plot(
        time_sec, current_a, color=color_current, linewidth=1.5, 
        marker='o', markersize=1.5, label="Current (A)"
    )
    ax1.tick_params(axis="y", labelcolor=color_current)
    ax1.grid(True, alpha=0.3)

    # Right axis for voltages
    ax2 = ax1.twinx()
    color_mps = "cyan"  # голубой
    color_mag = "purple"  # фиолетовый
    ax2.set_ylabel("Voltage (V)", fontsize=12)
    line2 = ax2.plot(
        time_sec,
        mps_v,
        color=color_mps,
        linewidth=1.5,
        marker='o', markersize=1.5,
        label="MPS Voltage (V)",
    )
    line3 = ax2.plot(
        time_sec,
        mag_v,
        color=color_mag,
        linewidth=1.5,
        linestyle="-",
        marker='o', markersize=1.5,
        label="MAG Voltage (V)",
    )
    ax2.tick_params(axis="y")

    # Combine legends
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", fontsize=10)

    # Title
    video_name = data.get("video", "Unknown")
    plt.title(f"MRI Ramp Data: {video_name}", fontsize=14, fontweight="bold")

    # Adjust layout
    plt.tight_layout()

    # Save plot
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Graph saved to: {output_path}")

    # Save cleaned data to JSON
    cleaned_output_path = output_path.parent / "output_cleaned.json"
    cleaned_output_data = {
        "video": data.get("video", "Unknown"),
        "fps": data.get("fps", 30.0),
        "frame_interval": data.get("frame_interval", 10),
        "total_frames": data.get("total_frames", 0),
        "original_data_points": len(video_data),
        "cleaned_data_points": len(cleaned_data),
        "data": cleaned_data
    }
    
    with open(cleaned_output_path, "w") as f:
        json.dump(cleaned_output_data, f, indent=2)
    print(f"Cleaned data saved to: {cleaned_output_path}")

    # Also show the plot
    plt.show()


def run_plot() -> None:
    """Run Plot: Plot graphs from extracted data."""
    print("Plot: Plot Graphs")
    print("=" * 50)

    # Load output data
    output_path = Path("result/output.json")
    if not output_path.exists():
        print(f"Output file not found: {output_path}")
        print("Please run 'smva extract' first to generate output data.")
        return

    try:
        data = load_output_data(output_path)
        print(f"Loaded data from: {output_path}")
        print(f"Video: {data.get('video', 'Unknown')}")
        print(f"Total data points: {len(data['data'])}")

        # Plot graphs
        plot_output_path = Path("result/graph.png")
        plot_graphs(data, plot_output_path)

        print("\nPlot completed successfully!")
    except Exception as e:
        print(f"Error plotting graphs: {e}")
        raise

