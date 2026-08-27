"""Flat annotation drawing — circle each pothole, label severity. No glow."""
import cv2
import numpy as np

from .config import SEVERITY_BGR


def _rounded_label(img, text, org, bg_bgr, fg_bgr=(15, 15, 15)):
    """Draw a small solid label chip (flat, no shadow/glow)."""
    x, y = org
    font = cv2.FONT_HERSHEY_DUPLEX
    scale = max(0.5, img.shape[1] / 1600.0)
    thick = max(1, int(scale * 1.4))
    (tw, th), base = cv2.getTextSize(text, font, scale, thick)
    pad = int(6 * scale)
    y = max(th + pad, y)
    cv2.rectangle(img, (x, y - th - pad), (x + tw + 2 * pad, y + base), bg_bgr, -1)
    cv2.putText(img, text, (x + pad, y - pad // 2), font, scale, fg_bgr, thick, cv2.LINE_AA)


def draw_pothole(img, bbox, severity, conf):
    """Draw an ellipse around one pothole + a severity/confidence chip.

    Returns (cx, cy, r) of the drawn circle for the frontend.
    """
    x1, y1, x2, y2 = [int(v) for v in bbox]
    color = SEVERITY_BGR.get(severity, (30, 200, 245))
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    ax, ay = max(6, (x2 - x1) // 2), max(6, (y2 - y1) // 2)
    r = int(np.hypot(ax, ay))

    thick = max(2, int(img.shape[1] / 640))
    # Flat ellipse outline + subtle inner tick marks, no blur/glow.
    cv2.ellipse(img, (cx, cy), (ax + thick, ay + thick), 0, 0, 360, color, thick, cv2.LINE_AA)
    # crosshair center tick
    cv2.line(img, (cx - 6, cy), (cx + 6, cy), color, max(1, thick - 1), cv2.LINE_AA)
    cv2.line(img, (cx, cy - 6), (cx, cy + 6), color, max(1, thick - 1), cv2.LINE_AA)

    label = f"{severity.upper()} {int(conf * 100)}%"
    _rounded_label(img, label, (x1, y1 - 4), color)
    return cx, cy, r
