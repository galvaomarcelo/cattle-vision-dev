from pathlib import Path
import csv


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

INPUT_CSV = METADATA_DIR / "images_metadata.csv"
OUTPUT_CSV = METADATA_DIR / "dataset.csv"


# ============================================================
# Canonical Cattle-Vision dataset columns
# ============================================================

KEEP_COLUMNS = [

    # Identity
    "image_id",
    "FileName",
    "relative_path",

    # Time
    "DateTimeOriginal",

    # Camera
    "ProductName",
    "UniqueCameraModel",

    # Image
    "ExifImageWidth",
    "ExifImageHeight",

    # Exposure
    "ExposureTime",
    "ISO",
    "ExposureCompensation",
    "WhiteBalanceCCT",

    # Optics
    "FNumber",
    "FocalLength",
    "FocalLengthIn35mmFormat",
    "FOV",

    # GPS
    "GPSLatitude",
    "GPSLongitude",
    "GPSAltitude",
    "RelativeAltitude",

    # Gimbal attitude
    "GimbalPitchDegree",
    "GimbalYawDegree",
    "GimbalRollDegree",

    # Flight attitude / movement
    "FlightPitchDegree",
    "FlightRollDegree",
    "FlightYawDegree",
    "FlightXSpeed",
    "FlightYSpeed",
    "FlightZSpeed",
]


# ============================================================
# Optional metadata
#
# Kept here for documentation. These may become useful later.
# ============================================================

# "FileSize",
# "MIMEType",
# "Make",
# "Model",
# "SerialNumber",
# "GPSLatitudeRef",
# "GPSLongitudeRef",
# "GPSPosition",
# "AbsoluteAltitude",
# "ScaleFactor35efl",
# "ZoomFactor",
# "WhiteBalance",


# ============================================================
# DJI / debug / internal metadata
# ============================================================

DROP_PREFIXES = (
    "ADJDebugInfo",
    "AEDebugInfo",
    "AEHistogramInfo",
    "AELiveViewHistogramInfo",
    "AELiveViewLocalHistogram",
    "AELocalHistogram",
    "AFDebugInfo",
    "Awb_Dbg_Data_V2",
    "Histogram",
    "HyperlapsDebugInfo",
    "Scap_Info",
    "Sisr_Info",
    "PreviewImage",
    "ThumbnailImage",
    "SelfData",
    "ImageUIDList",
    "DeviceSettingDescription",
)


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("CATTLE-VISION - COLUMN FILTER")
    print("=" * 60)

    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_CSV}"
        )

    # --------------------------------------------------------
    # Read input
    # --------------------------------------------------------

    with INPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        input_columns = reader.fieldnames
        rows = list(reader)

    if not input_columns:
        raise ValueError("Input CSV has no header.")

    print(f"\nInput: {INPUT_CSV}")
    print(f"Images: {len(rows)}")
    print(f"Input columns: {len(input_columns)}")

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    missing = [
        column
        for column in KEEP_COLUMNS
        if column not in input_columns
    ]

    if missing:
        print("\nERROR: Missing required columns:")

        for column in missing:
            print(f"  - {column}")

        raise ValueError(
            "The input metadata does not contain all "
            "required columns."
        )

    # --------------------------------------------------------
    # Filter
    # --------------------------------------------------------

    clean_rows = [
        {
            column: row[column]
            for column in KEEP_COLUMNS
        }
        for row in rows
    ]

    # --------------------------------------------------------
    # Write output
    # --------------------------------------------------------

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=KEEP_COLUMNS
        )

        writer.writeheader()
        writer.writerows(clean_rows)

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    discarded = [
        column
        for column in input_columns
        if column not in KEEP_COLUMNS
    ]

    print(f"Output columns: {len(KEEP_COLUMNS)}")
    print(f"Discarded columns: {len(discarded)}")

    print("\nOutput:")
    print(f"  {OUTPUT_CSV}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()