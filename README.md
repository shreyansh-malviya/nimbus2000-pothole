# Nimbus2000 — Aerial Pothole Detection & Severity Survey

A YOLOv8 pipeline that turns raw **Nimbus2000** drone road-survey footage (frames
+ GPS telemetry) into a geolocated, severity-graded pothole report — with a
Vercel-deployable dashboard and an "Analyze Footage" upload flow that runs the
model on new flights on demand.

![theme](https://img.shields.io/badge/theme-amber%2Fblack-ffc21f) ![stack](https://img.shields.io/badge/stack-Next.js%20%2B%20FastAPI%20%2B%20YOLOv8-111)

## Architecture

```
                        ┌────────────────────────────┐
  browser (Vercel) ─────┤  Next.js static dashboard   │
   • pre-baked sessions │  • session switcher          │
     load instantly     │  • severity pie / map / KPIs │
   • "Analyze Footage"  └───────────────┬──────────────┘
     uploads a flight ZIP               │  ZIP POSTed straight to the backend
     DIRECTLY to backend                │  (bypasses Vercel's 4.5 MB body limit)
     ───────────────────────────────────▼──────────────
                        ┌────────────────────────────┐
   Python backend ──────┤  FastAPI  /analyze          │
   (Render / Fly /      │  • unzip → YOLOv8 detect     │
    localhost:8000)     │  • severity grade + circle   │
                        │  • return JSON + base64 imgs │
                        └────────────────────────────┘
```

The heavy ML (PyTorch + Ultralytics) is far too large for Vercel serverless, so
the deployed frontend is **static** and talks to a separate Python service. The
browser uploads the raw ZIP straight to that service, so large flights aren't
capped by the host's request-body limit.

## What it does

1. **Trains** a YOLOv8 pothole detector on the public IVCNZ dataset (1,243 labeled
   images, single `pothole` class).
2. **Detects** potholes on drone frames, **circles** each one, and **grades
   severity** (`shallow`/`deep`/`severe`) via a documented monocular proxy
   (perspective-corrected size + interior-shadow depth cue + confidence).
3. **Geolocates** every detection using the flight `manifest.json` GPS.
4. **Multi-session**: any number of flights under `Data/sessions/<id>/`; the
   dashboard has a flight switcher, and "Analyze Footage" adds new ones live.

## Repo layout

```
nimbus/        shared engine (config, manifest, severity, drawing, analyze)
dataset/       download + train/val split -> data.yaml
training/      YOLOv8 fine-tune -> models/best.pt + metrics.json
inference/     bake.py: pre-render all sessions -> frontend/public
backend/       FastAPI /analyze service (Dockerfile, Procfile, requirements)
frontend/      Next.js dashboard (Vercel) — map, pie, gallery, upload
Data/sessions/ raw drone captures (frame_*.jpg + manifest.json) per flight
```

## Quick start (local, full pipeline)

```bash
pip install -r requirements.txt

# 1. training data (download once, then split)
python dataset/prepare.py

# 2. train (CPU-friendly)
python training/train.py --epochs 80 --imgsz 640      # -> models/best.pt

# 3. pre-bake the provided flights into the frontend
python inference/bake.py --enhance --augment          # -> frontend/public/...

# 4a. backend (detection API for the upload flow)
pip install -r backend/requirements.txt
uvicorn backend.app:app --host 0.0.0.0 --port 8000

# 4b. frontend
cd frontend && npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev            # http://localhost:3000
```

## Deploy

**Frontend → Vercel**
- Import the repo, set **Root Directory = `frontend`** (framework auto-detected).
- Add env var `NEXT_PUBLIC_API_URL` = your backend URL.
- The pre-baked sessions in `frontend/public` ship with the build, so the site
  shows real results immediately (backend only needed for new uploads).

**Backend → Render** (one click via [`render.yaml`](render.yaml)) or any Docker
host ([`backend/Dockerfile`](backend/Dockerfile)):
- `models/best.pt` is committed so the service has the weights.
- Set `ALLOWED_ORIGINS` to your Vercel URL to lock down CORS.

## Adding a new flight (data folder)

- **In the deployed app**: click **Analyze Footage**, drop a ZIP of
  `frame_*.jpg` + `manifest.json`. It's sent to the backend, detected, and
  rendered live as a new session.
- **To bake it into the static site**: drop the folder under
  `Data/sessions/<id>/`, run `python inference/bake.py --enhance`, and redeploy.

## Honest caveats

- The provided `manifest.json` is **GPS telemetry only** — the frames carry no
  pothole labels. They are the *inference target*; training uses the external
  IVCNZ dataset. Detection counts are real model output, not fabricated.
- **Severity is an ordinal proxy**, not measured depth (no depth sensor / scale
  reference). Upgrade path: monocular depth (Depth-Anything V2).
- Frames from flight `-665` are night-time and motion-blurred; `-863` are clearer
  daytime close-ups. CLAHE enhancement (`--enhance`) lifts detail from the dark
  frames honestly (no synthetic content).
