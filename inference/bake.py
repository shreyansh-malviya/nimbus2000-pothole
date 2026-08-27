"""Pre-bake all local sessions into static assets for the Next.js frontend.

For each session under Data/sessions/<id>/ this writes:
  frontend/public/sessions/<id>/detections.json
  frontend/public/sessions/<id>/annotated/*.jpg
  frontend/public/sessions/<id>/raw/*.jpg
and a combined frontend/public/data/sessions.json index.

Usage:
    python inference/bake.py --conf 0.20 --enhance --augment
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nimbus.config import (  # noqa: E402
    BEST_MODEL, MODELS_DIR, SESSIONS_OUT, SESSIONS_INDEX, list_sessions,
)
from nimbus.analyze import analyze_session, load_metrics  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conf", type=float, default=0.20)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--model", default=str(BEST_MODEL))
    ap.add_argument("--enhance", action="store_true")
    ap.add_argument("--augment", action="store_true")
    ap.add_argument("--limit", type=int, default=0,
                    help="frames per session (0 = all); for quick validation")
    ap.add_argument("--session", default="",
                    help="bake only this session id (default: all)")
    args = ap.parse_args()

    from ultralytics import YOLO

    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}. Train first.")

    sessions = list_sessions()
    if not sessions:
        raise SystemExit("No sessions found under Data/sessions/")

    model = YOLO(str(model_path))
    metrics = load_metrics(MODELS_DIR)

    if args.session:
        sessions = [s for s in sessions if s[0] == args.session]
        if not sessions:
            raise SystemExit(f"Session '{args.session}' not found.")

    index = []
    for sid, frames_dir, manifest_path in sessions:
        print(f"\n=== baking {sid} ({frames_dir}) ===")
        out_dir = SESSIONS_OUT / sid

        def prog(done, total, potholes):
            if done % 20 == 0 or done == total:
                print(f"  {done}/{total} frames  potholes={potholes}")

        result = analyze_session(
            frames_dir, manifest_path, model,
            conf=args.conf, iou=args.iou, imgsz=args.imgsz,
            enhance=args.enhance, augment=args.augment,
            metrics=metrics, model_name=model_path.name,
            annotated_out_dir=out_dir / "annotated",
            raw_out_dir=None,  # raw copies are unused by the frontend — don't bake them
            want_base64=False,
            limit=args.limit,
            progress=prog,
        )
        # Rewrite annotated as a session-relative URL the frontend can load.
        for d in result["detections"]:
            d["annotated"] = f"sessions/{sid}/annotated/{d['frame_id']}"

        (out_dir).mkdir(parents=True, exist_ok=True)
        (out_dir / "detections.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

        s = result["summary"]
        index.append({
            "session_id": sid,
            "drone": result["drone"],
            "frames_total": s["frames_total"],
            "potholes_total": s["potholes_total"],
            "severity_counts": s["severity_counts"],
            "distance_covered_m": s["distance_covered_m"],
            "area_bounds": s["area_bounds"],
            "data": f"sessions/{sid}/detections.json",
        })
        print(f"  -> {out_dir/'detections.json'}  potholes={s['potholes_total']}")

    SESSIONS_INDEX.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_INDEX.write_text(json.dumps({
        "drone": "Nimbus2000",
        "model": {"weights": model_path.name, "metrics": metrics},
        "sessions": index,
    }, indent=2), encoding="utf-8")
    print(f"\nWrote index -> {SESSIONS_INDEX} ({len(index)} sessions)")


if __name__ == "__main__":
    main()
