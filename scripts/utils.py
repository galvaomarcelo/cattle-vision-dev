import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------

def read_csv(file_path: Path) -> list[dict[str, str]]:
    """Read a CSV file and return a list of dictionaries."""
    with file_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv(
    file_path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    """Write a list of dictionaries to a CSV file."""
    if not rows and not fieldnames:
        raise ValueError("Cannot determine CSV columns from empty data.")

    if fieldnames is None:
        fieldnames = list(rows[0].keys())

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------

def read_json(file_path: Path) -> Any:
    """Read and decode a JSON file."""
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(
    file_path: Path,
    data: Any,
    indent: int = 2,
) -> None:
    """Write data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=indent,
            ensure_ascii=False,
        )


# ---------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------

def parse_float(value: Any) -> float | None:
    """Safely convert a value to float."""
    if value is None:
        return None

    if isinstance(value, float):
        return value

    if isinstance(value, int):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_datetime(value: Any) -> datetime | None:
    """
    Parse the DJI DateTimeOriginal format.

    Example:
        2026:09:04 13:39:36
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()

    if not text:
        return None

    formats = (
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    )

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


# ---------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------

def format_duration(seconds: float | None) -> str:
    """Format a duration in seconds as HH:MM:SS."""
    if seconds is None:
        return ""

    seconds = max(0, int(round(seconds)))

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"