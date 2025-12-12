"""Analyze: Interactive analysis of cleaned data with dynamic axis limits."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
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
    # Use time_sec_precise if available, otherwise fall back to time_sec
    time_sec = np.array([
        item.get("time_sec_precise", item["time_sec"]) 
        for item in video_data
    ])
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

    # Create figure with space for text input fields
    fig = plt.figure(figsize=(16, 10))
    
    # Main plot area (more space since no sliders)
    # [left, bottom, width, height]
    ax_plot = plt.axes([0.12, 0.12, 0.75, 0.75])
    
    # Create twin axis for voltages
    ax_voltage = ax_plot.twinx()

    # Plot data
    color_current = "red"
    color_mps = "cyan"
    color_mag = "purple"

    ax_plot.set_xlabel("Time (seconds)", fontsize=12)
    ax_plot.set_ylabel("Current (A)", color=color_current, fontsize=12)
    line1, = ax_plot.plot(
        time_sec_display, current_a_display, color=color_current, linewidth=1.5,
        marker='o', markersize=4, markerfacecolor=color_current, 
        markeredgecolor='darkred', markeredgewidth=0.5, alpha=0.9, antialiased=True
    )
    ax_plot.tick_params(axis="y", labelcolor=color_current)
    ax_plot.grid(True, alpha=0.3)

    ax_voltage.set_ylabel("Voltage (V)", fontsize=12)
    line2, = ax_voltage.plot(
        time_sec_display, mps_v_display, color=color_mps, linewidth=1.5,
        marker='s', markersize=4, markerfacecolor=color_mps, 
        markeredgecolor='darkcyan', markeredgewidth=0.5, alpha=0.9, antialiased=True
    )
    line3, = ax_voltage.plot(
        time_sec_display, mag_v_display, color=color_mag, linewidth=1.5,
        marker='^', markersize=4, markerfacecolor=color_mag, 
        markeredgecolor='darkmagenta', markeredgewidth=0.5, alpha=0.9, antialiased=True
    )

    # Title
    video_name = data.get("video", "Unknown")
    ax_plot.set_title(f"MRI Ramp Data Analysis: {video_name}", fontsize=14, fontweight="bold")

    # Set initial limits
    ax_plot.set_xlim(time_min, time_max)
    ax_plot.set_ylim(current_min, current_max)
    ax_voltage.set_ylim(voltage_min, voltage_max)

    # Create text input fields for axis limits (no sliders for better performance)
    textbox_width = 0.08
    textbox_height = 0.035
    
    # Store current limits for reset
    initial_limits = {
        'time_min': time_min,
        'time_max': time_max,
        'current_min': current_min,
        'current_max': current_max,
        'voltage_min': voltage_min,
        'voltage_max': voltage_max
    }
    
    # === TIME AXIS TEXTBOXES (below X-axis, at bottom) ===
    ax_time_min_text = plt.axes([0.12, 0.02, textbox_width, textbox_height])
    ax_time_max_text = plt.axes([0.79 - textbox_width, 0.02, textbox_width, textbox_height])
    
    textbox_time_min = TextBox(ax_time_min_text, 'Time min (s)', initial=f"{time_min:.1f}", textalignment='center')
    textbox_time_max = TextBox(ax_time_max_text, 'Time max (s)', initial=f"{time_max:.1f}", textalignment='center')
    
    # === CURRENT AXIS TEXTBOXES (left side: min at bottom, max at top) ===
    ax_current_min_text = plt.axes([0.02, 0.12, textbox_width, textbox_height])
    ax_current_max_text = plt.axes([0.02, 0.87, textbox_width, textbox_height])
    
    textbox_current_min = TextBox(ax_current_min_text, 'Current min (A)', initial=f"{current_min:.1f}", textalignment='center')
    textbox_current_max = TextBox(ax_current_max_text, 'Current max (A)', initial=f"{current_max:.1f}", textalignment='center')
    
    # === VOLTAGE AXIS TEXTBOXES (right side: min at bottom, max at top) ===
    ax_voltage_min_text = plt.axes([0.90, 0.12, textbox_width, textbox_height])
    ax_voltage_max_text = plt.axes([0.90, 0.87, textbox_width, textbox_height])
    
    textbox_voltage_min = TextBox(ax_voltage_min_text, 'Voltage min (V)', initial=f"{voltage_min:.2f}", textalignment='center')
    textbox_voltage_max = TextBox(ax_voltage_max_text, 'Voltage max (V)', initial=f"{voltage_max:.2f}", textalignment='center')
    
    # Function to handle textbox clicks - move cursor to end for easier editing
    def on_textbox_click(event):
        """Handle textbox clicks - move cursor to end for easier text selection/editing."""
        if hasattr(event, 'inaxes') and event.inaxes:
            # Find which textbox was clicked
            for textbox in [textbox_time_min, textbox_time_max, 
                          textbox_current_min, textbox_current_max,
                          textbox_voltage_min, textbox_voltage_max]:
                if event.inaxes == textbox.ax:
                    # Get current text and move cursor to end
                    # This makes it easier to select all text manually (Ctrl+A or triple-click)
                    # or to append/overwrite the value
                    current_text = textbox.text_disp.get_text()
                    textbox.cursor_index = len(current_text)
                    textbox._rendercursor()
                    break
    
    # Connect click event for textbox interaction
    fig.canvas.mpl_connect('button_press_event', on_textbox_click)

    # Reset button (top left corner)
    ax_reset = plt.axes([0.02, 0.92, 0.08, 0.04])
    btn_reset = Button(ax_reset, 'Reset', color='lightgray', hovercolor='gray')

    # Update functions for textboxes (directly update plot limits)
    # All functions preserve decimal precision when updating
    def update_time_min(text):
        try:
            val = float(text)
            current_max = float(textbox_time_max.text_disp.get_text())
            if val < current_max:
                ax_plot.set_xlim(val, current_max)
                # Update textbox to show formatted value (preserves decimal if entered)
                textbox_time_min.set_val(f"{val:.1f}")
                ax_plot.figure.canvas.draw_idle()
            else:
                # Invalid range, restore previous value
                textbox_time_min.set_val(f"{ax_plot.get_xlim()[0]:.1f}")
        except ValueError:
            # Invalid input, restore previous value
            textbox_time_min.set_val(f"{ax_plot.get_xlim()[0]:.1f}")
    
    def update_time_max(text):
        try:
            val = float(text)
            current_min = float(textbox_time_min.text_disp.get_text())
            if val > current_min:
                ax_plot.set_xlim(current_min, val)
                # Update textbox to show formatted value (preserves decimal if entered)
                textbox_time_max.set_val(f"{val:.1f}")
                ax_plot.figure.canvas.draw_idle()
            else:
                # Invalid range, restore previous value
                textbox_time_max.set_val(f"{ax_plot.get_xlim()[1]:.1f}")
        except ValueError:
            # Invalid input, restore previous value
            textbox_time_max.set_val(f"{ax_plot.get_xlim()[1]:.1f}")
    
    def update_current_min(text):
        try:
            val = float(text)
            current_max = float(textbox_current_max.text_disp.get_text())
            if val < current_max:
                ax_plot.set_ylim(val, current_max)
                # Update textbox to show formatted value (preserves decimal if entered)
                textbox_current_min.set_val(f"{val:.1f}")
                ax_plot.figure.canvas.draw_idle()
            else:
                # Invalid range, restore previous value
                textbox_current_min.set_val(f"{ax_plot.get_ylim()[0]:.1f}")
        except ValueError:
            # Invalid input, restore previous value
            textbox_current_min.set_val(f"{ax_plot.get_ylim()[0]:.1f}")
    
    def update_current_max(text):
        try:
            val = float(text)
            current_min = float(textbox_current_min.text_disp.get_text())
            if val > current_min:
                ax_plot.set_ylim(current_min, val)
                # Update textbox to show formatted value (preserves decimal if entered)
                textbox_current_max.set_val(f"{val:.1f}")
                ax_plot.figure.canvas.draw_idle()
            else:
                # Invalid range, restore previous value
                textbox_current_max.set_val(f"{ax_plot.get_ylim()[1]:.1f}")
        except ValueError:
            # Invalid input, restore previous value
            textbox_current_max.set_val(f"{ax_plot.get_ylim()[1]:.1f}")
    
    def update_voltage_min(text):
        try:
            val = float(text)
            current_max = float(textbox_voltage_max.text_disp.get_text())
            if val < current_max:
                ax_voltage.set_ylim(val, current_max)
                # Update textbox to show formatted value (preserves decimal if entered)
                textbox_voltage_min.set_val(f"{val:.2f}")
                ax_plot.figure.canvas.draw_idle()
            else:
                # Invalid range, restore previous value
                textbox_voltage_min.set_val(f"{ax_voltage.get_ylim()[0]:.2f}")
        except ValueError:
            # Invalid input, restore previous value
            textbox_voltage_min.set_val(f"{ax_voltage.get_ylim()[0]:.2f}")
    
    def update_voltage_max(text):
        try:
            val = float(text)
            current_min = float(textbox_voltage_min.text_disp.get_text())
            if val > current_min:
                ax_voltage.set_ylim(current_min, val)
                # Update textbox to show formatted value (preserves decimal if entered)
                textbox_voltage_max.set_val(f"{val:.2f}")
                ax_plot.figure.canvas.draw_idle()
            else:
                # Invalid range, restore previous value
                textbox_voltage_max.set_val(f"{ax_voltage.get_ylim()[1]:.2f}")
        except ValueError:
            # Invalid input, restore previous value
            textbox_voltage_max.set_val(f"{ax_voltage.get_ylim()[1]:.2f}")

    # Reset function
    def reset(event):
        # Restore initial limits
        ax_plot.set_xlim(initial_limits['time_min'], initial_limits['time_max'])
        ax_plot.set_ylim(initial_limits['current_min'], initial_limits['current_max'])
        ax_voltage.set_ylim(initial_limits['voltage_min'], initial_limits['voltage_max'])
        
        # Update textboxes
        textbox_time_min.set_val(f"{initial_limits['time_min']:.1f}")
        textbox_time_max.set_val(f"{initial_limits['time_max']:.1f}")
        textbox_current_min.set_val(f"{initial_limits['current_min']:.1f}")
        textbox_current_max.set_val(f"{initial_limits['current_max']:.1f}")
        textbox_voltage_min.set_val(f"{initial_limits['voltage_min']:.2f}")
        textbox_voltage_max.set_val(f"{initial_limits['voltage_max']:.2f}")
        
        ax_plot.figure.canvas.draw_idle()
    
    # Connect textboxes to update functions
    textbox_time_min.on_submit(update_time_min)
    textbox_time_max.on_submit(update_time_max)
    textbox_current_min.on_submit(update_current_min)
    textbox_current_max.on_submit(update_current_max)
    textbox_voltage_min.on_submit(update_voltage_min)
    textbox_voltage_max.on_submit(update_voltage_max)
    
    # Connect reset button
    btn_reset.on_clicked(reset)
    
    # Helper function to select all text on double-click or focus
    def make_textbox_selectable(textbox):
        """Make textbox select all text on focus."""
        def on_click(event):
            if event.inaxes == textbox.ax:
                # Clear and let user type (matplotlib TextBox doesn't support selection well)
                # User can double-click to select all manually
                pass
        return on_click
    
    # Note: matplotlib TextBox doesn't support text selection well
    # Users can double-click to select all text manually

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
    instructions = "Введите значения в текстовые поля и нажмите Enter для обновления графика | Ctrl+A или тройной клик для выделения всего текста | 'Reset' - сброс к начальным значениям"
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
        print("Enter values in text fields and press Enter to update axis limits.")
        print("Use Ctrl+A or triple-click to select all text in a field.")
        print("Click 'Reset' button to restore default limits.")

        # Create interactive plot
        plot_interactive(data)

        print("\nAnalysis completed!")
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

