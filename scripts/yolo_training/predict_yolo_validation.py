"""
Generate YOLO predictions for the Cattle-Vision validation dataset.

This script uses the best trained model and generates visual
predictions for all validation images.

The purpose is diagnostic:

    - Inspect missed cattle
    - Inspect false positives
    - Compare large and small cattle
    - Compare nadir and oblique images
    - Evaluate difficult/occluded animals visually

No training is performed here.
"""

from pathlib import Path

from ultralytics import YOLO


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Trained model
# ---------------------------------------------------------------------------

MODEL_PATH = (
    PROJECT_ROOT
    / "runs"
    / "detect"
    / "cattle_baseline_yolo11n_1280"
    / "weights"
    / "best.pt"
)


# ---------------------------------------------------------------------------
# Validation images
# ---------------------------------------------------------------------------

VALIDATION_IMAGES = (
    PROJECT_ROOT
    / "data"
    / "yolo"
    / "cattle"
    / "images"
    / "val"
)


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "inspection"
    / "yolo_predictions"
)


# ============================================================================
# PREDICTION PARAMETERS
# ============================================================================

# Image size used by YOLO during inference.

IMAGE_SIZE = 1280
# IMAGE_SIZE = 640


# Confidence threshold.
#
# A detection must have at least this confidence to be displayed.
#
# We use a relatively low value for inspection because we want to see
# what the model is attempting to detect, including uncertain detections.

CONFIDENCE = 0.20

# IoU threshold used by Non-Maximum Suppression (NMS).

IOU = 0.7

#Bounding box par

LINE_WIDTH = 16
FONT_SIZE = 60


# ============================================================================
# MAIN
# ============================================================================

def main():

    print("=" * 70)
    print("CATTLE-VISION - VALIDATION PREDICTIONS")
    print("=" * 70)

    # ------------------------------------------------------------------------
    # Check model
    # ------------------------------------------------------------------------

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Model not found:\n{MODEL_PATH}"
        )

    # ------------------------------------------------------------------------
    # Check validation images
    # ------------------------------------------------------------------------

    if not VALIDATION_IMAGES.exists():

        raise FileNotFoundError(
            f"Validation image directory not found:\n"
            f"{VALIDATION_IMAGES}"
        )

    images = sorted(
        [
            path
            for path in VALIDATION_IMAGES.iterdir()
            if path.suffix.lower()
            in {".jpg", ".jpeg", ".png"}
        ]
    )

    if not images:

        raise ValueError(
            "No validation images found."
        )

    # ------------------------------------------------------------------------
    # Prepare output directory
    # ------------------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ------------------------------------------------------------------------
    # Load model
    # ------------------------------------------------------------------------

    print()
    print("MODEL")
    print("-" * 70)

    print(
        f"Model: {MODEL_PATH}"
    )

    model = YOLO(
        str(MODEL_PATH)
    )

    # ------------------------------------------------------------------------
    # Dataset information
    # ------------------------------------------------------------------------

    print()
    print("VALIDATION DATASET")
    print("-" * 70)

    print(
        f"Images: {len(images)}"
    )

    print(
        f"Output: {OUTPUT_DIR}"
    )

    # ------------------------------------------------------------------------
    # Run prediction
    # ------------------------------------------------------------------------

    print()
    print("PREDICTIONS")
    print("-" * 70)

    total_detections = 0

    for index, image_path in enumerate(
        images,
        start=1
    ):

        print()
        print(
            f"[{index}/{len(images)}] "
            f"{image_path.name}"
        )

        results = model.predict(
            source=str(image_path),
            imgsz=IMAGE_SIZE,
            conf=CONFIDENCE,
            iou=IOU,

            save=True,
            project=str(OUTPUT_DIR),
            name="predictions",
            exist_ok=True,

            show_labels=False,
            show_conf=True,
            line_width=3,

            verbose=False,
        )

        result = results[0]

        detections = 0

        if result.boxes is not None:

            detections = len(
                result.boxes
            )

        total_detections += detections

        print(
            f"Detections: {detections}"
        )

    # ------------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------------

    print()
    print("=" * 70)
    print("PREDICTION COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Validation images : {len(images)}"
    )

    print(
        f"Total detections  : {total_detections}"
    )

    print()
    print(
        f"Results saved to:"
    )

    print(
        OUTPUT_DIR / "predictions"
    )

    print()
    print("=" * 70)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()