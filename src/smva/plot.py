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

    # Extract data
    time_sec = [item["time_sec"] for item in video_data]
    current_a = [item["current_A"] for item in video_data]
    mps_v = [item["mps_V"] for item in video_data]
    mag_v = [item["mag_V"] for item in video_data]

    # Create figure and axes
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Left axis for current (red)
    color_current = "red"
    ax1.set_xlabel("Time (seconds)", fontsize=12)
    ax1.set_ylabel("Current (A)", color=color_current, fontsize=12)
    line1 = ax1.plot(
        time_sec, current_a, color=color_current, linewidth=1.5, label="Current (A)"
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
        label="MPS Voltage (V)",
    )
    line3 = ax2.plot(
        time_sec,
        mag_v,
        color=color_mag,
        linewidth=1.5,
        linestyle="-",
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

