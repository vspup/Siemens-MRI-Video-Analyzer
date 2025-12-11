"""Analyze: Interactive analysis of cleaned data with dynamic axis limits."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import matplotlib.pyplot as plt
from matplotlib.widgets import RangeSlider, Button, TextBox
import numpy as np


def load_cleaned_data(cleaned_path: Path) -> Dict[str, Any]:
    """
    Load cleaned data from JSON file.

    Args:
        cleaned_path: Path to cleaned JSON file

    Returns:
        Dictionary with cleaned video data
    """
    if not cleaned_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_path}")

    with open(cleaned_path, "r") as f:
        data = json.load(f)

    if "data" not in data:
        raise ValueError("Invalid cleaned data file format: missing 'data' key")

    return data


def plot_interactive(data: Dict[str, Any]) -> None:
    """
    Create interactive plot with dynamic axis limits.

    Args:
        data: Dictionary with cleaned video data
    """
    video_data = data["data"]

    if not video_data:
        raise ValueError("No data to plot")

    # Extract data
    time_sec = np.array([item["time_sec"] for item in video_data])
    current_a = np.array([item["current_A"] for item in video_data])
    mps_v = np.array([item["mps_V"] for item in video_data])
    mag_v = np.array([item["mag_V"] for item in video_data])
    
    # Downsample data for faster rendering if there are too many points
    # Keep every Nth point for display
    max_display_points = 1000
    if len(time_sec) > max_display_points:
        downsample_factor = len(time_sec) // max_display_points
        display_indices = np.arange(0, len(time_sec), downsample_factor)
        time_sec_display = time_sec[display_indices]
        current_a_display = current_a[display_indices]
        mps_v_display = mps_v[display_indices]
        mag_v_display = mag_v[display_indices]
        print(f"Displaying {len(time_sec_display)} of {len(time_sec)} points for performance")
    else:
        time_sec_display = time_sec
        current_a_display = current_a
        mps_v_display = mps_v
        mag_v_display = mag_v

    # Calculate initial axis limits
    time_min, time_max = time_sec.min(), time_sec.max()
    current_min, current_max = current_a.min(), current_a.max()
    voltage_min = min(mps_v.min(), mag_v.min())
    voltage_max = max(mps_v.max(), mag_v.max())

    # Add some padding to limits
    time_padding = (time_max - time_min) * 0.05
    current_padding = (current_max - current_min) * 0.1
    voltage_padding = (voltage_max - voltage_min) * 0.1

    time_min -= time_padding
    time_max += time_padding
    current_min -= current_padding
    current_max += current_padding
    voltage_min -= voltage_padding
    voltage_max += voltage_padding

    # Create figure with space for sliders
    fig = plt.figure(figsize=(16, 10))
    
    # Main plot area (centered with space for sliders on all sides)
    # [left, bottom, width, height]
    ax_plot = plt.axes([0.15, 0.15, 0.65, 0.7])
    
    # Create twin axis for voltages
    ax_voltage = ax_plot.twinx()

    # Plot data
    color_current = "red"
    color_mps = "cyan"
    color_mag = "purple"

    ax_plot.set_xlabel("Time (seconds)", fontsize=12)
    ax_plot.set_ylabel("Current (A)", color=color_current, fontsize=12)
    line1, = ax_plot.plot(
        time_sec_display, current_a_display, color=color_current, linewidth=1.2,
        marker='o', markersize=2, markerfacecolor=color_current, 
        markeredgewidth=0, alpha=0.8, antialiased=True
    )
    ax_plot.tick_params(axis="y", labelcolor=color_current)
    ax_plot.grid(True, alpha=0.3)

    ax_voltage.set_ylabel("Voltage (V)", fontsize=12)
    line2, = ax_voltage.plot(
        time_sec_display, mps_v_display, color=color_mps, linewidth=1.2,
        marker='s', markersize=2, markerfacecolor=color_mps, 
        markeredgewidth=0, alpha=0.8, antialiased=True
    )
    line3, = ax_voltage.plot(
        time_sec_display, mag_v_display, color=color_mag, linewidth=1.2,
        marker='^', markersize=2, markerfacecolor=color_mag, 
        markeredgewidth=0, alpha=0.8, antialiased=True
    )

    # Title
    video_name = data.get("video", "Unknown")
    ax_plot.set_title(f"MRI Ramp Data Analysis: {video_name}", fontsize=14, fontweight="bold")

    # Set initial limits
    ax_plot.set_xlim(time_min, time_max)
    ax_plot.set_ylim(current_min, current_max)
    ax_voltage.set_ylim(voltage_min, voltage_max)

    # Create range sliders for axis limits positioned near their respective axes
    
    # === TIME AXIS RANGE SLIDER (below X-axis) ===
    slider_width_horizontal = 0.65
    slider_height_horizontal = 0.03
    slider_left_horizontal = 0.15
    textbox_width = 0.06
    textbox_height = 0.025
    
    # Time slider
    ax_time_range = plt.axes([slider_left_horizontal, 0.06, slider_width_horizontal, slider_height_horizontal])
    
    slider_time = RangeSlider(
        ax_time_range, 'Time (s)', 
        time_sec.min() - time_padding * 2, 
        time_sec.max() + time_padding * 2,
        valinit=(time_min, time_max),
        valstep=(time_max - time_min) / 100,
        color='steelblue'
    )
    
    # Time textboxes (min and max)
    ax_time_min_text = plt.axes([slider_left_horizontal, 0.02, textbox_width, textbox_height])
    ax_time_max_text = plt.axes([slider_left_horizontal + slider_width_horizontal - textbox_width, 0.02, textbox_width, textbox_height])
    
    textbox_time_min = TextBox(ax_time_min_text, '', initial=f"{time_min:.1f}", textalignment='center')
    textbox_time_max = TextBox(ax_time_max_text, '', initial=f"{time_max:.1f}", textalignment='center')

    # === CURRENT AXIS RANGE SLIDER (left side, vertical) ===
    slider_width_vertical = 0.025
    slider_height_vertical = 0.3
    slider_bottom_left = 0.15
    textbox_width_vert = 0.045
    textbox_height_vert = 0.03
    
    # Current slider
    ax_current_range = plt.axes([0.04, slider_bottom_left, slider_width_vertical, slider_height_vertical])
    
    slider_current = RangeSlider(
        ax_current_range, 'Current\n(A)',
        current_a.min() - current_padding * 2, 
        current_a.max() + current_padding * 2,
        valinit=(current_min, current_max),
        valstep=(current_max - current_min) / 100,
        orientation='vertical',
        color=color_current
    )
    
    # Current textboxes (min at bottom, max at top)
    ax_current_min_text = plt.axes([0.015, slider_bottom_left - 0.04, textbox_width_vert, textbox_height_vert])
    ax_current_max_text = plt.axes([0.015, slider_bottom_left + slider_height_vertical + 0.01, textbox_width_vert, textbox_height_vert])
    
    textbox_current_min = TextBox(ax_current_min_text, '', initial=f"{current_min:.1f}", textalignment='center')
    textbox_current_max = TextBox(ax_current_max_text, '', initial=f"{current_max:.1f}", textalignment='center')

    # === VOLTAGE AXIS RANGE SLIDER (right side, vertical) ===
    slider_left_right = 0.83
    
    # Voltage slider
    ax_voltage_range = plt.axes([slider_left_right, slider_bottom_left, slider_width_vertical, slider_height_vertical])
    
    voltage_range = voltage_max - voltage_min
    slider_voltage = RangeSlider(
        ax_voltage_range, 'Voltage\n(V)',
        min(mps_v.min(), mag_v.min()) - voltage_padding * 2,
        max(mps_v.max(), mag_v.max()) + voltage_padding * 2,
        valinit=(voltage_min, voltage_max),
        valstep=voltage_range / 100 if voltage_range > 0 else 0.01,
        orientation='vertical',
        color='mediumorchid'
    )
    
    # Voltage textboxes (min at bottom, max at top)
    ax_voltage_min_text = plt.axes([slider_left_right + 0.035, slider_bottom_left - 0.04, textbox_width_vert, textbox_height_vert])
    ax_voltage_max_text = plt.axes([slider_left_right + 0.035, slider_bottom_left + slider_height_vertical + 0.01, textbox_width_vert, textbox_height_vert])
    
    textbox_voltage_min = TextBox(ax_voltage_min_text, '', initial=f"{voltage_min:.2f}", textalignment='center')
    textbox_voltage_max = TextBox(ax_voltage_max_text, '', initial=f"{voltage_max:.2f}", textalignment='center')

    # Reset button (bottom left corner)
    ax_reset = plt.axes([0.02, 0.90, 0.08, 0.04])
    btn_reset = Button(ax_reset, 'Reset', color='lightgray', hovercolor='gray')

    # Flag to prevent recursive updates of textboxes
    updating_textboxes = {'flag': False}
    
    # Update function for sliders
    def update_from_slider(val):
        time_range = slider_time.val
        current_range = slider_current.val
        voltage_range = slider_voltage.val
        
        # Update plot limits (fast operation)
        ax_plot.set_xlim(time_range[0], time_range[1])
        ax_plot.set_ylim(current_range[0], current_range[1])
        ax_voltage.set_ylim(voltage_range[0], voltage_range[1])
        
        # Update textboxes without triggering their callbacks
        if not updating_textboxes['flag']:
            updating_textboxes['flag'] = True
            textbox_time_min.set_val(f"{time_range[0]:.1f}")
            textbox_time_max.set_val(f"{time_range[1]:.1f}")
            textbox_current_min.set_val(f"{current_range[0]:.1f}")
            textbox_current_max.set_val(f"{current_range[1]:.1f}")
            textbox_voltage_min.set_val(f"{voltage_range[0]:.2f}")
            textbox_voltage_max.set_val(f"{voltage_range[1]:.2f}")
            updating_textboxes['flag'] = False
        
        # Redraw only what's needed
        ax_plot.figure.canvas.draw_idle()

    # Update functions for textboxes
    def update_time_min(text):
        if updating_textboxes['flag']:
            return
        try:
            val = float(text)
            current_range = slider_time.val
            if val < current_range[1]:
                slider_time.set_val((val, current_range[1]))
        except ValueError:
            pass
    
    def update_time_max(text):
        if updating_textboxes['flag']:
            return
        try:
            val = float(text)
            current_range = slider_time.val
            if val > current_range[0]:
                slider_time.set_val((current_range[0], val))
        except ValueError:
            pass
    
    def update_current_min(text):
        if updating_textboxes['flag']:
            return
        try:
            val = float(text)
            current_range = slider_current.val
            if val < current_range[1]:
                slider_current.set_val((val, current_range[1]))
        except ValueError:
            pass
    
    def update_current_max(text):
        if updating_textboxes['flag']:
            return
        try:
            val = float(text)
            current_range = slider_current.val
            if val > current_range[0]:
                slider_current.set_val((current_range[0], val))
        except ValueError:
            pass
    
    def update_voltage_min(text):
        if updating_textboxes['flag']:
            return
        try:
            val = float(text)
            current_range = slider_voltage.val
            if val < current_range[1]:
                slider_voltage.set_val((val, current_range[1]))
        except ValueError:
            pass
    
    def update_voltage_max(text):
        if updating_textboxes['flag']:
            return
        try:
            val = float(text)
            current_range = slider_voltage.val
            if val > current_range[0]:
                slider_voltage.set_val((current_range[0], val))
        except ValueError:
            pass

    # Reset function
    def reset(event):
        slider_time.reset()
        slider_current.reset()
        slider_voltage.reset()
        # Textboxes will be updated automatically by slider callbacks

    # Connect sliders to update function
    slider_time.on_changed(update_from_slider)
    slider_current.on_changed(update_from_slider)
    slider_voltage.on_changed(update_from_slider)
    
    # Connect textboxes to update functions
    textbox_time_min.on_submit(update_time_min)
    textbox_time_max.on_submit(update_time_max)
    textbox_current_min.on_submit(update_current_min)
    textbox_current_max.on_submit(update_current_max)
    textbox_voltage_min.on_submit(update_voltage_min)
    textbox_voltage_max.on_submit(update_voltage_max)
    
    # Connect reset button
    btn_reset.on_clicked(reset)

    # Display statistics (top of figure)
    if len(time_sec_display) < len(time_sec):
        stats_text = f"Data points: {len(video_data)} (displaying {len(time_sec_display)} for performance) | "
    else:
        stats_text = f"Data points: {len(video_data)} | "
    stats_text += f"Time range: {time_sec.min():.1f}-{time_sec.max():.1f}s | "
    stats_text += f"Current: {current_a.min():.1f}-{current_a.max():.1f}A | "
    stats_text += f"Voltage: {voltage_min:.2f}-{voltage_max:.2f}V"
    
    fig.text(0.5, 0.97, stats_text, ha='center', fontsize=9, style='italic')
    
    # Instructions
    instructions = "Грубая настройка: перемещайте бегунки слайдеров | Точная настройка: введите значения в текстовые поля (Enter) | 'Reset' - сброс"
    fig.text(0.5, 0.01, instructions, ha='center', fontsize=8, style='italic', color='gray')

    plt.show()


def run_analyze() -> None:
    """Run Analyze: Interactive analysis of cleaned data."""
    print("Analyze: Interactive Data Analysis")
    print("=" * 50)

    # Load cleaned data
    cleaned_path = Path("result/output_cleaned.json")
    if not cleaned_path.exists():
        print(f"Cleaned data file not found: {cleaned_path}")
        print("Please run 'smva plot' first to generate cleaned data.")
        return

    try:
        data = load_cleaned_data(cleaned_path)
        print(f"Loaded cleaned data from: {cleaned_path}")
        print(f"Video: {data.get('video', 'Unknown')}")
        print(f"Data points: {len(data['data'])}")
        print(f"\nOpening interactive plot...")
        print("Use sliders to adjust axis limits dynamically.")
        print("Click 'Reset' button to restore default limits.")

        # Create interactive plot
        plot_interactive(data)

        print("\nAnalysis completed!")
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

