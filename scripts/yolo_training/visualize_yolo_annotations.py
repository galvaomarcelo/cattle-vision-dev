"""
Cattle-Vision - Visualize YOLO Annotations

Reads YOLO bounding-box annotations exported from CVAT and draws them
over the original images for visual inspection.

Input:
    data/raw/images/
    data/annotations/test_sample_yolo/labels/Train/

Output:
    data/inspection/yolo_annotations/

YOLO format:
    class_id center_x center_y width height

Coordinates are normalized to [0, 1].
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "images"

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
    / "inspection"
    / "yolo_annotations"
)

CLASS_NAMES = {
    0: "cattle",
}

BOX_WIDTH = 3

TEXT_MARGIN = 5
TEXT_PADDING = 4


def find_image(image_name: str) -> Path | None:
    """
    Find the original image corresponding to an annotation file.
    """
    image_path = IMAGE_DIR / image_name

    if image_path.exists():
        return image_path

    for extension in (".JPG", ".jpg", ".JPEG", ".jpeg", ".PNG", ".png"):
        candidate = IMAGE_DIR / f"{image_name}{extension}"

        if candidate.exists():
            return candidate

    return None


def read_yolo_annotations(
    annotation_path: Path,
) -> list[tuple[int, float, float, float, float]]:
    """
    Read YOLO annotations.

    Returns:
        List of tuples:
            (class_id, center_x, center_y, width, height)
    """
    annotations = []

    with annotation_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            values = line.split()

            if len(values) != 5:
                raise ValueError(
                    f"Invalid YOLO annotation in "
                    f"{annotation_path.name}, line {line_number}: "
                    f"{line}"
                )

            class_id = int(values[0])

            center_x = float(values[1])
            center_y = float(values[2])
            width = float(values[3])
            height = float(values[4])

            annotations.append(
                (
                    class_id,
                    center_x,
                    center_y,
                    width,
                    height,
                )
            )

    return annotations


def yolo_to_pixels(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    """
    Convert normalized YOLO coordinates to pixel coordinates.

    Returns:
        left, top, right, bottom
    """
    box_width = width * image_width
    box_height = height * image_height

    center_x_px = center_x * image_width
    center_y_px = center_y * image_height

    left = int(center_x_px - box_width / 2)
    top = int(center_y_px - box_height / 2)
    right = int(center_x_px + box_width / 2)
    bottom = int(center_y_px + box_height / 2)

    return left, top, right, bottom


def load_font(size: int = 24):
    """Load a suitable font for annotation labels."""
    try:
        return ImageFont.truetype(
            "arial.ttf",
            size,
        )
    except OSError:
        return ImageFont.load_default()


def draw_annotation(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    font,
) -> None:
    """Draw one bounding box and its label."""
    left, top, right, bottom = box

    draw.rectangle(
        [left, top, right, bottom],
        outline="red",
        width=BOX_WIDTH,
    )

    text_bbox = draw.textbbox(
        (0, 0),
        label,
        font=font,
    )

    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    text_left = left
    text_top = max(
        0,
        top - text_height - TEXT_MARGIN * 2,
    )

    draw.rectangle(
        [
            text_left,
            text_top,
            text_left + text_width + TEXT_PADDING * 2,
            text_top + text_height + TEXT_PADDING * 2,
        ],
        fill="red",
    )

    draw.text(
        (
            text_left + TEXT_PADDING,
            text_top + TEXT_PADDING,
        ),
        label,
        fill="white",
        font=font,
    )


def visualize_annotation(
    annotation_path: Path,
) -> None:
    """Create an annotated copy of the corresponding image."""
    image_name = annotation_path.stem

    image_path = find_image(image_name)

    if image_path is None:
        print(
            f"  WARNING: image not found for "
            f"{annotation_path.name}"
        )
        return

    annotations = read_yolo_annotations(
        annotation_path
    )

    image = Image.open(image_path).convert("RGB")

    image_width, image_height = image.size

    draw = ImageDraw.Draw(image)

    font = load_font()

    for class_id, center_x, center_y, width, height in annotations:
        label = CLASS_NAMES.get(
            class_id,
            f"class_{class_id}",
        )

        box = yolo_to_pixels(
            center_x,
            center_y,
            width,
            height,
            image_width,
            image_height,
        )

        draw_annotation(
            draw,
            box,
            label,
            font,
        )

    output_path = OUTPUT_DIR / image_path.name

    image.save(
        output_path,
        quality=95,
    )

    print(
        f"  {image_path.name}: "
        f"{len(annotations)} cattle"
    )


def main():
    print("=" * 70)
    print("CATTLE-VISION - YOLO ANNOTATION VISUALIZATION")
    print("=" * 70)

    print()
    print(f"Images      : {IMAGE_DIR}")
    print(f"Annotations : {ANNOTATION_DIR}")
    print(f"Output      : {OUTPUT_DIR}")
    print()

    if not IMAGE_DIR.exists():
        print("ERROR: Image directory does not exist.")
        return

    if not ANNOTATION_DIR.exists():
        print("ERROR: Annotation directory does not exist.")
        return

    annotation_files = sorted(
        ANNOTATION_DIR.glob("*.txt")
    )

    print(
        f"Found {len(annotation_files)} "
        f"annotation files."
    )
    print()

    if not annotation_files:
        print("No annotation files found.")
        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for annotation_path in annotation_files:
        visualize_annotation(annotation_path)

    print()
    print("=" * 70)
    print("Done!")
    print("=" * 70)
    print()
    print(f"Output directory:")
    print(f"  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()