"""
Train a YOLO object detection model for Cattle-Vision.

Main responsibilities
---------------------

1. Load the prepared YOLO dataset.
2. Load a pretrained YOLO11 model.
3. Train the model on the Cattle-Vision training images.
4. Validate the model after training.
5. Save the training results and best model weights.

This is the first baseline experiment.

The dataset currently contains:
    - 22 training images
    - 8 validation images
    - 1,071 cattle annotations in total
    - 1 negative image

The model currently detects only one class:
    cattle
"""


from pathlib import Path

from ultralytics import YOLO


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# Prepared YOLO dataset
DATASET_DIR = (
    PROJECT_ROOT
    / "data"
    / "yolo"
    / "cattle"
)


DATA_YAML = (
    DATASET_DIR
    / "data.yaml"
)


# ============================================================================
# MODEL
# ============================================================================

# YOLO11 Nano.
#
# The ".pt" file is a pretrained model.
#
# Ultralytics will download it automatically the first time
# it is used if it is not already available locally.

MODEL_NAME = "yolo11n.pt"


# ============================================================================
# TRAINING PARAMETERS
# ============================================================================

# Number of complete passes through the training dataset.

EPOCHS = 30


# Image size used by the model during training.
#
# Our original drone images are 4096 x 3072.
#
# 640 is a reasonable baseline and keeps CPU training
# somewhat manageable.

IMAGE_SIZE = 1280


# Number of images processed together during one training step.
#
# The current computer has no NVIDIA GPU and only ~8 GB RAM,
# so we use a conservative value.

BATCH_SIZE = 4


# Number of CPU workers used to load images.
#
# Keep this small on the current machine.

WORKERS = 2


# Name of this experiment.

RUN_NAME = "cattle_baseline_yolo11n_1280"


# Directory where Ultralytics stores training runs.

RUNS_DIR = (
    PROJECT_ROOT
    / "runs"
    / "detect"
)


# ============================================================================
# TRAINING
# ============================================================================

def train():

    print("=" * 70)
    print("CATTLE-VISION - YOLO TRAINING")
    print("=" * 70)

    print()
    print(f"Dataset : {DATASET_DIR}")
    print(f"Config  : {DATA_YAML}")
    print(f"Model   : {MODEL_NAME}")
    print(f"Epochs  : {EPOCHS}")
    print(f"Image   : {IMAGE_SIZE}")
    print(f"Batch   : {BATCH_SIZE}")
    print(f"Workers : {WORKERS}")
    print(f"Run     : {RUN_NAME}")

    print()
    print("-" * 70)
    print("Loading pretrained model...")
    print("-" * 70)

    model = YOLO(
        MODEL_NAME
    )

    print()
    print("-" * 70)
    print("Starting training...")
    print("-" * 70)

    results = model.train(

        # Dataset
        data=str(
            DATA_YAML
        ),

        # Training parameters
        epochs=EPOCHS,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        workers=WORKERS,

        # Output
        project=str(
            RUNS_DIR
        ),
        name=RUN_NAME,

        # Reproducibility
        seed=42,

        # Save the best model
        save=True,

        # Validate during training
        val=True,

        # Use pretrained weights
        pretrained=True,
    )

    return model, results


# ============================================================================
# VALIDATION
# ============================================================================

def validate(model):

    print()
    print("=" * 70)
    print("VALIDATING BEST MODEL")
    print("=" * 70)

    best_model_path = (
        RUNS_DIR
        / RUN_NAME
        / "weights"
        / "best.pt"
    )

    print()
    print(
        f"Best model: {best_model_path}"
    )

    if not best_model_path.exists():

        print()
        print(
            "WARNING: best.pt was not found."
        )

        return

    # Load the best checkpoint.

    best_model = YOLO(
        str(best_model_path)
    )

    # Run validation on the validation set.

    metrics = best_model.val(
        data=str(
            DATA_YAML
        ),
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
    )

    return metrics


# ============================================================================
# MAIN
# ============================================================================

def main():

    # ------------------------------------------------------------------------
    # Train
    # ------------------------------------------------------------------------

    model, results = train()

    # ------------------------------------------------------------------------
    # Validate best checkpoint
    # ------------------------------------------------------------------------

    validate(
        model
    )

    # ------------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------------

    best_model_path = (
        RUNS_DIR
        / RUN_NAME
        / "weights"
        / "best.pt"
    )

    print()
    print("=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Results : "
        f"{RUNS_DIR / RUN_NAME}"
    )

    print(
        f"Best model : "
        f"{best_model_path}"
    )

    print()
    print("=" * 70)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()