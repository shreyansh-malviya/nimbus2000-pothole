"""ONNX Runtime YOLOv8 detector — torch-free, small-footprint inference.

Replaces Ultralytics/PyTorch at serving time so the backend fits free 512MB
hosts. Loads a YOLOv8 ONNX export and returns pothole boxes as an (N,5) array
of [x1, y1, x2, y2, conf] in the ORIGINAL image's pixel coordinates.
"""
from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np
import onnxruntime as ort


class OnnxDetector:
    def __init__(self, model_path: str | Path, imgsz: int = 640):
        self.imgsz = imgsz
        so = ort.SessionOptions()
        so.intra_op_num_threads = 2  # keep memory/CPU modest on free tiers
        self.session = ort.InferenceSession(
            str(model_path), sess_options=so, providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name

    def _letterbox(self, img, new=640):
        """Resize keeping aspect ratio, pad to a square. Returns (padded, scale, (dx,dy))."""
        h, w = img.shape[:2]
        scale = min(new / w, new / h)
        nw, nh = int(round(w * scale)), int(round(h * scale))
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((new, new, 3), 114, dtype=np.uint8)
        dx, dy = (new - nw) // 2, (new - nh) // 2
        canvas[dy:dy + nh, dx:dx + nw] = resized
        return canvas, scale, (dx, dy)

    def detect(self, img_bgr, conf=0.20, iou=0.5, imgsz=None) -> np.ndarray:
        imgsz = imgsz or self.imgsz
        h0, w0 = img_bgr.shape[:2]
        padded, scale, (dx, dy) = self._letterbox(img_bgr, imgsz)

        blob = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))[None]  # NCHW

        out = self.session.run(None, {self.input_name: blob})[0]  # [1, 4+nc, 8400]
        out = np.squeeze(out, 0).T                                 # [8400, 4+nc]

        boxes_xywh = out[:, :4]
        scores_all = out[:, 4:]
        cls_ids = np.argmax(scores_all, axis=1)
        scores = scores_all[np.arange(scores_all.shape[0]), cls_ids]

        keep = scores >= conf
        if not np.any(keep):
            return np.empty((0, 5), dtype=np.float32)
        boxes_xywh, scores = boxes_xywh[keep], scores[keep]

        # xywh (letterboxed space) -> xyxy in original image coords
        cx, cy, bw, bh = boxes_xywh.T
        x1 = (cx - bw / 2 - dx) / scale
        y1 = (cy - bh / 2 - dy) / scale
        x2 = (cx + bw / 2 - dx) / scale
        y2 = (cy + bh / 2 - dy) / scale
        x1 = np.clip(x1, 0, w0); y1 = np.clip(y1, 0, h0)
        x2 = np.clip(x2, 0, w0); y2 = np.clip(y2, 0, h0)

        # NMS (OpenCV expects [x, y, w, h])
        rects = np.stack([x1, y1, x2 - x1, y2 - y1], axis=1).tolist()
        idxs = cv2.dnn.NMSBoxes(rects, scores.tolist(), conf, iou)
        if len(idxs) == 0:
            return np.empty((0, 5), dtype=np.float32)
        idxs = np.array(idxs).flatten()

        return np.stack([x1[idxs], y1[idxs], x2[idxs], y2[idxs], scores[idxs]], axis=1).astype(np.float32)
