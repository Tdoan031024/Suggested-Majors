"""Shared paths for offline training and evaluation."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "DXDuong.xlsx"
MODEL_DIR = PROJECT_ROOT / "models"
EVALUATION_DIR = Path(__file__).resolve().parent / "evaluation"
