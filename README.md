<div align="center">

# 🛰️ Nimbus2000 — Aerial Pothole Detection & Severity Survey

**A drone-to-dashboard system that turns raw road footage into geolocated,
severity-graded pothole intelligence.**

![theme](https://img.shields.io/badge/theme-amber%2Fblack-ffc21f)
![model](https://img.shields.io/badge/model-YOLOv8n%20%E2%86%92%20ONNX-111)
![stack](https://img.shields.io/badge/stack-Next.js%20%2B%20FastAPI%20%2B%20ONNX%20Runtime-262)
![mAP50](https://img.shields.io/badge/mAP%4050-0.63-ff7a1a)
![hosting](https://img.shields.io/badge/hosting-Vercel%20%2B%20Render%20(free)-4ccf6a)

</div>

---

## Overview

**Nimbus2000** is an end-to-end pipeline for automated road-surface inspection.
A **custom Android app** flies with the drone, captures the road, and exports a
single geotagged **ZIP**. That ZIP is processed by a trained **YOLOv8** detector
that finds every pothole, **circles** it, **grades its severity**
(shallow / deep / severe), and pins it to a map using the flight's GPS track —
all surfaced in a clean, industrial analytics dashboard.

```
 ┌──────────────┐   flight ZIP    ┌───────────────────┐   detections   ┌──────────────────┐
 │  Nimbus2000  │  frames + GPS   │   Detection API    │  + annotated   │    Dashboard     │
 │  Android app │ ───(manifest)──▶│ FastAPI + YOLOv8   │────frames─────▶│ Next.js on Vercel│
 │ (with drone) │   .zip export   │  (ONNX Runtime)    │   JSON         │ map · pie · gallery│
 └──────────────┘                 └───────────────────┘                └──────────────────┘
```

---

## 1. Data-Preparation Android App 📱

A **purpose-built Android application** (`Data Prepration App.apk`, source in
[`Android app/`](Android%20app/)) is the front line of the system. It pairs with
the **drone** to collect flight data and package it for analysis:

- **Captures** the drone's road-facing video during a flight.
- **Samples frames** at a fixed interval (1 fps) as `frame_0000.jpg …`.
- **Tags every frame** with live telemetry — latitude, longitude, altitude,
  heading, GPS accuracy, and video timestamp.
- **Exports one ZIP** per flight session containing all frames plus a
  `manifest.json` telemetry file — the exact format this pipeline ingests.

Built as a cross-platform **React Native / Expo** app (`app.json`, `eas.json`),
distributed as a standalone APK. The operator flies the drone, hits *export*, and
hands the resulting ZIP to the dashboard's **"Analyze Footage"** button — no
manual labelling, no desktop tooling in the field.

> Each provided flight (`FL-20260827-665`, `FL-20260827-863`) is exactly one such
> ZIP produced by this app.

---

## 2. The AI — Models & Processing 🧠

### Detection model
- **Architecture:** [YOLOv8n](https://github.com/ultralytics/ultralytics)
  (Ultralytics) — a compact single-stage detector, fine-tuned from COCO-pretrained
  weights.
- **Training data:** the public **IVCNZ Pothole Dataset** — 1,243 hand-labelled
  road images (4,076 pothole instances), split 995 train / 248 val.
- **Results (validation):** **mAP@50 ≈ 0.63**, mAP@50-95 ≈ 0.31, precision ≈ 0.66,
  recall ≈ 0.56 — strong for a single-class detector on noisy, real-world footage.
- **Serving:** exported to **ONNX** and run with **ONNX Runtime** (no PyTorch at
  serving time) → ~160 MB RAM, ~0.25 s/frame on CPU, so it fits **free** hosting.

### Image enhancement
Drone frames are often night-time and motion-blurred. A **CLAHE** (Contrast
Limited Adaptive Histogram Equalization) pass on the luminance channel lifts real
detail out of dark frames before detection — improving recall honestly, with no
synthetic content added.

### Severity grading (monocular proxy)
A single RGB frame has no true depth, so severity is a **documented, ordinal
estimate** — not a fabricated measurement. Each detection is scored by fusing:

| Cue | Weight | Intuition |
|-----|--------|-----------|
| Perspective-corrected **size** | 0.55 | bigger defect (adjusted for distance down the road) = worse |
| Interior **shadow / darkness** | 0.35 | deep potholes trap shadow → darker interior vs. surround |
| Detection **confidence** | 0.10 | tie-breaker |

The composite score maps to **`shallow` → `deep` → `severe`**. Thresholds live in
[`nimbus/severity.py`](nimbus/severity.py) and are easy to tune. *(Upgrade path:
a monocular depth model such as Depth-Anything V2 for metric depth.)*

---

## 3. The Dashboard 📊

A flat, industrial **yellow / orange / black** interface (Next.js 14 +
TypeScript) — deliberately not "AI-generic": no glow, no neon, solid ink and hard
edges.

- **Interactive map** (Leaflet, dark basemap) — the dashed flight path plus every
  pothole pinned and colour-coded by severity.
- **Severity pie/donut** + KPI strip (potholes, route length, avg confidence,
  density, model mAP).
- **Annotated frame gallery** — each detection circled with a severity label;
  click for a detail view with full GPS, per-pothole score bars, and a map link.
- **Multi-session switcher** — compare flights; uploaded flights appear as a
  **LIVE** session.
- **"Analyze Footage"** — drop a new ZIP; it's sent to the backend and rendered
  live without a page reload.

---

## 4. Architecture & Deployment ☁️

Free, no-credit-card hosting:

| Layer | Tech | Host |
|-------|------|------|
| Frontend | Next.js (static) | **Vercel** (free) |
| Backend  | FastAPI + ONNX Runtime | **Render** (free 512 MB tier) |
| Keep-alive | GitHub Actions cron | [`nimbus2000-pinger`](https://github.com/shreyansh-malviya/nimbus2000-pinger) |

The browser uploads the (large) flight ZIP **directly** to the backend, bypassing
Vercel's 4.5 MB request limit. Full instructions in **[`DEPLOY.md`](DEPLOY.md)**.

### Repo layout
```
Android app/     data-collection Android app (Expo/React Native) + the .apk
nimbus/          shared engine — config, manifest, severity, drawing, ONNX detector, analyze
dataset/         IVCNZ download + train/val split -> data.yaml
training/        YOLOv8 fine-tune -> models/best.pt (+ ONNX export)
inference/       bake.py — pre-render all flights into the frontend
backend/         FastAPI /analyze service (ONNX) — Dockerfile, Render config
frontend/        Next.js dashboard (Vercel) — map, pie, gallery, upload
Data/sessions/   raw drone captures (frame_*.jpg + manifest.json) per flight
models/          best.pt (training), best.onnx (serving), metrics.json
```

### Run it locally
```bash
pip install -r requirements.txt
python dataset/prepare.py                                   # training data
python training/train.py --epochs 80 --imgsz 640            # -> models/best.pt
python -c "from ultralytics import YOLO; YOLO('models/best.pt').export(format='onnx', imgsz=640, opset=12, simplify=True)"
python inference/bake.py --model models/best.onnx --conf 0.35 --enhance   # static flights

pip install -r backend/requirements.txt
uvicorn backend.app:app --port 8000                         # backend
cd frontend && npm install && npm run dev                   # http://localhost:3000
```

---

## 5. 🚀 Future Scope & Expansion

Nimbus2000 is a foundation for continuous, automated infrastructure monitoring.
Planned directions:

- **On-device real-time detection** — run the ONNX model inside the Android app
  for live, in-flight pothole alerts and instant driver warnings, streaming
  results to the server as the drone flies rather than after landing.
- **Multi-class road-damage detection** — extend beyond potholes to cracks,
  ravelling, faded lane markings, and damaged/obscured signage, turning the tool
  into a full road-health scanner.
- **Automated repair workflows** — wire the dashboard into municipal/works
  systems so `severe` clusters auto-generate geotagged repair work-orders,
  prioritised by severity and traffic density.
- **Metric depth & dimensions** — add a monocular-depth model (e.g.
  Depth-Anything V2) to convert the severity proxy into real depth/volume
  estimates for cost forecasting.
- **City-scale crowdsourcing** — a public build of the app lets everyday
  commuters passively map road conditions, keeping a live, city-wide condition
  database continuously fresh.
- **Fleet & scheduling** — multi-drone flight planning with coverage tracking and
  historical trend analysis to watch road decay over time.

---

<div align="center">
<sub>Nimbus2000 · drone-based road survey · YOLOv8 → ONNX · built for the field</sub>
</div>
