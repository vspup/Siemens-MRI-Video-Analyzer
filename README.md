# Siemens MRI Video Analyzer

Extract numerical MRI console data from Siemens MPS ramp videos by selecting a single ROI block and performing OCR inside it.

## Features

- **Setup ROI**: Interactive ROI selection tool for identifying the data block area
- **Test OCR**: Test OCR processing on 5 sample frames for verification
- **Extract**: Full video processing with frame sampling (every 10th frame) and fallback to neighboring frames
- **Plot**: Create graphs with dual Y-axes visualization
- Extracts four data values:
  - ACTUAL CURRENT (A)
  - MPS VOLTS (V)
  - MAG VOLTS (V)
  - Elapsed Time (hh:mm:ss)

## Installation

### 1. Create virtual environment

```bash
python -m venv .venv
```

### 2. Activate virtual environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Install Tesseract OCR

**Windows:**
- Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Default installation path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- The path is automatically configured in the code

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## Usage

### 1. Setup ROI

```bash
smva setup-roi
```

This will:
1. Open a file dialog to select a video
2. Extract 5 preview frames
3. Display a frame for manual ROI selection
4. Save ROI configuration to `config/roi.yaml`

### 2. Test OCR

```bash
smva test-ocr
```

This will:
1. Load ROI from `config/roi.yaml`
2. Extract 5 evenly spaced test frames
3. Process each frame with OCR
4. Display results in a table for verification
5. Save test frame images to `result/test_frames/`

### 3. Extract Data

```bash
smva extract
```

This will:
1. Load ROI from `config/roi.yaml`
2. Process every 10th frame for efficiency
3. If OCR fails on a frame, automatically try neighboring frames (±5 frames)
4. Extract and parse the four data values
5. Save results to `result/output.json`

### 4. Plot Graphs

```bash
smva plot
```

This will:
1. Load data from `result/output.json`
2. Create a graph with dual Y-axes:
   - **Left axis (red)**: Current (A)
   - **Right axis**: Voltages
     - **MPS Voltage (cyan)**: Blue line
     - **MAG Voltage (purple)**: Purple solid line
3. Save graph to `result/graph.png`
4. Display the graph

## Project Structure

```
Siemens-MRI-Video-Analyzer/
├── src/smva/          # Main package
├── config/            # Configuration files
├── raw_video/         # Input videos
├── result/            # Output files
└── docs/              # Documentation
```

## Requirements

- Python 3.11+
- Tesseract OCR (must be installed separately)

