# User Guide

## Installation

1. Install Python 3.11 or higher
2. Install Tesseract OCR:
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
3. Install project dependencies:
   ```bash
   pip install -e .
   ```

## Usage

### 1. Setup ROI

Run the ROI selection tool:

```bash
smva setup-roi
```

1. A file dialog will open - select your video file
2. The tool will extract 5 preview frames
3. A window will open showing the first preview frame
4. Click and drag to draw a rectangle around the data block
5. The rectangle should include all 4 lines:
   - ACTUAL CURRENT
   - MPS VOLTS
   - MAG VOLTS
   - Elapsed Time
6. Press SPACE to confirm, ESC to cancel
7. ROI configuration will be saved to `config/roi.yaml`

### 2. Test OCR

Run the test OCR processing:

```bash
smva test-ocr
```

1. A file dialog will open - select your video file
2. The tool will load ROI from `config/roi.yaml`
3. 5 evenly spaced test frames will be processed:
   - ROI region is cropped
   - OCR extracts text
   - Four values are parsed
4. Results are displayed in a table for verification
5. Test frame images are saved to `result/test_frames/`

### 3. Extract Data

Run the full video processing:

```bash
smva extract
```

1. A file dialog will open - select your video file
2. The tool will load ROI from `config/roi.yaml`
3. Every 10th frame will be processed:
   - ROI region is cropped
   - OCR extracts text
   - Four values are parsed
   - If OCR fails, neighboring frames are tried automatically
   - Frames with current > 550A are skipped
4. Results are saved to `result/output.json`

### 4. Plot Graphs

Create visualization graphs:

```bash
smva plot
```

1. Loads data from `result/output.json`
2. Creates a graph with dual Y-axes:
   - Left axis (red): Current (A)
   - Right axis: Voltages (MPS - cyan, MAG - purple)
3. Saves graph to `result/graph.png`
4. Displays the graph

## Output Format

The output JSON contains:

```json
{
  "video": "Avanto Fit Ramp.mp4",
  "fps": 30,
  "data": [
    {
      "frame": 14880,
      "time_sec": 496.0,
      "current_A": 349.8,
      "mps_V": 1.766,
      "mag_V": 0.808,
      "time": "00:29:04"
    }
  ]
}
```

## Troubleshooting

### OCR Not Working

- Ensure Tesseract OCR is installed and in PATH
- Check that ROI includes all text clearly
- Try adjusting ROI selection if text is cut off

### No Data Extracted

- Verify ROI selection includes all 4 data lines
- Check that video quality is sufficient for OCR
- Ensure text is clearly visible in the selected region

### Frames Skipped

- Frames with current_A > 550 are automatically skipped
- This is expected behavior for the ramp video analysis

