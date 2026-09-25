"""
Create a GeoJSON containing the GPS position of the
currently annotated drone images.

This is an intermediate validation step for the
Cattle-Vision geolocation pipeline.

Only images with YOLO annotations are included.

The geometry is stored in WGS84 (EPSG:4326).

The metric CRS EPSG:29192 is not used for the
geometry yet; it will be used later for the
geometric DEM intersection.
"""

from __future__ import annotations

import json
from pathlib import Path

from utils import parse_float, read_csv


# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "dataset_clean.csv"
)

ANNOTATIONS_DIR = (
    PROJECT_ROOT
    / "data"
    / "annotations"
    / "test_sample_yolo"
    / "labels"
    / "Train"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "inspection"
    / "drone_positions.geojson"
)


# ============================================================================
# CRS
# ============================================================================

GEOGRAPHIC_CRS = "EPSG:4326"

METRIC_CRS = "EPSG:29192"


# ============================================================================
# FEATURE
# ============================================================================

def create_feature(
    row: dict[str, str],
) -> dict | None:
    """
    Create one GeoJSON Point from one image metadata record.

    The point represents the GPS position of the drone
    when the image was captured.
    """

    longitude = parse_float(
        row.get("GPSLongitude")
    )

    latitude = parse_float(
        row.get("GPSLatitude")
    )

    if longitude is None or latitude is None:
        return None

    relative_altitude = parse_float(
        row.get("RelativeAltitude")
    )

    absolute_altitude = parse_float(
        row.get("AbsoluteAltitude")
    )

    # ------------------------------------------------------------------------
    # Home altitude
    # ------------------------------------------------------------------------
    #
    # DJI:
    #
    #     AbsoluteAltitude
    #             -
    #     RelativeAltitude
    #
    # gives an estimate of the altitude of the
    # reference point for the relative altitude.
    #
    # Example:
    #
    #     331.374 - 87.200 = 244.174 m
    #

    home_altitude = None

    if (
        absolute_altitude is not None
        and relative_altitude is not None
    ):
        home_altitude = (
            absolute_altitude
            - relative_altitude
        )

    return {
        "type": "Feature",

        "geometry": {
            "type": "Point",
            "coordinates": [
                longitude,
                latitude,
            ],
        },

        "properties": {
            "image": Path(
                row["FileName"]
            ).stem,

            "relative_altitude_m": (
                relative_altitude
            ),

            "absolute_altitude_m": (
                absolute_altitude
            ),

            "home_altitude_m": (
                round(home_altitude, 3)
                if home_altitude is not None
                else None
            ),

            "gimbal_pitch_deg": parse_float(
                row.get("GimbalPitchDegree")
            ),

            "gimbal_yaw_deg": parse_float(
                row.get("GimbalYawDegree")
            ),

            "gimbal_roll_deg": parse_float(
                row.get("GimbalRollDegree")
            ),

            "fov_deg": parse_float(
                row.get("FOV")
            ),
        },
    }


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:

    print("Loading metadata...")

    metadata_rows = read_csv(
        METADATA_FILE
    )

    # ------------------------------------------------------------------------
    # Find the currently annotated images.
    #
    # Each YOLO .txt file corresponds to one annotated image.
    # ------------------------------------------------------------------------

    annotation_stems = {
        annotation_file.stem
        for annotation_file
        in ANNOTATIONS_DIR.glob("*.txt")
    }

    print(
        f"Annotated images found: "
        f"{len(annotation_stems)}"
    )

    features = []

    # ------------------------------------------------------------------------
    # Process only annotated images.
    # ------------------------------------------------------------------------

    for row in metadata_rows:

        filename = row.get(
            "FileName",
            "",
        ).strip()

        if not filename:
            continue

        image_stem = Path(
            filename
        ).stem

        if image_stem not in annotation_stems:
            continue

        feature = create_feature(row)

        if feature is None:

            print(
                f"WARNING: missing GPS: "
                f"{image_stem}"
            )

            continue

        features.append(feature)

    # ------------------------------------------------------------------------
    # GeoJSON
    # ------------------------------------------------------------------------

    geojson = {
        "type": "FeatureCollection",

        "name": "drone_positions",

        "crs": {
            "type": "name",
            "properties": {
                "name": GEOGRAPHIC_CRS,
            },
        },

        "properties": {
            "geographic_crs": GEOGRAPHIC_CRS,
            "metric_crs": METRIC_CRS,
        },

        "features": features,
    }

    # ------------------------------------------------------------------------
    # Write file
    # ------------------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            geojson,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 60)
    print("Drone positions GeoJSON created.")
    print("=" * 60)
    print(f"Images: {len(features)}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()