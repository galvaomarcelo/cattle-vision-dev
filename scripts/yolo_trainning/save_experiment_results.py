"""
Save YOLO experiment results to a CSV log.

The script creates the CSV if it does not exist and appends a new
experiment result if it already exists.

RUN AFTER predict_yolo_validation!!!!!

Usage:
    python scripts/save_experiment_results.py
"""

from pathlib import Path
import csv


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "inspection"
    / "yolo_experiment_results.csv"
)


# ---------------------------------------------------------------------
# Experiment result
# ---------------------------------------------------------------------

RESULT = {
    "experiment": "baseline_640",
    "model": "yolo11n",
    "image_size": 640,
    "epochs": 30,
    "batch_size": 4,

    # Official validation metrics
    "precision": 0.784,
    "recall": 0.292,
    "map50": 0.460,
    "map50_95": 0.167,

    # Inference threshold test
    "confidence": 0.10,
    "detections": 18,

    # Optional observations
    "false_positives": 2,
    "notes": "Many false negatives; few false positives",
}


# ---------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

fieldnames = list(RESULT.keys())

file_exists = OUTPUT_FILE.exists()

with OUTPUT_FILE.open("a", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    # Write the header only when creating the file.
    if not file_exists:
        writer.writeheader()

    writer.writerow(RESULT)


print("=" * 70)
print("EXPERIMENT RESULT SAVED")
print("=" * 70)
print(f"File: {OUTPUT_FILE}")
print(f"Experiment: {RESULT['experiment']}")
print(f"Image size: {RESULT['image_size']}")
print(f"Confidence: {RESULT['confidence']}")
print(f"Detections: {RESULT['detections']}")
print("=" * 70)

