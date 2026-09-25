"""
Cattle-Vision - Extract Image Metadata

Extracts EXIF/XMP metadata from all supported images using ExifTool
and creates the raw metadata files used by the rest of the pipeline.

Main functions:
    find_images()      Find supported image files recursively.
    extract_metadata() Extract metadata from one image using ExifTool.
    process_images()   Extract metadata from all images and add project fields.
    main()             Run the complete metadata extraction pipeline.

Outputs:
    data/metadata/images_metadata.json
    data/metadata/images_metadata.csv

The generated files are RAW metadata and must not be modified by later
processing steps.
"""

from pathlib import Path
import json
import subprocess

from utils import write_csv, write_json


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "images"
OUTPUT_DIR = PROJECT_ROOT / "data" / "metadata"

OUTPUT_JSON = OUTPUT_DIR / "images_metadata.json"
OUTPUT_CSV = OUTPUT_DIR / "images_metadata.csv"


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".dng",
    ".tif",
    ".tiff",
}


# ---------------------------------------------------------------------
# Image discovery
# ---------------------------------------------------------------------

def find_images(image_dir: Path) -> list[Path]:
    """
    Find all supported image files recursively.
    """
    return sorted(
        path
        for path in image_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


# ---------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------

def extract_metadata(image_path: Path) -> dict:
    """
    Extract metadata from one image using ExifTool.
    """

    command = [
        "exiftool",
        "-j",
        "-n",
        str(image_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)[0]


def process_image(
    image_path: Path,
    image_id: str,
) -> dict:
    """
    Extract metadata from one image and add project-specific fields.
    """

    metadata = extract_metadata(image_path)

    metadata["image_id"] = image_id

    metadata["relative_path"] = str(
        image_path.relative_to(PROJECT_ROOT)
    )

    return metadata


def process_images(
    images: list[Path],
) -> list[dict]:
    """
    Extract metadata from all images.

    Images that fail metadata extraction are skipped.
    """

    all_metadata = []

    for index, image_path in enumerate(images, start=1):

        image_id = f"IMG_{index:04d}"

        print(
            f"[{index:02d}/{len(images):02d}] "
            f"{image_path.name}"
        )

        try:
            metadata = process_image(
                image_path,
                image_id,
            )

            all_metadata.append(metadata)

        except subprocess.CalledProcessError as error:

            print("  ERROR: ExifTool failed")
            print(f"  {error}")

        except json.JSONDecodeError:

            print("  ERROR: Could not decode ExifTool output")

    return all_metadata


# ---------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------

def get_metadata_fields(
    metadata: list[dict],
) -> list[str]:
    """
    Return all metadata fields found across the dataset.
    """

    return sorted(
        {
            key
            for item in metadata
            for key in item.keys()
        }
    )


def save_metadata(
    metadata: list[dict],
) -> None:
    """
    Save extracted metadata as JSON and CSV.
    """

    fields = get_metadata_fields(metadata)

    write_json(
        OUTPUT_JSON,
        metadata,
    )

    write_csv(
        OUTPUT_CSV,
        metadata,
        fieldnames=fields,
    )

    print()
    print(f"Metadata fields  : {len(fields)}")
    print()
    print(f"JSON : {OUTPUT_JSON}")
    print(f"CSV  : {OUTPUT_CSV}")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("CATTLE-VISION - METADATA EXTRACTION")
    print("=" * 70)

    print()
    print(f"Project : {PROJECT_ROOT}")
    print(f"Images  : {IMAGE_DIR}")
    print()

    images = find_images(IMAGE_DIR)

    print(f"Found {len(images)} images")
    print()

    if not images:
        print("No images found.")
        return

    metadata = process_images(images)

    print()

    if not metadata:
        print("No metadata extracted.")
        return

    save_metadata(metadata)

    print()
    print("Done!")
    print()
    print(f"Images processed : {len(metadata)}")


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()