"""Command-line interface for SMVA."""

import click

from smva.setup_roi import run_setup_roi
from smva.test_ocr import run_test_ocr
from smva.extract import run_extract
from smva.plot import run_plot
from smva.analyze import run_analyze


@click.group()
def main():
    """Siemens MRI Video Analyzer - Extract data from MPS ramp videos."""
    pass


@main.command(name="setup-roi")
def setup_roi():
    """Setup ROI: Select region of interest from video preview."""
    run_setup_roi()


@main.command(name="test-ocr")
def test_ocr():
    """Test OCR: Test OCR processing on sample frames for verification."""
    run_test_ocr()


@main.command(name="extract")
def extract():
    """Extract: Process full video with frame sampling and extract data."""
    run_extract()


@main.command(name="plot")
def plot():
    """Plot: Create graphs from extracted data."""
    run_plot()


@main.command(name="analyze")
def analyze():
    """Analyze: Interactive analysis of cleaned data with dynamic axis limits."""
    run_analyze()


if __name__ == "__main__":
    main()

