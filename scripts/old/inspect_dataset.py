from pathlib import Path
import csv
import math
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "images"

CSV_FILE = METADATA_DIR / "dataset.csv"


# ============================================================
# DERIVED COLUMNS
# ============================================================

DERIVED_FIELDS = [
    "camera_orientation",
    "off_nadir_angle_deg",
    "vertical_fov_deg",
    "nadir_ground_width_m",
    "nadir_ground_height_m",
    "nadir_equivalent_gsd_cm_px",
]


# ============================================================
# REQUIRED INPUT COLUMNS
# ============================================================

REQUIRED_FIELDS = [
    "image_id",
    "FileName",
    "DateTimeOriginal",
    "ExifImageWidth",
    "ExifImageHeight",
    "FocalLength",
    "FOV",
    "GPSLatitude",
    "GPSLongitude",
    "RelativeAltitude",
    "GimbalPitchDegree",
]


# ============================================================
# HELPERS
# ============================================================

def parse_float(value):
    """
    Convert a value to float.

    Returns None if the value is empty or invalid.
    """

    if value is None or value == "":
        return None

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


def parse_datetime(value):
    """
    Parse DJI DateTimeOriginal.

    Expected format:
        YYYY:MM:DD HH:MM:SS

    Returns a datetime object or None.
    """

    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y:%m:%d %H:%M:%S"
        )

    except ValueError:
        return None


def classify_camera_orientation(gimbal_pitch):
    """
    Classify the camera as NADIR or OBLIQUE.

    DJI gimbal pitch:
        -90° = straight down

    NADIR tolerance:
        ±10° around -90°
    """

    pitch = parse_float(gimbal_pitch)

    if pitch is None:
        return None

    off_nadir = abs(pitch + 90.0)

    if off_nadir <= 10.0:
        return "NADIR"

    return "OBLIQUE"


def calculate_off_nadir_angle(gimbal_pitch):
    """
    Calculate the angle between the camera direction
    and the nadir direction.

    DJI:
        -90° = nadir
         0°  = horizontal

    Therefore:

        off_nadir = |pitch + 90|
    """

    pitch = parse_float(gimbal_pitch)

    if pitch is None:
        return None

    return abs(pitch + 90.0)


def calculate_vertical_fov(
    horizontal_fov,
    image_width,
    image_height
):
    """
    Estimate vertical FOV from horizontal FOV and
    image aspect ratio.

    Formula:

        vfov = 2 * atan(
            tan(hfov / 2) * height / width
        )
    """

    hfov = parse_float(horizontal_fov)
    width = parse_float(image_width)
    height = parse_float(image_height)

    if (
        hfov is None
        or width is None
        or height is None
        or width <= 0
        or height <= 0
    ):
        return None

    hfov_rad = math.radians(hfov)

    vfov_rad = 2.0 * math.atan(
        math.tan(hfov_rad / 2.0)
        * (height / width)
    )

    return math.degrees(vfov_rad)


def calculate_nadir_ground_coverage(
    altitude,
    horizontal_fov,
    vertical_fov
):
    """
    Calculate approximate ground coverage assuming:

        - camera is NADIR
        - terrain is flat
        - altitude is relative altitude
        - FOV represents the camera field of view

    Returns:

        ground_width_m
        ground_height_m
    """

    altitude = parse_float(altitude)
    hfov = parse_float(horizontal_fov)
    vfov = parse_float(vertical_fov)

    if (
        altitude is None
        or hfov is None
        or vfov is None
        or altitude <= 0
    ):
        return None, None

    hfov_rad = math.radians(hfov)
    vfov_rad = math.radians(vfov)

    ground_width = (
        2.0
        * altitude
        * math.tan(hfov_rad / 2.0)
    )

    ground_height = (
        2.0
        * altitude
        * math.tan(vfov_rad / 2.0)
    )

    return ground_width, ground_height


def calculate_nadir_gsd(
    ground_width,
    image_width
):
    """
    Calculate approximate nadir GSD.

    Returns meters/pixel.
    """

    ground_width = parse_float(ground_width)
    image_width = parse_float(image_width)

    if (
        ground_width is None
        or image_width is None
        or image_width <= 0
    ):
        return None

    return ground_width / image_width


def format_range(values, decimals=2):
    """
    Format min/max range.
    """

    valid = [
        value
        for value in values
        if value is not None
    ]

    if not valid:
        return "N/A"

    return (
        f"{min(valid):.{decimals}f}"
        f" → "
        f"{max(valid):.{decimals}f}"
    )


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():
    """
    Load dataset.csv.
    """

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Dataset CSV not found:\n{CSV_FILE}"
        )

    with CSV_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        fieldnames = reader.fieldnames

        if not fieldnames:
            raise ValueError(
                "dataset.csv has no header."
            )

        rows = list(reader)

    if not rows:
        raise ValueError(
            "dataset.csv is empty."
        )

    return fieldnames, rows


# ============================================================
# VALIDATE DATASET
# ============================================================

def validate_dataset(fieldnames):
    """
    Validate required input columns.
    """

    missing = [
        field
        for field in REQUIRED_FIELDS
        if field not in fieldnames
    ]

    if missing:

        print()
        print(
            "ERROR: dataset.csv is missing "
            "required columns:"
        )

        for field in missing:
            print(f"  - {field}")

        raise ValueError(
            "dataset.csv does not contain "
            "all required columns."
        )


# ============================================================
# PROCESS DATASET
# ============================================================

def process_rows(rows):
    """
    Calculate and add derived attributes.
    """

    processed_rows = []

    for row in rows:

        # ----------------------------------------------------
        # Camera orientation
        # ----------------------------------------------------

        orientation = classify_camera_orientation(
            row.get("GimbalPitchDegree")
        )

        row["camera_orientation"] = (
            orientation
            if orientation is not None
            else ""
        )

        # ----------------------------------------------------
        # Off-nadir angle
        # ----------------------------------------------------

        off_nadir = calculate_off_nadir_angle(
            row.get("GimbalPitchDegree")
        )

        row["off_nadir_angle_deg"] = (
            f"{off_nadir:.6f}"
            if off_nadir is not None
            else ""
        )

        # ----------------------------------------------------
        # Vertical FOV
        # ----------------------------------------------------

        vertical_fov = calculate_vertical_fov(
            row.get("FOV"),
            row.get("ExifImageWidth"),
            row.get("ExifImageHeight")
        )

        row["vertical_fov_deg"] = (
            f"{vertical_fov:.6f}"
            if vertical_fov is not None
            else ""
        )

        # ----------------------------------------------------
        # Nadir ground coverage
        # ----------------------------------------------------

        ground_width, ground_height = (
            calculate_nadir_ground_coverage(
                row.get("RelativeAltitude"),
                row.get("FOV"),
                vertical_fov
            )
        )

        row["nadir_ground_width_m"] = (
            f"{ground_width:.6f}"
            if ground_width is not None
            else ""
        )

        row["nadir_ground_height_m"] = (
            f"{ground_height:.6f}"
            if ground_height is not None
            else ""
        )

        # ----------------------------------------------------
        # Nadir-equivalent GSD
        # ----------------------------------------------------

        nadir_gsd = calculate_nadir_gsd(
            ground_width,
            row.get("ExifImageWidth")
        )

        if nadir_gsd is not None:
            row["nadir_equivalent_gsd_cm_px"] = (
                f"{nadir_gsd * 100.0:.6f}"
            )
        else:
            row["nadir_equivalent_gsd_cm_px"] = ""

        processed_rows.append(row)

    return processed_rows


# ============================================================
# IMAGE FILE CHECK
# ============================================================

def check_image_files(rows):
    """
    Check whether all image files referenced by
    dataset.csv exist in data/raw/images.
    """

    missing_files = []

    for row in rows:

        filename = row.get("FileName", "")

        if not filename:
            missing_files.append(
                "(empty filename)"
            )
            continue

        image_path = IMAGE_DIR / filename

        if not image_path.exists():
            missing_files.append(filename)

    return missing_files


# ============================================================
# SAVE DATASET
# ============================================================

def save_dataset(
    fieldnames,
    rows
):
    """
    Write the processed dataset back to dataset.csv.

    Existing columns are preserved.
    Derived columns are appended at the end.
    """

    output_fields = list(fieldnames)

    for field in DERIVED_FIELDS:

        if field not in output_fields:
            output_fields.append(field)

    with CSV_FILE.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=output_fields
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


# ============================================================
# MAIN INSPECTION REPORT
# ============================================================

def print_report(
    fieldnames,
    rows,
    missing_files
):

    print()
    print("=" * 70)
    print("CATTLE-VISION DATASET INSPECTION")
    print("=" * 70)

    # --------------------------------------------------------
    # General
    # --------------------------------------------------------

    print()
    print("GENERAL")
    print("-" * 70)

    print(f"Dataset: {CSV_FILE}")
    print(f"Images: {len(rows)}")
    print(f"Columns: {len(fieldnames)}")

    # --------------------------------------------------------
    # Camera
    # --------------------------------------------------------

    products = sorted(
        set(
            row.get("ProductName", "")
            for row in rows
            if row.get("ProductName", "")
        )
    )

    models = sorted(
        set(
            row.get("UniqueCameraModel", "")
            for row in rows
            if row.get("UniqueCameraModel", "")
        )
    )

    print()
    print("CAMERA")
    print("-" * 70)

    print(
        "Products: "
        + (
            ", ".join(products)
            if products
            else "N/A"
        )
    )

    print(
        "Models: "
        + (
            ", ".join(models)
            if models
            else "N/A"
        )
    )

    # --------------------------------------------------------
    # Resolution
    # --------------------------------------------------------

    resolutions = sorted(
        set(
            (
                row.get("ExifImageWidth"),
                row.get("ExifImageHeight")
            )
            for row in rows
        )
    )

    print()
    print("IMAGE")
    print("-" * 70)

    print(
        "Resolutions: "
        + ", ".join(
            f"{width}x{height}"
            for width, height in resolutions
        )
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    dates = []

    for row in rows:

        dt = parse_datetime(
            row.get("DateTimeOriginal")
        )

        if dt:
            dates.append(dt)

    print()
    print("DATE")
    print("-" * 70)

    if dates:

        print(
            f"Range: "
            f"{min(dates).strftime('%Y-%m-%d')} "
            f"→ "
            f"{max(dates).strftime('%Y-%m-%d')}"
        )

        date_counts = {}

        for dt in dates:

            date_key = dt.strftime(
                "%Y-%m-%d"
            )

            date_counts[date_key] = (
                date_counts.get(date_key, 0) + 1
            )

        for date_key in sorted(date_counts):

            print(
                f"  {date_key}: "
                f"{date_counts[date_key]}"
            )

    else:
        print("No valid dates.")

    # --------------------------------------------------------
    # GPS
    # --------------------------------------------------------

    latitudes = [
        parse_float(
            row.get("GPSLatitude")
        )
        for row in rows
    ]

    longitudes = [
        parse_float(
            row.get("GPSLongitude")
        )
        for row in rows
    ]

    print()
    print("GPS")
    print("-" * 70)

    print(
        "Latitude:  "
        + format_range(
            latitudes,
            7
        )
    )

    print(
        "Longitude: "
        + format_range(
            longitudes,
            7
        )
    )

    # --------------------------------------------------------
    # Altitude
    # --------------------------------------------------------

    altitudes = [
        parse_float(
            row.get("RelativeAltitude")
        )
        for row in rows
    ]

    valid_altitudes = [
        value
        for value in altitudes
        if value is not None
    ]

    print()
    print("ALTITUDE")
    print("-" * 70)

    print(
        "Relative altitude: "
        + format_range(
            altitudes,
            2
        )
        + " m"
    )

    if valid_altitudes:

        mean_altitude = (
            sum(valid_altitudes)
            / len(valid_altitudes)
        )

        print(
            f"Mean altitude: "
            f"{mean_altitude:.2f} m"
        )

    # --------------------------------------------------------
    # Camera orientation
    # --------------------------------------------------------

    orientation_counts = {}

    for row in rows:

        orientation = row.get(
            "camera_orientation"
        )

        if orientation:
            orientation_counts[orientation] = (
                orientation_counts.get(
                    orientation,
                    0
                ) + 1
            )

    print()
    print("CAMERA ORIENTATION")
    print("-" * 70)

    for orientation in (
        "NADIR",
        "OBLIQUE"
    ):

        print(
            f"{orientation}: "
            f"{orientation_counts.get(orientation, 0)}"
        )

    # --------------------------------------------------------
    # Off-nadir
    # --------------------------------------------------------

    off_nadir_values = [
        parse_float(
            row.get("off_nadir_angle_deg")
        )
        for row in rows
    ]

    print()
    print("OFF-NADIR ANGLE")
    print("-" * 70)

    print(
        "Range: "
        + format_range(
            off_nadir_values,
            2
        )
        + "°"
    )

    # --------------------------------------------------------
    # Optics
    # --------------------------------------------------------

    focal_lengths = [
        parse_float(
            row.get("FocalLength")
        )
        for row in rows
    ]

    fovs = [
        parse_float(
            row.get("FOV")
        )
        for row in rows
    ]

    vertical_fovs = [
        parse_float(
            row.get("vertical_fov_deg")
        )
        for row in rows
    ]

    print()
    print("OPTICS")
    print("-" * 70)

    print(
        "Focal length: "
        + format_range(
            focal_lengths,
            2
        )
        + " mm"
    )

    print(
        "Horizontal FOV: "
        + format_range(
            fovs,
            2
        )
        + "°"
    )

    print(
        "Vertical FOV: "
        + format_range(
            vertical_fovs,
            2
        )
        + "°"
    )

    # --------------------------------------------------------
    # GSD
    # --------------------------------------------------------

    gsd_values = [
        parse_float(
            row.get(
                "nadir_equivalent_gsd_cm_px"
            )
        )
        for row in rows
    ]

    print()
    print("NADIR-EQUIVALENT GSD")
    print("-" * 70)

    print(
        "Range: "
        + format_range(
            gsd_values,
            2
        )
        + " cm/px"
    )

    # --------------------------------------------------------
    # ISO
    # --------------------------------------------------------

    iso_values = [
        parse_float(
            row.get("ISO")
        )
        for row in rows
    ]

    valid_iso = [
        int(value)
        for value in iso_values
        if value is not None
    ]

    print()
    print("EXPOSURE")
    print("-" * 70)

    if valid_iso:

        iso_counts = {}

        for iso in valid_iso:

            iso_counts[iso] = (
                iso_counts.get(iso, 0) + 1
            )

        print(
            "ISO values: "
            + ", ".join(
                f"{iso} ({count})"
                for iso, count
                in sorted(iso_counts.items())
            )
        )

    else:
        print("No valid ISO values.")

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    print()
    print("MISSING VALUES")
    print("-" * 70)

    missing_total = 0

    for field in fieldnames:

        missing_count = sum(
            1
            for row in rows
            if row.get(field, "") == ""
            or row.get(field) is None
        )

        if missing_count > 0:

            print(
                f"  {field}: "
                f"{missing_count}"
            )

            missing_total += missing_count

    if missing_total == 0:
        print("No missing values in dataset.")

    # --------------------------------------------------------
    # Image files
    # --------------------------------------------------------

    print()
    print("IMAGE FILES")
    print("-" * 70)

    if not missing_files:

        print(
            f"All {len(rows)} image files found."
        )

    else:

        print(
            f"Missing image files: "
            f"{len(missing_files)}"
        )

        for filename in missing_files:
            print(f"  - {filename}")

    # --------------------------------------------------------
    # Derived fields
    # --------------------------------------------------------

    print()
    print("DERIVED ATTRIBUTES")
    print("-" * 70)

    for field in DERIVED_FIELDS:
        print(f"  - {field}")

    print()
    print("=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    fieldnames, rows = load_dataset()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_dataset(fieldnames)

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    rows = process_rows(rows)

    # --------------------------------------------------------
    # Check image files
    # --------------------------------------------------------

    missing_files = check_image_files(rows)

    # --------------------------------------------------------
    # Save derived attributes
    # --------------------------------------------------------

    save_dataset(
        fieldnames,
        rows
    )

    # --------------------------------------------------------
    # Print report
    # --------------------------------------------------------

    print_report(
        fieldnames,
        rows,
        missing_files
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    print()
    print("Dataset updated:")
    print(f"  {CSV_FILE}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()