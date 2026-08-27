"""Fine-tune YOLOv8 for pothole detection (CPU-friendly).

Starts from COCO-pretrained yolov8n, trains on the IVCNZ pothole split, and
copies the best checkpoint to models/best.pt. Prints final validation metrics.

Usage:
    python training/train.py                 # default: 80 epochs, imgsz 640
    python training/train.py --epochs 40 --imgsz 512 --model yolov8n.pt
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nimbus.config import DATASET_YAML, MODELS_DIR, BEST_MODEL  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--patience", type=int, default=15)
    ap.add_argument("--name", default="pothole_yolov8n")
    args = ap.parse_args()

    from ultralytics import YOLO

    if not DATASET_YAML.exists():
        raise SystemExit(f"Missing {DATASET_YAML}. Run dataset/prepare.py first.")

    model = YOLO(args.model)
    results = model.train(
        data=str(DATASET_YAML),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device="cpu",
        cache="ram",           # keep decoded imgs in RAM — big CPU speedup
        workers=4,
        project=str(ROOT / "training" / "runs"),
        name=args.name,
        exist_ok=True,
        # augmentation tuned for road scenes: keep geometry sane, vary lighting
        hsv_h=0.015, hsv_s=0.5, hsv_v=0.5,
        degrees=0.0, translate=0.08, scale=0.4, shear=0.0,
        fliplr=0.5, flipud=0.0, mosaic=1.0, close_mosaic=10,
        optimizer="auto", seed=42, verbose=True,
    )

    # Locate best.pt from the run and copy to models/best.pt
    save_dir = Path(results.save_dir)
    best = save_dir / "weights" / "best.pt"
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if best.exists():
        shutil.copy2(best, BEST_MODEL)
        print(f"\nCopied best checkpoint -> {BEST_MODEL}")

    # Final validation metrics
    metrics = model.val(data=str(DATASET_YAML), device="cpu", imgsz=args.imgsz)
    box = metrics.box
    print("\n=== FINAL VALIDATION METRICS ===")
    print(f"mAP50    : {box.map50:.4f}")
    print(f"mAP50-95 : {box.map:.4f}")
    print(f"precision: {box.mp:.4f}")
    print(f"recall   : {box.mr:.4f}")

    # Persist metrics as JSON next to the model for the dashboard/build.
    import json
    (MODELS_DIR / "metrics.json").write_text(
        json.dumps(
            {
                "mAP50": round(float(box.map50), 4),
                "mAP50_95": round(float(box.map), 4),
                "precision": round(float(box.mp), 4),
                "recall": round(float(box.mr), 4),
                "imgsz": args.imgsz,
                "epochs": args.epochs,
                "model": args.model,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {MODELS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
