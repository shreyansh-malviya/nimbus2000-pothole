"""Core pothole-analysis engine — shared by the FastAPI backend and the static
pre-baker so both produce identical results.

analyze_session() runs YOLOv8 over a folder of drone frames, grades severity,
draws circled annotations, and joins GPS from the flight manifest. Annotated
frames are either written to disk (baker) or returned as base64 data URIs
(backend response), controlled by `annotated_out_dir` / `want_base64`.
"""
from __future__ import annotations

import base64
import math
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from .config import SEVERITY_LEVELS, DRONE_NAME
from .manifest import load_manifest
from . import severity as sev
from .draw import draw_pothole


def enhance_frame(img):
    """CLAHE on the L channel — lifts detail out of dark, low-contrast night
    frames without blowing out highlights. Improves recall honestly."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _fit_width(img, max_w):
    """Downscale to at most max_w px wide (keep aspect). No upscale."""
    if not max_w or img.shape[1] <= max_w:
        return img
    scale = max_w / float(img.shape[1])
    return cv2.resize(img, (max_w, int(round(img.shape[0] * scale))), interpolation=cv2.INTER_AREA)


def _jpg_data_uri(img, quality=80, max_w=900):
    ok, buf = cv2.imencode(".jpg", _fit_width(img, max_w), [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def analyze_session(
    frames_dir: Path,
    manifest_path: Path,
    model,
    *,
    conf: float = 0.20,
    iou: float = 0.5,
    imgsz: int = 640,
    enhance: bool = True,
    augment: bool = False,
    metrics: dict | None = None,
    model_name: str = "best.pt",
    annotated_out_dir: Path | None = None,
    raw_out_dir: Path | None = None,
    want_base64: bool = False,
    limit: int = 0,
    progress=None,
) -> dict:
    """Analyze every frame in `frames_dir`. Returns a detections dict.

    If `annotated_out_dir` is given, annotated JPGs are written there and each
    detection's `annotated` is a relative filename. If `want_base64`, each
    detection also carries an `annotated_uri` data URI (used by the API response
    so the frontend needs no separate image host).
    """
    frames_dir = Path(frames_dir)
    manifest = load_manifest(manifest_path)
    tele = manifest.by_frame

    if annotated_out_dir:
        annotated_out_dir = Path(annotated_out_dir)
        annotated_out_dir.mkdir(parents=True, exist_ok=True)
    if raw_out_dir:
        raw_out_dir = Path(raw_out_dir)
        raw_out_dir.mkdir(parents=True, exist_ok=True)

    frame_files = sorted(frames_dir.glob("frame_*.jpg"))
    if not frame_files:
        frame_files = sorted(p for p in frames_dir.glob("*.jpg"))
    if limit > 0:
        frame_files = frame_files[:limit]

    detections, path_points = [], []
    severity_counts = {k: 0 for k in SEVERITY_LEVELS}
    conf_sum = conf_n = pothole_total = 0

    for idx, fp in enumerate(frame_files):
        frame_id = fp.name
        orig = cv2.imread(str(fp))
        if orig is None:
            continue
        h, w = orig.shape[:2]
        img = enhance_frame(orig) if enhance else orig.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        t = tele.get(frame_id)
        if t:
            path_points.append({"frame_id": frame_id, "lat": t.latitude, "lon": t.longitude})

        res = model.predict(img, conf=conf, iou=iou, imgsz=imgsz,
                            augment=augment, device="cpu", verbose=False)[0]

        potholes = []
        for i, box in enumerate(res.boxes):
            xyxy = box.xyxy[0].tolist()
            c = float(box.conf[0])
            sres = sev.classify(gray, xyxy, c, w, h)
            cx, cy, r = draw_pothole(img, xyxy, sres.level, c)
            severity_counts[sres.level] += 1
            conf_sum += c
            conf_n += 1
            pothole_total += 1
            potholes.append({
                "id": f"{frame_id}-{i}",
                "bbox": [round(v, 1) for v in xyxy],
                "cx": cx, "cy": cy, "r": r,
                "conf": round(c, 4),
                "severity": sres.level,
                "score": sres.score,
                "size_ratio": sres.size_ratio,
                "darkness": sres.darkness,
            })

        # Only frames WITH potholes are displayed (gallery + map markers). Skip
        # image output for empty frames entirely — the full route is preserved in
        # `path`. Annotated frames are downscaled for the web to keep the static
        # bundle / API response small.
        if potholes:
            entry = {
                "frame_id": frame_id,
                "timestamp": t.video_timestamp if t else "",
                "img_w": w, "img_h": h,
                "gps": {
                    "lat": t.latitude, "lon": t.longitude, "alt": t.altitude_m,
                    "heading": t.heading_deg, "accuracy": t.accuracy_m,
                } if t else {},
                "potholes": potholes,
            }
            if annotated_out_dir:
                cv2.imwrite(str(annotated_out_dir / frame_id), _fit_width(img, 900),
                            [cv2.IMWRITE_JPEG_QUALITY, 82])
                entry["annotated"] = f"annotated/{frame_id}"
            if raw_out_dir:
                cv2.imwrite(str(raw_out_dir / frame_id), _fit_width(orig, 900),
                            [cv2.IMWRITE_JPEG_QUALITY, 80])
                entry["raw"] = f"raw/{frame_id}"
            if want_base64:
                entry["annotated_uri"] = _jpg_data_uri(img)
            detections.append(entry)

        if progress:
            progress(idx + 1, len(frame_files), pothole_total)

    dist = 0.0
    for a, b in zip(path_points, path_points[1:]):
        dist += _haversine_m(a["lat"], a["lon"], b["lat"], b["lon"])

    lats = [p["lat"] for p in path_points]
    lons = [p["lon"] for p in path_points]

    return {
        "drone": DRONE_NAME,
        "session_id": manifest.session_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "model": {
            "weights": model_name,
            "imgsz": imgsz,
            "conf": conf,
            "metrics": metrics or {"mAP50": 0.0, "mAP50_95": 0.0, "precision": 0.0, "recall": 0.0},
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


def load_metrics(models_dir: Path) -> dict:
    import json
    mpath = Path(models_dir) / "metrics.json"
    if mpath.exists():
        m = json.loads(mpath.read_text())
        return {
            "mAP50": m.get("mAP50", 0.0),
            "mAP50_95": m.get("mAP50_95", 0.0),
            "precision": m.get("precision", 0.0),
            "recall": m.get("recall", 0.0),
        }
    return {"mAP50": 0.0, "mAP50_95": 0.0, "precision": 0.0, "recall": 0.0}
