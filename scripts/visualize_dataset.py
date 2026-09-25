from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from utils import parse_datetime, parse_float, read_csv


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "dataset_clean.csv"
)

IMAGE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "images"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "inspection"
    / "dataset_overview.jpg"
)


THUMB_WIDTH = 320
THUMB_HEIGHT = 220

COLUMNS = 4

CELL_WIDTH = 360
CELL_HEIGHT = 350

BACKGROUND = "white"
TEXT_COLOR = "black"


# ---------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------

def load_font(size: int, bold: bool = False):
    """Load a common Windows font, with a safe fallback."""

    candidates = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
    )

    for path in candidates:
        font_path = Path(path)

        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)

    return ImageFont.load_default()


FONT_TITLE = load_font(18, bold=True)
FONT_INFO = load_font(15)
FONT_SMALL = load_font(14)


# ---------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------

def format_id(row: dict) -> str:
    return row.get("image_id", "Unknown")


def format_orientation(row: dict) -> str:
    orientation = (
        row.get("camera_orientation") or "UNKNOWN"
    ).upper()

    return orientation


def format_group(row: dict) -> str:
    group = row.get("flight_group")

    if not group:
        return "—"

    return str(group)


def format_datetime(row: dict) -> str:
    value = parse_datetime(row.get("DateTimeOriginal"))

    if value is None:
        return "Unknown date"

    return value.strftime("%Y-%m-%d %H:%M")


def format_altitude(row: dict) -> str:
    altitude = parse_float(row.get("RelativeAltitude"))

    if altitude is None:
        altitude = parse_float(row.get("GPSAltitude"))

    if altitude is None:
        return "Altitude: —"

    return f"Altitude: {altitude:.1f} m"


def format_camera_angle(row: dict) -> str:
    value = parse_float(row.get("GimbalPitchDegree"))

    if value is None:
        return "Angle: —"

    return f"Angle: {value:.1f}°"


def format_gsd(row: dict) -> str:
    value = parse_float(
        row.get("nadir_equivalent_gsd_cm_px")
    )

    if value is None:
        return "GSD: —"

    return f"GSD: {value:.2f} cm/px"


def format_focal_length(row: dict) -> str:
    value = parse_float(row.get("FocalLength"))

    if value is None:
        return "Focal: —"

    return f"Focal: {value:.2f} mm"


def format_fov(row: dict) -> str:
    value = parse_float(row.get("FOV"))

    if value is None:
        return "FOV: —"

    return f"FOV: {value:.2f}°"


# ---------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------

def load_thumbnail(row: dict) -> Image.Image | None:
    """Load and resize an image for the overview."""

    filename = row.get("FileName")

    if not filename:
        return None

    image_path = IMAGE_DIR / filename

    if not image_path.exists():
        return None

    try:
        image = Image.open(image_path).convert("RGB")

        image.thumbnail(
            (THUMB_WIDTH, THUMB_HEIGHT),
            Image.Resampling.LANCZOS,
        )

        canvas = Image.new(
            "RGB",
            (THUMB_WIDTH, THUMB_HEIGHT),
            "white",
        )

        x = (THUMB_WIDTH - image.width) // 2
        y = (THUMB_HEIGHT - image.height) // 2

        canvas.paste(image, (x, y))

        return canvas

    except Exception:
        return None


# ---------------------------------------------------------------------
# Cell
# ---------------------------------------------------------------------

def draw_cell(
    canvas: Image.Image,
    row: dict,
    x: int,
    y: int,
) -> None:

    draw = ImageDraw.Draw(canvas)

    # -------------------------------------------------------------
    # Thumbnail
    # -------------------------------------------------------------

    thumbnail = load_thumbnail(row)

    thumb_x = x + 20
    thumb_y = y + 10

    if thumbnail is not None:
        canvas.paste(
            thumbnail,
            (thumb_x, thumb_y),
        )
    else:
        draw.rectangle(
            [
                thumb_x,
                thumb_y,
                thumb_x + THUMB_WIDTH,
                thumb_y + THUMB_HEIGHT,
            ],
            outline=TEXT_COLOR,
        )

        draw.text(
            (
                thumb_x + 10,
                thumb_y + THUMB_HEIGHT // 2,
            ),
            "Image not found",
            fill=TEXT_COLOR,
            font=FONT_INFO,
        )

    # -------------------------------------------------------------
    # Header
    # -------------------------------------------------------------

    header_y = y + THUMB_HEIGHT + 18

    image_id = format_id(row)
    orientation = format_orientation(row)
    group = format_group(row)

    draw.text(
        (x + 20, header_y),
        image_id,
        fill=TEXT_COLOR,
        font=FONT_TITLE,
    )

    draw.text(
        (x + 125, header_y),
        orientation,
        fill=TEXT_COLOR,
        font=FONT_INFO,
    )

    draw.text(
        (x + 245, header_y),
        f"Group {group}",
        fill=TEXT_COLOR,
        font=FONT_INFO,
    )

    # -------------------------------------------------------------
    # Date / time
    # -------------------------------------------------------------

    draw.text(
        (x + 20, header_y + 25),
        format_datetime(row),
        fill=TEXT_COLOR,
        font=FONT_INFO,
    )

    # -------------------------------------------------------------
    # Camera / flight information
    # -------------------------------------------------------------

    info_y = header_y + 50

    draw.text(
        (x + 20, info_y),
        format_altitude(row),
        fill=TEXT_COLOR,
        font=FONT_SMALL,
    )

    draw.text(
        (x + 185, info_y),
        format_camera_angle(row),
        fill=TEXT_COLOR,
        font=FONT_SMALL,
    )

    draw.text(
        (x + 20, info_y + 22),
        format_focal_length(row),
        fill=TEXT_COLOR,
        font=FONT_SMALL,
    )

    draw.text(
        (x + 20, info_y + 44),
        format_fov(row),
        fill=TEXT_COLOR,
        font=FONT_SMALL,
    )

    draw.text(
        (x + 185, info_y + 22),
        format_gsd(row),
        fill=TEXT_COLOR,
        font=FONT_SMALL,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print("CATTLE-VISION - DATASET VISUALIZATION")
    print("=" * 70)

    print()
    print(f"Dataset: {CSV_FILE}")
    print(f"Output:  {OUTPUT_FILE}")
    print()

    rows = read_csv(CSV_FILE)

    if not rows:
        raise RuntimeError("Dataset is empty.")

    # -------------------------------------------------------------
    # Sort by flight group and image time
    # -------------------------------------------------------------

    def sort_key(row):
        group = row.get("flight_group")

        try:
            group_number = int(group)
        except (TypeError, ValueError):
            group_number = 999999

        timestamp = parse_datetime(
            row.get("DateTimeOriginal")
        )

        return (
            group_number,
            timestamp is None,
            timestamp,
        )

    rows.sort(key=sort_key)

    # -------------------------------------------------------------
    # Canvas
    # -------------------------------------------------------------

    number_of_rows = (
        len(rows) + COLUMNS - 1
    ) // COLUMNS

    canvas_width = COLUMNS * CELL_WIDTH
    canvas_height = number_of_rows * CELL_HEIGHT

    canvas = Image.new(
        "RGB",
        (canvas_width, canvas_height),
        BACKGROUND,
    )

    # -------------------------------------------------------------
    # Draw cells
    # -------------------------------------------------------------

    for index, row in enumerate(rows):

        column = index % COLUMNS
        row_number = index // COLUMNS

        x = column * CELL_WIDTH
        y = row_number * CELL_HEIGHT

        draw_cell(
            canvas,
            row,
            x,
            y,
        )

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    canvas.save(
        OUTPUT_FILE,
        quality=92,
    )

    print(f"Images: {len(rows)}")
    print(f"Groups: {len(set(row.get('flight_group') for row in rows))}")
    print()
    print(f"Created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()