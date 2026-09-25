# 🔄 Development Workflow

The project is organized as a reproducible pipeline. Each stage has a specific purpose and produces the input required by the next stage.

The complete workflow is:

```text
1. Collect drone images
        │
        ▼
2. Extract image metadata
        │
        ▼
3. Process and analyze the dataset
        │
        ▼
4. Annotate cattle with CVAT
        │
        ▼
5. Prepare YOLO dataset
        │
        ▼
6. Inspect annotations
        │
        ▼
7. Train YOLO model
        │
        ▼
8. Predict on validation images
        │
        ▼
9. Evaluate and inspect results
        │
        ▼
10. Geolocate detections
        │
        ▼
11. Visualize results in QGIS
```

The important principle is that **each stage is explicit**. The project should be reproducible without having to remember what was done manually.

---

## 1. 🚁 Collect Drone Images

Images are collected using the DJI Air 3S.

The original images are stored locally under:

```text
data/raw/images/
```

The raw images are intentionally **not committed to GitHub** because they are large.

Each image should retain its original DJI metadata because the geolocation pipeline depends on information such as:

* GPS position
* altitude
* gimbal orientation
* focal length
* image dimensions
* camera information
* capture date/time

---

## 2. 📋 Extract Metadata

The first processing step extracts the relevant EXIF/XMP metadata from the drone images.

Script:

```text
scripts/extract_metadata.py
```

Run:

```powershell
python scripts/extract_metadata.py
```

Main outputs:

```text
data/metadata/
├── images_metadata.csv
└── images_metadata.json
```

The CSV version is used as the main tabular input for subsequent processing.

Conceptually:

```text
DJI images
    ↓
extract_metadata.py
    ↓
images_metadata.csv
images_metadata.json
```

---

## 3. 🧹 Process the Dataset

The raw metadata is cleaned and additional derived information is calculated.

Script:

```text
scripts/process_dataset.py
```

Run:

```powershell
python scripts/process_dataset.py
```

Main outputs:

```text
data/metadata/
├── dataset_clean.csv
└── dataset_clean.json
```

This stage prepares information such as:

* camera orientation
* off-nadir angle
* vertical field of view
* ground footprint
* approximate GSD
* normalized metadata fields

The resulting `dataset_clean.csv` becomes the main dataset description used by later analysis.

---

## 4. ✈️ Analyze Flights

The images are grouped according to their flight/capture characteristics.

Script:

```text
scripts/analyze_flights.py
```

Run:

```powershell
python scripts/analyze_flights.py
```

Output:

```text
data/metadata/flight_groups_summary.csv
```

The flight grouping is important for machine-learning evaluation.

Instead of randomly distributing individual images between training and validation, images from complete flight groups are kept together.

This reduces the possibility of having almost identical images from the same flight in both datasets.

---

# 5. 🏷️ Annotate Cattle

Cattle are manually annotated using **CVAT**.

The annotations follow the guidelines documented in:

```text
documents/annotation_guidelines.md
```

The current dataset uses one class:

```text
0 = cattle
```

The annotation process produces YOLO-format label files.

Conceptually:

```text
Drone images
      +
CVAT annotations
      │
      ▼
YOLO annotations
```

The original CVAT project/export is kept outside the Git repository.

---

# 6. 📦 Prepare the YOLO Dataset

After annotation, the images and YOLO labels must be organized into the training and validation structure.

Script:

```text
scripts/yolo_training/prepare_yolo_dataset.py
```

Run:

```powershell
python scripts/yolo_training/prepare_yolo_dataset.py
```

The script:

1. Reads the cleaned dataset metadata
2. Identifies the flight group of each image
3. Applies the predefined train/validation flight groups
4. Copies the images
5. Copies the YOLO labels
6. Creates the required directory structure
7. Creates `data.yaml`
8. Checks for missing annotations

The generated structure is:

```text
data/yolo/cattle/
├── images/
│   ├── train/
│   └── val/
│
├── labels/
│   ├── train/
│   └── val/
│
└── data.yaml
```

For the current dataset:

```text
Training:   22 images / 951 cattle
Validation:  8 images / 120 cattle
```

---

# 7. 👀 Inspect YOLO Annotations

Before training, the annotations should be visually inspected.

Script:

```text
scripts/yolo_training/visualize_yolo_annotations.py
```

Run:

```powershell
python scripts/yolo_training/visualize_yolo_annotations.py
```

This creates visualization images showing the bounding boxes over the original images.

The purpose is to catch problems such as:

* incorrect bounding boxes
* missing cattle
* incorrect class IDs
* malformed YOLO labels
* boxes that do not correspond to cattle
* problems caused by the CVAT → YOLO conversion

This step should happen **before training**.

```text
YOLO dataset
     ↓
visualize_yolo_annotations.py
     ↓
Human inspection
     ↓
Training
```

---

# 8. 🧠 Train the YOLO Model

Once the dataset has been checked, the detector can be trained.

Script:

```text
scripts/yolo_training/train_yolo.py
```

Run:

```powershell
python scripts/yolo_training/train_yolo.py
```

The training script defines parameters such as:

```text
Model
Image size
Epochs
Batch size
Workers
Experiment name
```

Training results are stored under:

```text
runs/detect/
```

A typical experiment contains:

```text
runs/detect/<experiment>/
├── weights/
│   ├── best.pt
│   └── last.pt
├── results.csv
├── results.png
├── confusion_matrix.png
└── ...
```

The most important model for subsequent prediction is normally:

```text
weights/best.pt
```

Model weights are intentionally excluded from GitHub.

---

# 9. 🔮 Predict on Validation Images

After training, the model is used to generate predictions on images that were **not used during training**.

Script:

```text
scripts/yolo_training/predict_yolo_validation.py
```

The script uses the trained:

```text
best.pt
```

and generates prediction images with bounding boxes.

Conceptually:

```text
Validation images
        +
      best.pt
        │
        ▼
predict_yolo_validation.py
        │
        ▼
Prediction images
```

The predictions are stored under:

```text
data/inspection/yolo_predictions/
```

This allows visual inspection of:

* correctly detected cattle
* missed cattle
* false positives
* small/distant cattle
* crowded groups
* difficult terrain/backgrounds

---

# 10. 📊 Evaluate the Model

Model performance is evaluated using the YOLO validation metrics.

Important metrics include:

```text
Precision
Recall
mAP50
mAP50-95
```

However, numerical metrics alone are not sufficient.

The project therefore combines:

```text
Quantitative evaluation
        +
Visual inspection
        ↓
Error analysis
```

For example, a model can have reasonable mAP while still failing systematically on very small or distant cattle.

The development process therefore treats prediction visualization as an important part of model evaluation.

---

# 11. 📍 Geolocate Detections

Once cattle detections are available, their image coordinates can be converted into approximate geographic coordinates.

Script:

```text
scripts/geolocate_annotations.py
```

The current geolocation pipeline is:

```text
YOLO bounding box
        │
        ▼
Bounding-box center
        │
        ▼
Camera ray
        │
        ▼
Camera / gimbal orientation
        │
        ▼
NED
        │
        ▼
ENU
        │
        ▼
Ground intersection
        │
        ▼
Projected coordinates
        │
        ▼
WGS84 / EPSG:4326
        │
        ▼
GeoJSON
```

The process combines the detection with the corresponding drone metadata.

This is the bridge between the **computer vision** and **geospatial** parts of the project.

---

# 12. 🗺️ Inspect in QGIS

The geolocation results can be loaded into **QGIS** for visual inspection.

Typical workflow:

```text
Drone image
      │
      ▼
YOLO detection
      │
      ▼
Geolocation
      │
      ▼
GeoJSON
      │
      ▼
QGIS
```

This makes it possible to compare:

* drone position
* detected cattle
* estimated cattle positions
* farm boundaries
* pasture boundaries
* roads
* streams
* terrain
* DEM

QGIS is currently an important validation tool because it provides an intuitive way to determine whether the calculated positions are spatially plausible.

---

# 🧩 Complete Command Reference

For a new development session, the basic pipeline is:

```powershell
# 1. Extract metadata
python scripts/extract_metadata.py

# 2. Process metadata
python scripts/process_dataset.py

# 3. Analyze flights
python scripts/analyze_flights.py

# 4. Prepare YOLO dataset
python scripts/yolo_training/prepare_yolo_dataset.py

# 5. Inspect annotations
python scripts/yolo_training/visualize_yolo_annotations.py

# 6. Train model
python scripts/yolo_training/train_yolo.py

# 7. Predict on validation images
python scripts/yolo_training/predict_yolo_validation.py

# 8. Geolocate detections
python scripts/geolocate_annotations.py
```

Not every stage needs to be executed every time.

For example, if the metadata and YOLO dataset have not changed, there is no need to repeat the preparation stages before every training run.

---

# 🧭 Practical Development Cycle

During normal experimentation, the most common cycle is:

```text
        ┌──────────────────────────────┐
        │                              │
        ▼                              │
   Prepare data                        │
        │                              │
        ▼                              │
   Annotate / modify annotations       │
        │                              │
        ▼                              │
   Prepare YOLO dataset                │
        │                              │
        ▼                              │
   Inspect annotations                 │
        │                              │
        ▼                              │
   Train model                         │
        │                              │
        ▼                              │
   Predict validation images           │
        │                              │
        ▼                              │
   Evaluate + inspect errors           │
        │                              │
        ▼                              │
   Modify data / approach ─────────────┘
```

The geospatial branch can then be explored independently:

```text
YOLO detections
       │
       ▼
Geolocation
       │
       ▼
GeoJSON
       │
       ▼
QGIS
       │
       ▼
Spatial analysis
```

This separation is intentional: **object detection and geolocation are related, but they are different technical problems and can be developed and validated independently.**
