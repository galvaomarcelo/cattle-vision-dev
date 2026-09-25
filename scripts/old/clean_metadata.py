# clean_metadata.py
"""
Read the raw ExifTool JSON dump and produce a cleaned JSON + CSV
containing only the columns defined in columns.KEEP_COLUMNS.

Adds a computed ZoomFactor column based on 35mm-equivalent focal length.
"""

from pathlib import Path
import csv
import json

from columns_filter import KEEP_COLUMNS, WIDE_BASELINE_35MM


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

INPUT_JSON       = METADATA_DIR / "images_metadata.json"
OUTPUT_JSON      = METADATA_DIR / "images_metadata_clean.json"
OUTPUT_CSV       = METADATA_DIR / "images_metadata_clean.csv"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def compute_zoom_factor(record: dict) -> float | None:
    """
    Approximate zoom factor relative to the wide-lens baseline.

    Air 3S wide lens: 24mm equiv at 1x.
    ZoomFactor = FocalLengthIn35mmFormat / 24

    Returns None if the required field is missing or non-numeric.

    NOTE: This is only valid while shooting with the wide lens.
    Once the drone switches to the medium-tele lens, the baseline
    changes and this number should be treated as a rough indicator,
    not a true zoom ratio.
    """
    focal_35 = record.get("FocalLengthIn35mmFormat")

    if focal_35 is None:
        return None

    try:
        focal_35 = float(focal_35)
    except (TypeError, ValueError):
        return None

    if focal_35 <= 0:
        return None

    return round(focal_35 / WIDE_BASELINE_35MM, 3)


def clean_record(record: dict) -> dict:
    """
    Return a new dict containing only KEEP_COLUMNS, in that order.
    Adds ZoomFactor as a computed field.
    """
    cleaned = {col: record.get(col, None) for col in KEEP_COLUMNS}
    cleaned["ZoomFactor"] = compute_zoom_factor(record)
    return cleaned


def write_json(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=KEEP_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> None:

    if not INPUT_JSON.exists():
        print(f"ERROR: input not found: {INPUT_JSON}")
        print("Run extract_metadata.py first.")
        return

    with open(INPUT_JSON, encoding="utf-8") as f:
        raw_records = json.load(f)

    print(f"Loaded {len(raw_records)} records from {INPUT_JSON.name}")

    # --- Warn about KEEP_COLUMNS that never appear in the source ---
    present_keys = {k for r in raw_records for k in r.keys()}
    missing = [c for c in KEEP_COLUMNS if c not in present_keys and c != "ZoomFactor"]
    if missing:
        print("WARNING: these KEEP_COLUMNS were not found in the source:")
        for col in missing:
            print(f"  - {col}")

    # --- Clean ---
    cleaned_records = [clean_record(r) for r in raw_records]

    # --- Write both outputs ---
    write_json(cleaned_records, OUTPUT_JSON)
    write_csv(cleaned_records, OUTPUT_CSV)

    print()
    print("Done.")
    print(f"Records : {len(cleaned_records)}")
    print(f"Columns : {len(KEEP_COLUMNS)}")
    print(f"JSON    : {OUTPUT_JSON}")
    print(f"CSV     : {OUTPUT_CSV}")


if __name__ == "__main__":
    main()