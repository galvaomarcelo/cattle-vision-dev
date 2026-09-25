from pathlib import Path
import json
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "images"

image = sorted(IMAGE_DIR.glob("*.JPG"))[0]

print(f"Reading: {image.name}")
print()

result = subprocess.run(
    ["exiftool", "-j", "-n", str(image)],
    capture_output=True,
    text=True,
    check=True
)

metadata = json.loads(result.stdout)[0]

print(f"Number of metadata fields: {len(metadata)}")
print()

for key, value in metadata.items():
    print(f"{key}: {value}")