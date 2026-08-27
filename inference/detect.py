"""Run the trained pothole model over the Nimbus2000 flight frames.

For every frame:
  * detect potholes (YOLOv8),
  * classify each detection's severity (nimbus.severity),
  * draw circled annotations (nimbus.draw),
  * join GPS telemetry from the manifest.

Emits dashboard/public/data/detections.json + annotated frames.

Usage:
    python inference/detect.py --conf 0.25
"""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nimbus.config import (  # noqa: E402
    FRAMES_DIR, BEST_MODEL, MODELS_DIR, ANNOTATED_DIR, DETECTIONS_JSON,
    DASHBOARD_PUBLIC, DRONE_NAME, SEVERITY_LEVELS,
)
from nimbus.manifest import load_manifest  # noqa: E402
from nimbus import severity as sev  # noqa: E402
from nimbus.draw import draw_pothole  # noqa: E402


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--model", default=str(BEST_MODEL))
    args = ap.parse_args()

    from ultralytics import YOLO

    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}. Train first (training/train.py).")

    manifest = load_manifest()
    tele = manifest.by_frame

    ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
    raw_out = DASHBOARD_PUBLIC / "frames" / "raw"
    raw_out.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_path))

    frame_files = sorted(FRAMES_DIR.glob("frame_*.jpg"))
    if not frame_files:
        raise SystemExit(f"No frames under {FRAMES_DIR}")

    detections = []
    path_points = []
    severity_counts = {k: 0 for k in SEVERITY_LEVELS}
    conf_sum, conf_n = 0.0, 0
    pothole_total = 0

    for fp in frame_files:
        frame_id = fp.name
        img = cv2.imread(str(fp))
        if img is None:
            continue
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        t = tele.get(frame_id)
        if t:
            path_points.append({"frame_id": frame_id, "lat": t.latitude, "lon": t.longitude})

        res = model.predict(img, conf=args.conf, iou=args.iou, imgsz=args.imgsz,
                            device="cpu", verbose=False)[0]

        potholes = []
        for i, box in enumerate(res.boxes):
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            sres = sev.classify(gray, xyxy, conf, w, h)
            cx, cy, r = draw_pothole(img, xyxy, sres.level, conf)
            severity_counts[sres.level] += 1
            conf_sum += conf
            conf_n += 1
            pothole_total += 1
            potholes.append({
                "id": f"{frame_id}-{i}",
                "bbox": [round(v, 1) for v in xyxy],
                "cx": cx, "cy": cy, "r": r,
                "conf": round(conf, 4),
                "severity": sres.level,
                "score": sres.score,
                "size_ratio": sres.size_ratio,
                "darkness": sres.darkness,
            })

        # Save annotated frame (always) so the map/gallery can reference it.
        out_path = ANNOTATED_DIR / frame_id
        cv2.imwrite(str(out_path), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        # Also keep a downscaled raw copy for reference.
        cv2.imwrite(str(raw_out / frame_id), cv2.imread(str(fp)),
                    [cv2.IMWRITE_JPEG_QUALITY, 80])

        if potholes:
            detections.append({
                "frame_id": frame_id,
                "annotated": f"frames/annotated/{frame_id}",
                "raw": f"frames/raw/{frame_id}",
                "timestamp": t.video_timestamp if t else "",
                "img_w": w, "img_h": h,
                "gps": {
                    "lat": t.latitude, "lon": t.longitude, "alt": t.altitude_m,
                    "heading": t.heading_deg, "accuracy": t.accuracy_m,
                } if t else {},
                "potholes": potholes,
            })

    # Distance covered along the flight path
    dist = 0.0
    for a, b in zip(path_points, path_points[1:]):
        dist += haversine_m(a["lat"], a["lon"], b["lat"], b["lon"])

    lats = [p["lat"] for p in path_points]
    lons = [p["lon"] for p in path_points]

    # Load training metrics if present
    metrics = {"mAP50": 0.0, "mAP50_95": 0.0, "precision": 0.0, "recall": 0.0}
    mpath = MODELS_DIR / "metrics.json"
    if mpath.exists():
        m = json.loads(mpath.read_text())
        metrics = {
            "mAP50": m.get("mAP50", 0.0),
            "mAP50_95": m.get("mAP50_95", 0.0),
            "precision": m.get("precision", 0.0),
            "recall": m.get("recall", 0.0),
        }

    out = {
        "drone": DRONE_NAME,
        "session_id": manifest.session_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "model": {
            "weights": model_path.name,
            "imgsz": args.imgsz,
            "conf": args.conf,
            "metrics": metrics,
        },
        "summary": {
            "frames_total": len(frame_files),
            "frames_with_potholes": len(detections),
            "potholes_total": pothole_total,
            "severity_counts": severity_counts,
            "distance_covered_m": round(dist, 1),
            "avg_confidence": round(conf_sum / conf_n, 4) if conf_n else 0.0,
            "area_bounds": {
                "min_lat": min(lats), "max_lat": max(lats),
                "min_lon": min(lons), "max_lon": max(lons),
            } if lats else {},
        },
        "path": path_points,
        "detections": detections,
    }

    DETECTIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    DETECTIONS_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"frames={len(frame_files)} frames_with_potholes={len(detections)} "
          f"potholes={pothole_total}")
    print(f"severity={severity_counts}")
    print(f"distance={dist:.1f} m  avg_conf={out['summary']['avg_confidence']}")
    print(f"-> {DETECTIONS_JSON}")


if __name__ == "__main__":
    main()
