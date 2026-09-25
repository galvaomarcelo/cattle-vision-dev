from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "images"

print("Project:", PROJECT_ROOT)
print("Images:", IMAGE_DIR)

images = list(IMAGE_DIR.glob("*.JPG"))

print(f"Found {len(images)} images")

for image in images:
    print(image.name)