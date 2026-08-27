"""Central paths and constants for the Nimbus2000 pipeline."""
from pathlib import Path

# Project root = parent of this file's parent (nimbus/ -> project root)
ROOT = Path(__file__).resolve().parent.parent

# Multi-session drone captures. Each session folder holds frame_*.jpg + manifest.json.
SESSIONS_DIR = ROOT / "Data" / "sessions"

# Legacy single-session location (first provided flight), kept as a fallback.
LEGACY_FRAMES_DIR = ROOT / "Data" / "extracted"

# Labeled training dataset (downloaded/prepared separately)
DATASET_DIR = ROOT / "dataset" / "pothole"
DATASET_YAML = DATASET_DIR / "data.yaml"

# Trained model
MODELS_DIR = ROOT / "models"
BEST_MODEL = MODELS_DIR / "best.pt"
ONNX_MODEL = MODELS_DIR / "best.onnx"

# Pre-baked static outputs consumed by the frontend (Next.js /public).
FRONTEND_PUBLIC = ROOT / "frontend" / "public"
SESSIONS_OUT = FRONTEND_PUBLIC / "sessions"          # per-session detections + frames
SESSIONS_INDEX = FRONTEND_PUBLIC / "data" / "sessions.json"

# Drone / flight identity
DRONE_NAME = "Nimbus2000"

# Severity categories (ordered by increasing seriousness)
SEVERITY_LEVELS = ["shallow", "deep", "severe"]

# Theme-consistent colors for drawing (BGR for OpenCV). No neon/glow — flat.
SEVERITY_BGR = {
    "shallow": (30, 200, 245),   # amber/yellow
    "deep": (30, 130, 240),      # orange
    "severe": (40, 40, 210),     # deep red-orange
}


def list_sessions():
    """Return sorted list of (session_id, frames_dir, manifest_path) for every
    session folder that contains a manifest.json."""
    out = []
    if SESSIONS_DIR.exists():
        for d in sorted(SESSIONS_DIR.iterdir()):
            if d.is_dir() and (d / "manifest.json").exists():
                out.append((d.name, d, d / "manifest.json"))
    return out
