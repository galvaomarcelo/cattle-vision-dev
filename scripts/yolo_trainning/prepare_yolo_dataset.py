"""
Prepare the Cattle-Vision YOLO dataset.

This script converts the CVAT YOLO annotations into the directory
structure expected by Ultralytics YOLO.

Main responsibilities
---------------------

1. Read the cleaned image metadata.
2. Match source images with CVAT YOLO Detection 1.0 annotation files.
3. Split images by flight_group, never splitting a group between
   training and validation.
4. Copy images and labels into the YOLO directory structure.
5. Create empty label files for known negative images.
6. Validate that no unexpected annotations are missing.
7. Generate data.yaml.
8. Print a detailed dataset summary.

Dataset strategy
----------------

The validation groups are explicitly defined below.

Validation groups:
    7, 12, 13, 14

All other groups are assigned to training.

This fixed split makes experiments reproducible and avoids data
leakage between visually similar images from the same flight/group.
"""

from pathlib import Path
import csv
import shutil


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

IMAGE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "images"
)

METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "dataset_clean.csv"
)

ANNOTATION_DIR = (
    PROJECT_ROOT
    / "data"
    / "annotations"
    / "cattle_yolo"
    / "labels"
    / "Train"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "yolo"
    / "cattle"
)

TRAIN_IMAGE_DIR = (
    OUTPUT_DIR
    / "images"
    / "train"
)

VAL_IMAGE_DIR = (
    OUTPUT_DIR
    / "images"
    / "val"
)

TRAIN_LABEL_DIR = (
    OUTPUT_DIR
    / "labels"
    / "train"
)

VAL_LABEL_DIR = (
    OUTPUT_DIR
    / "labels"
    / "val"
)

DATA_YAML = OUTPUT_DIR / "data.yaml"


# ============================================================================
# DATASET SPLIT
# ============================================================================

# Groups assigned to validation.
#
# All other groups are assigned to training.

VALIDATION_GROUPS = {
    7,
    12,
    13,
    14,
}


# ============================================================================
# KNOWN NEGATIVE IMAGES
# ============================================================================

# These images intentionally contain no cattle.
#
# They therefore do not have a CVAT annotation file.
#
# The preparation script will create an empty YOLO label file for them.

KNOWN_NEGATIVE_IMAGES = {
    "DJI_20260904180007_0024_D",
}


# ============================================================================
# HELPERS
# ============================================================================

def load_metadata():
    """
    Load dataset_clean.csv.

    Returns
    -------
    dict
        Dictionary indexed by image filename stem.
    """

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata file not found:\n{METADATA_FILE}"
        )

    with METADATA_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(
                "Metadata CSV has no header."
            )

        rows = list(reader)

    metadata = {}

    for row in rows:

        filename = row.get(
            "FileName",
            "",
        ).strip()

        if not filename:
            continue

        stem = Path(filename).stem

        metadata[stem] = row

    return metadata


def get_group(row):
    """
    Return the flight group as an integer.

    Raises an error if flight_group is missing or invalid.
    """

    value = row.get(
        "flight_group",
        "",
    ).strip()

    if not value:
        raise ValueError(
            f"Missing flight_group for {row.get('FileName')}"
        )

    try:
        return int(float(value))

    except ValueError:
        raise ValueError(
            f"Invalid flight_group '{value}' "
            f"for {row.get('FileName')}"
        )


def clean_output_directory():
    """
    Remove the previous generated YOLO dataset.

    This is intentional because the YOLO directory is a generated
    dataset and should always be reproducible from the source data.
    """

    if OUTPUT_DIR.exists():

        print()
        print("Removing previous generated dataset...")

        shutil.rmtree(
            OUTPUT_DIR
        )


def create_directories():
    """
    Create YOLO train/validation directories.
    """

    TRAIN_IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    VAL_IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TRAIN_LABEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    VAL_LABEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def find_source_image(stem):
    """
    Find the source image using its filename stem.

    Supports JPG/JPEG variants and different capitalization.
    """

    extensions = {
        ".jpg",
        ".jpeg",
        ".JPG",
        ".JPEG",
    }

    matches = [
        path
        for path in IMAGE_DIR.iterdir()
        if path.is_file()
        and path.stem == stem
        and path.suffix in extensions
    ]

    if not matches:
        return None

    if len(matches) > 1:
        raise ValueError(
            f"Multiple images found for {stem}: "
            f"{matches}"
        )

    return matches[0]


def count_annotations(label_file):
    """
    Count YOLO annotations in a label file.

    Empty label files represent negative images.
    """

    if not label_file.exists():
        return 0

    with label_file.open(
        "r",
        encoding="utf-8",
    ) as file:

        lines = [
            line.strip()
            for line in file
            if line.strip()
        ]

    return len(lines)


def copy_example(
    stem,
    row,
    split,
):
    """
    Copy one image and its annotation into the selected split.

    Returns
    -------
    int
        Number of cattle annotations.
    """

    source_image = find_source_image(
        stem
    )

    if source_image is None:
        raise FileNotFoundError(
            f"Image not found:\n{stem}"
        )

    source_label = (
        ANNOTATION_DIR
        / f"{stem}.txt"
    )

    # ---------------------------------------------------------------
    # Destination directories
    # ---------------------------------------------------------------

    if split == "train":

        image_destination = (
            TRAIN_IMAGE_DIR
            / source_image.name
        )

        label_destination = (
            TRAIN_LABEL_DIR
            / f"{stem}.txt"
        )

    else:

        image_destination = (
            VAL_IMAGE_DIR
            / source_image.name
        )

        label_destination = (
            VAL_LABEL_DIR
            / f"{stem}.txt"
        )

    # ---------------------------------------------------------------
    # Annotation handling
    # ---------------------------------------------------------------

    if source_label.exists():

        annotation_count = count_annotations(
            source_label
        )

        shutil.copy2(
            source_label,
            label_destination,
        )

    elif stem in KNOWN_NEGATIVE_IMAGES:

        # A genuine negative image.
        #
        # YOLO expects a corresponding label file, but the file
        # contains no annotation lines.

        label_destination.write_text(
            "",
            encoding="utf-8",
        )

        annotation_count = 0

    else:

        raise FileNotFoundError(
            f"Missing annotation for image:\n"
            f"{stem}\n\n"
            f"This image is not listed as a known negative."
        )

    # ---------------------------------------------------------------
    # Copy image
    # ---------------------------------------------------------------

    shutil.copy2(
        source_image,
        image_destination,
    )

    return annotation_count


# ============================================================================
# WRITE DATA.YAML
# ============================================================================

def write_data_yaml():

    content = f"""path: {OUTPUT_DIR.as_posix()}
train: images/train
val: images/val

names:
  0: cattle
"""

    DATA_YAML.write_text(
        content,
        encoding="utf-8",
    )


# ============================================================================
# MAIN
# ============================================================================

def main():

    print("=" * 70)
    print("CATTLE-VISION - PREPARE YOLO DATASET")
    print("=" * 70)

    print()
    print(f"Images      : {IMAGE_DIR}")
    print(f"Metadata    : {METADATA_FILE}")
    print(f"Annotations : {ANNOTATION_DIR}")
    print(f"Output      : {OUTPUT_DIR}")

    # ------------------------------------------------------------------------
    # Load metadata
    # ------------------------------------------------------------------------

    metadata = load_metadata()

    print()
    print(
        f"Metadata images: {len(metadata)}"
    )

    # ------------------------------------------------------------------------
    # Validate validation groups
    # ------------------------------------------------------------------------

    available_groups = {
        get_group(row)
        for row in metadata.values()
    }

    missing_groups = (
        VALIDATION_GROUPS
        - available_groups
    )

    if missing_groups:

        raise ValueError(
            "Validation groups not found in metadata: "
            f"{sorted(missing_groups)}"
        )

    # ------------------------------------------------------------------------
    # Clean generated dataset
    # ------------------------------------------------------------------------

    clean_output_directory()

    create_directories()

    # ------------------------------------------------------------------------
    # Sort images by group and filename
    # ------------------------------------------------------------------------

    examples = []

    for stem, row in metadata.items():

        group = get_group(row)

        if group in VALIDATION_GROUPS:
            split = "val"
        else:
            split = "train"

        examples.append(
            (
                group,
                stem,
                row,
                split,
            )
        )

    examples.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    # ------------------------------------------------------------------------
    # Process images
    # ------------------------------------------------------------------------

    train_examples = []
    val_examples = []

    train_instances = 0
    val_instances = 0

    for (
        group,
        stem,
        row,
        split,
    ) in examples:

        annotation_count = copy_example(
            stem,
            row,
            split,
        )

        record = {
            "group": group,
            "stem": stem,
            "file": row.get(
                "FileName",
                "",
            ),
            "annotations": annotation_count,
        }

        if split == "train":

            train_examples.append(
                record
            )

            train_instances += (
                annotation_count
            )

        else:

            val_examples.append(
                record
            )

            val_instances += (
                annotation_count
            )

    # ------------------------------------------------------------------------
    # Print split
    # ------------------------------------------------------------------------

    print()
    print("VALIDATION GROUPS")
    print("-" * 70)

    for group in sorted(
        VALIDATION_GROUPS
    ):
        print(
            f"  {group}"
        )

    print()
    print("TRAIN")
    print("-" * 70)

    for item in train_examples:

        print(
            f"  Group {item['group']:>2}  "
            f"{item['stem']}  "
            f"({item['annotations']} cattle)"
        )

    print()
    print("VALIDATION")
    print("-" * 70)

    for item in val_examples:

        print(
            f"  Group {item['group']:>2}  "
            f"{item['stem']}  "
            f"({item['annotations']} cattle)"
        )

    # ------------------------------------------------------------------------
    # Write YAML
    # ------------------------------------------------------------------------

    write_data_yaml()

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    train_negative = sum(
        1
        for item in train_examples
        if item["annotations"] == 0
    )

    val_negative = sum(
        1
        for item in val_examples
        if item["annotations"] == 0
    )

    print()
    print("=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)

    print()
    print(
        f"Training images     : {len(train_examples)}"
    )

    print(
        f"Training cattle     : {train_instances}"
    )

    print(
        f"Training negatives  : {train_negative}"
    )

    print()
    print(
        f"Validation images   : {len(val_examples)}"
    )

    print(
        f"Validation cattle   : {val_instances}"
    )

    print(
        f"Validation negatives: {val_negative}"
    )

    print()
    print(
        f"Total images        : "
        f"{len(train_examples) + len(val_examples)}"
    )

    print(
        f"Total cattle        : "
        f"{train_instances + val_instances}"
    )

    print()
    print(
        f"Dataset: {OUTPUT_DIR}"
    )

    print(
        f"Config : {DATA_YAML}"
    )

    print()
    print("=" * 70)
    print("Dataset prepared successfully.")
    print("=" * 70)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()