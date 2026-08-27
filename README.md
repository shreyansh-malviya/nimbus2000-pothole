# Nimbus2000 — Aerial Pothole Detection & Severity Survey

A YOLOv8 pipeline that turns raw **Nimbus2000** drone road-survey frames (+ GPS
telemetry) into a geolocated, severity-graded pothole report with an
analytics dashboard.

![theme: yellow / orange / black](https://img.shields.io/badge/theme-amber%2Fblack-ffc21f)

## What it does

1. **Trains** a YOLOv8 pothole detector on the public IVCNZ pothole dataset
   (1,243 labeled images, single `pothole` class).
2. **Runs inference** on the 170 Nimbus2000 flight frames — circling every
   detected pothole and joining each frame to its GPS fix from `manifest.json`.
3. **Grades severity** — `shallow` / `deep` / `severe` — using a documented
   monocular proxy (perspective-corrected size + interior-shadow depth cue +
   confidence). See [`nimbus/severity.py`](nimbus/severity.py).
4. **Dashboard** — a flat industrial (yellow/orange/black, no glow) web app with
   a live map of pothole locations, a severity pie chart, KPIs, and an annotated
   frame gallery with per-pothole detail.

## Data

- Provided: `Data/FL-20260827-665_frames.zip` → 170 JPGs + `manifest.json`
  (GPS/altitude/heading per frame). **No pothole labels** — these are the
  inference target, not training data.
- Training data (downloaded): IVCNZ pothole dataset (MIT).

## Quick start

```bash
# 1. Python deps
pip install -r requirements.txt

# 2. Prepare training data (downloads + splits)
curl -L -o dataset/downloads/pothole_ivcnz.zip \
  https://github.com/jaygala24/pothole-detection/releases/download/v1.0.0/Pothole.Dataset.IVCNZ.zip
# unzip into dataset/raw/, then:
python dataset/prepare.py

# 3. Train (CPU-friendly)
python training/train.py --epochs 80 --imgsz 640

# 4. Run detection over the Nimbus2000 frames
python inference/detect.py --conf 0.25

# 5. Dashboard
cd dashboard && npm install && npm run dev
```

## Layout

```
nimbus/        shared modules (config, manifest, severity, drawing)
dataset/       download + train/val split -> data.yaml
training/      YOLOv8 fine-tune -> models/best.pt + metrics.json
inference/     detect over flight frames -> dashboard/public/data/detections.json
dashboard/     Vite + React + Leaflet + Recharts UI
```

## Severity — honest caveat

A single RGB frame has no true depth, so severity here is an **ordinal proxy**,
not a metric depth. It fuses relative (perspective-corrected) size with an
interior-darkness shadow cue and detection confidence. This is stated plainly in
the code and UI; upgrading to a monocular depth model (e.g. Depth-Anything V2) is
the path to metric depth.
