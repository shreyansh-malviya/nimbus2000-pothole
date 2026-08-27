"""Nimbus2000 detection backend (FastAPI).

The Vercel-hosted frontend uploads a raw flight ZIP (frames + manifest.json)
DIRECTLY to this service — bypassing Vercel's 4.5 MB serverless body limit. We
extract it, run the trained YOLOv8 pothole detector, grade severity, draw
circled annotations, and return a lightweight JSON payload: the GPS flight path,
the detected potholes (severity + lat/lon), and each annotated frame as a base64
data URI. Temp files are deleted after each request.

Run locally:
    uvicorn backend.app:app --host 0.0.0.0 --port 8000
Deploy (Render/Fly/Railway): same command via the Procfile.
"""
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nimbus.config import BEST_MODEL, MODELS_DIR, DRONE_NAME  # noqa: E402
from nimbus.analyze import analyze_session, load_metrics  # noqa: E402

app = FastAPI(title="Nimbus2000 Pothole Detection API", version="1.0.0")

# CORS — allow the deployed frontend + local dev. Override with ALLOWED_ORIGINS
# (comma-separated) in production; "*" is fine for a public read-only detector.
_origins = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _origins == "*" else [o.strip() for o in _origins.split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single source of truth for the weights path (env override for deploys).
MODEL_PATH = Path(os.environ.get("MODEL_PATH", str(BEST_MODEL)))

# Lazy-loaded singleton model (heavy import; load once).
_MODEL = None
_METRICS = None


def get_model():
    global _MODEL, _METRICS
    if _MODEL is None:
        from ultralytics import YOLO
        if not MODEL_PATH.exists():
            raise HTTPException(503, f"Model weights not found at {MODEL_PATH}. Train first.")
        _MODEL = YOLO(str(MODEL_PATH))
        _METRICS = load_metrics(MODELS_DIR)
    return _MODEL, _METRICS


@app.get("/")
def root():
    return {"service": "Nimbus2000 Pothole Detection API", "drone": DRONE_NAME,
            "endpoints": ["/health", "/model", "POST /analyze"]}


@app.get("/health")
def health():
    return {"status": "ok", "model_present": MODEL_PATH.exists(), "model_path": str(MODEL_PATH)}


@app.get("/model")
def model_info():
    _, metrics = get_model()
    return {"weights": MODEL_PATH.name, "metrics": metrics}


def _find_frames_dir(root: Path) -> Path | None:
    """Locate the folder containing manifest.json inside an extracted zip."""
    for mf in root.rglob("manifest.json"):
        return mf.parent
    # Fallback: any dir with frame_*.jpg
    for p in root.rglob("frame_*.jpg"):
        return p.parent
    return None


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    conf: float = Query(0.20, ge=0.01, le=0.9),
    enhance: bool = Query(True),
    augment: bool = Query(False),
    imgsz: int = Query(640),
):
    """Accept a flight ZIP, return detections + base64 annotated frames."""
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Please upload a .zip of the flight frames + manifest.json")

    model, metrics = get_model()
    tmp = Path(tempfile.mkdtemp(prefix="nimbus_"))
    zip_path = tmp / "upload.zip"
    try:
        # Stream the (potentially large) upload to disk in chunks.
        with zip_path.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)

        extract_dir = tmp / "extracted"
        extract_dir.mkdir()
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            raise HTTPException(400, "Uploaded file is not a valid ZIP archive.")

        frames_dir = _find_frames_dir(extract_dir)
        if frames_dir is None:
            raise HTTPException(422, "Could not find manifest.json / frame_*.jpg in the ZIP.")

        manifest_path = frames_dir / "manifest.json"
        if not manifest_path.exists():
            raise HTTPException(422, "manifest.json not found next to the frames.")

        result = analyze_session(
            frames_dir, manifest_path, model,
            conf=conf, iou=0.5, imgsz=imgsz,
            enhance=enhance, augment=augment,
            metrics=metrics, model_name=MODEL_PATH.name,
            annotated_out_dir=None, raw_out_dir=None,
            want_base64=True,
        )
        return JSONResponse(result)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
