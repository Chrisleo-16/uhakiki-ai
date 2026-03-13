#!/usr/bin/env python3
"""
Fixed version of model_training.py with corrected paths
"""

# Fix the path resolution
ROOT = Path(__file__).resolve().parent  # Correct: from /backend/ to project root
DATA_PATH = ROOT / "backend" / "data" / "training"
MODELS_PATH = ROOT / "backend" / "models"
FORENSICS = ROOT / "backend" / "data" / "forensics" / "original"

# Fix the import path
sys.path.insert(0, str(ROOT / "backend"))
from app.logic.rad_model import RADAutoencoder
