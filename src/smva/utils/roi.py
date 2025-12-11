"""ROI selection and management utilities."""

import yaml
from pathlib import Path
from typing import Dict, Any


def save_roi_config(
    config_path: Path,
    roi: Dict[str, int],
    video_metadata: Dict[str, Any],
) -> None:
    """
    Save ROI configuration to YAML file.

    Args:
        config_path: Path to config file
        roi: ROI dictionary with x, y, w, h
        video_metadata: Video metadata with width, height, fps
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "roi": roi,
        "video": video_metadata,
    }

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def load_roi_config(config_path: Path) -> Dict[str, Any]:
    """
    Load ROI configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary with roi and video keys
    """
    if not config_path.exists():
        raise FileNotFoundError(f"ROI config not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if "roi" not in config or "video" not in config:
        raise ValueError("Invalid ROI config format")

    return config

