# Architecture Overview

## Project Purpose

The Siemens MRI Video Analyzer extracts numerical MRI console data from Siemens MPS ramp videos by selecting a single ROI block and performing OCR inside it.

## Key Components

### ROI Block Structure

The ROI contains exactly four lines, always in this order:

1. **ACTUAL CURRENT** → value (A)
2. **MPS VOLTS** → value (V)
3. **MAG VOLTS** → value (V)
4. **Elapsed Time** → hh:mm:ss

The entire block appears on the right side of the full console screen.

### Processing Pipeline

#### Setup ROI (`setup-roi` command, `setup_roi.py`)

- Opens file dialog to select video
- Extracts video metadata (resolution, FPS, frame count)
- Extracts 5 evenly spaced preview frames
- Displays interactive ROI selector
- Saves ROI configuration to `config/roi.yaml`

#### Test OCR (`test-ocr` command, `test_ocr.py`)

- Loads ROI configuration from `config/roi.yaml`
- Extracts 5 evenly spaced test frames
- Processes each test frame:
  - Crops ROI region
  - Performs OCR on the cropped region
  - Parses four values in fixed order
- Displays results in a table for verification
- Saves test frame images to `result/test_frames/`

#### Extract Data (`extract` command, `extract.py`)

- Loads ROI configuration from `config/roi.yaml`
- Processes every 10th frame for efficiency:
  - Crops ROI region
  - Performs OCR on the cropped region
  - If OCR fails, tries neighboring frames (±5 frames)
  - Parses four values in fixed order
  - Converts time string to seconds
  - Skips frames where current_A > 550
- Saves results to `result/output.json`

#### Plot Graphs (`plot` command, `plot.py`)

- Loads data from `result/output.json`
- Creates graph with dual Y-axes:
  - Left axis (red): Current (A)
  - Right axis: Voltages (MPS - cyan, MAG - purple)
- Saves graph to `result/graph.png`
- Displays the graph

### Module Structure

- `setup_roi.py`: ROI selection tool
- `test_ocr.py`: Test OCR processing on sample frames
- `extract.py`: Full video processing with frame sampling and fallback
- `plot.py`: Graph plotting from extracted data
- `utils/video.py`: Video metadata and frame extraction utilities
- `utils/roi.py`: ROI configuration management
- `utils/ocr.py`: OCR processing and data parsing
- `cli.py`: Command-line interface with `setup-roi`, `test-ocr`, `extract`, and `plot` commands

### Data Flow

```
Video File → setup-roi → ROI Config (YAML)
                    ↓
Video File + ROI Config → test-ocr → Test Results (verification)
                    ↓
Video File + ROI Config → extract → Output JSON
                    ↓
Output JSON → plot → Graph PNG
```

