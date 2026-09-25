from pathlib import Path


from utils import (
    format_duration,
    parse_datetime,
    parse_float,
    read_csv,
    write_csv,
    write_json,
)

from geo import latlon_distance_m


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

DATASET_CSV = METADATA_DIR / "dataset_clean.csv"
DATASET_JSON = METADATA_DIR / "dataset_clean.json"

SUMMARY_CSV = METADATA_DIR / "flight_groups_summary.csv"


# Heuristic thresholds
MAX_TIME_GAP_MINUTES = 15
MAX_DISTANCE_METERS = 200


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def get_datetime(row: dict) -> object:
    """Return the image timestamp."""
    return parse_datetime(row.get("DateTimeOriginal"))


def get_latitude(row: dict) -> float | None:
    return parse_float(row.get("GPSLatitude"))


def get_longitude(row: dict) -> float | None:
    return parse_float(row.get("GPSLongitude"))


def get_orientation(row: dict) -> str:
    """Return NADIR or OBLIQUE."""
    return (row.get("camera_orientation") or "").strip().upper()


def should_start_new_group(
    previous: dict,
    current: dict,
) -> tuple[bool, str]:
    """
    Determine whether the current image should start a new flight group.

    Returns:
        (new_group, reason)
    """

    previous_datetime = get_datetime(previous)
    current_datetime = get_datetime(current)

    # -------------------------------------------------------------
    # Time
    # -------------------------------------------------------------

    if previous_datetime is not None and current_datetime is not None:
        time_gap_seconds = (
            current_datetime - previous_datetime
        ).total_seconds()

        time_gap_minutes = time_gap_seconds / 60.0

        if time_gap_minutes > MAX_TIME_GAP_MINUTES:
            return True, "time"


    # -------------------------------------------------------------
    # Distance
    # -------------------------------------------------------------

    previous_lat = get_latitude(previous)
    previous_lon = get_longitude(previous)

    current_lat = get_latitude(current)
    current_lon = get_longitude(current)

    if (
        previous_lat is not None
        and previous_lon is not None
        and current_lat is not None
        and current_lon is not None
    ):
        distance = latlon_distance_m(
            previous_lat,
            previous_lon,
            current_lat,
            current_lon,
        )

        if distance > MAX_DISTANCE_METERS:
            return True, "distance"


    # -------------------------------------------------------------
    # Camera orientation
    # -------------------------------------------------------------

    previous_orientation = get_orientation(previous)
    current_orientation = get_orientation(current)

    if (
        previous_orientation
        and current_orientation
        and previous_orientation != current_orientation
    ):
        return True, "orientation"


    return False, ""


# ---------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------

def assign_flight_groups(
    rows: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Assign a flight_group to every image.

    Returns:
        updated rows
        flight group summary rows
    """

    if not rows:
        return [], []

    # Always process images chronologically.
    rows = sorted(
        rows,
        key=lambda row: (
            get_datetime(row) is None,
            get_datetime(row),
        ),
    )

    flight_group = 1

    rows[0]["flight_group"] = str(flight_group)

    group_start_index = 0

    summary_rows = []

    for index in range(1, len(rows)):

        previous = rows[index - 1]
        current = rows[index]

        new_group, reason = should_start_new_group(
            previous,
            current,
        )

        if new_group:

            summary_rows.append(
                create_group_summary(
                    rows,
                    group_start_index,
                    index - 1,
                    flight_group,
                )
            )

            flight_group += 1

            group_start_index = index

        current["flight_group"] = str(flight_group)

    # Final group
    summary_rows.append(
        create_group_summary(
            rows,
            group_start_index,
            len(rows) - 1,
            flight_group,
        )
    )

    return rows, summary_rows


# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

def create_group_summary(
    rows: list[dict],
    start_index: int,
    end_index: int,
    flight_group: int,
) -> dict:

    group = rows[start_index:end_index + 1]

    start_datetime = get_datetime(group[0])
    end_datetime = get_datetime(group[-1])

    duration_seconds = None

    if start_datetime is not None and end_datetime is not None:
        duration_seconds = (
            end_datetime - start_datetime
        ).total_seconds()

    orientations = {
        get_orientation(row)
        for row in group
        if get_orientation(row)
    }

    if len(orientations) == 1:
        orientation = next(iter(orientations))
    elif len(orientations) > 1:
        orientation = "MIXED"
    else:
        orientation = ""

    latitudes = [
        get_latitude(row)
        for row in group
        if get_latitude(row) is not None
    ]

    longitudes = [
        get_longitude(row)
        for row in group
        if get_longitude(row) is not None
    ]

    return {
        "flight_group": flight_group,
        "images": len(group),
        "start_time": (
            start_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if start_datetime
            else ""
        ),
        "end_time": (
            end_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if end_datetime
            else ""
        ),
        "duration_min": (
            round(duration_seconds / 60.0, 2)
            if duration_seconds is not None
            else ""
        ),
        "duration": (
            format_duration(duration_seconds)
            if duration_seconds is not None
            else ""
        ),
        "camera_orientation": orientation,
        "min_latitude": (
            min(latitudes)
            if latitudes
            else ""
        ),
        "max_latitude": (
            max(latitudes)
            if latitudes
            else ""
        ),
        "min_longitude": (
            min(longitudes)
            if longitudes
            else ""
        ),
        "max_longitude": (
            max(longitudes)
            if longitudes
            else ""
        ),
    }


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print("CATTLE-VISION - FLIGHT GROUP ANALYSIS")
    print("=" * 70)

    print()
    print(f"Input:  {DATASET_CSV}")
    print(f"Output: {SUMMARY_CSV}")
    print()

    # -------------------------------------------------------------
    # Read dataset
    # -------------------------------------------------------------

    rows = read_csv(DATASET_CSV)

    if not rows:
        raise RuntimeError("Dataset is empty.")

    print(f"Images loaded: {len(rows)}")

    # -------------------------------------------------------------
    # Assign groups
    # -------------------------------------------------------------

    rows, summary_rows = assign_flight_groups(rows)

    # -------------------------------------------------------------
    # Preserve original column order and append flight_group
    # -------------------------------------------------------------

    original_columns = list(rows[0].keys())

    if "flight_group" in original_columns:
        original_columns.remove("flight_group")

    fieldnames = original_columns + ["flight_group"]

    # -------------------------------------------------------------
    # Save CSV
    # -------------------------------------------------------------

    write_csv(
        DATASET_CSV,
        rows,
        fieldnames=fieldnames,
    )

    # -------------------------------------------------------------
    # Save JSON
    # -------------------------------------------------------------

    # The JSON is regenerated from the updated dataset.
    write_json(
        DATASET_JSON,
        rows,
    )

    # -------------------------------------------------------------
    # Save summary
    # -------------------------------------------------------------

    summary_fields = [
        "flight_group",
        "images",
        "start_time",
        "end_time",
        "duration_min",
        "duration",
        "camera_orientation",
        "min_latitude",
        "max_latitude",
        "min_longitude",
        "max_longitude",
    ]

    write_csv(
        SUMMARY_CSV,
        summary_rows,
        fieldnames=summary_fields,
    )

    # -------------------------------------------------------------
    # Console report
    # -------------------------------------------------------------

    print()
    print("-" * 70)
    print("FLIGHT GROUPS")
    print("-" * 70)

    for summary in summary_rows:

        print(
            f"Group {summary['flight_group']:>2} | "
            f"{summary['images']:>2} images | "
            f"{summary['camera_orientation']:<7} | "
            f"{summary['start_time']} -> "
            f"{summary['end_time']}"
        )

    print()
    print("-" * 70)
    print(f"Total images : {len(rows)}")
    print(f"Flight groups: {len(summary_rows)}")
    print("-" * 70)

    print()
    print(f"Updated: {DATASET_CSV}")
    print(f"Updated: {DATASET_JSON}")
    print(f"Created: {SUMMARY_CSV}")
    print()


if __name__ == "__main__":
    main()