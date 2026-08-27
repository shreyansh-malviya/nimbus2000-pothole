"""Central paths and constants for the Nimbus2000 pipeline."""
from pathlib import Path

# Project root = parent of this file's parent (nimbus/ -> project root)
ROOT = Path(__file__).resolve().parent.parent

# Raw drone capture provided by the user (Nimbus2000 flight FL-20260827-665)
FRAMES_DIR = ROOT / "Data" / "extracted"
MANIFEST_PATH = FRAMES_DIR / "manifest.json"

# Labeled training dataset (downloaded/prepared separately)
DATASET_DIR = ROOT / "dataset" / "pothole"
DATASET_YAML = DATASET_DIR / "data.yaml"

# Trained model
MODELS_DIR = ROOT / "models"
BEST_MODEL = MODELS_DIR / "best.pt"

# Inference outputs consumed by the dashboard (kept in dashboard/public so the
# static site can load them without a bundler copy step).
DASHBOARD_PUBLIC = ROOT / "dashboard" / "public"
ANNOTATED_DIR = DASHBOARD_PUBLIC / "frames" / "annotated"
DETECTIONS_JSON = DASHBOARD_PUBLIC / "data" / "detections.json"

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
