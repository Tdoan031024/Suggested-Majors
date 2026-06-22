"""Runtime paths shared by source and packaged executions."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Return the project root or the PyInstaller executable directory."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def model_path(filename: str) -> Path:
    return project_root() / "models" / filename


def data_path(filename: str = "DXDuong.xlsx") -> Path:
    return project_root() / "data" / filename
