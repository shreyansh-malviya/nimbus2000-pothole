"""Monocular pothole severity estimation.

A single RGB frame carries no true depth, so "severity" here is an explicit,
documented *proxy* — not a claimed physical depth. It combines three cues that
correlate with how serious a pothole is in road-maintenance practice:

  1. Perspective-corrected size  — how much road the pothole occupies. Bigger =
     worse. Because the drone/camera looks down the road, a pothole lower in the
     frame is nearer, so the same pixel-area means a physically smaller defect;
     we down-weight size by vertical position to compensate.
  2. Interior darkness           — a deep pothole traps shadow, so its interior
     is darker than the surrounding road. We measure mean-intensity drop of the
     box interior vs. a ring around it. A large drop suggests depth.
  3. Detection confidence        — a weak, secondary tie-breaker.

These are combined into a 0..1 score and thresholded into {shallow, deep,
severe}. Thresholds live here so they can be tuned against real detections.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# Weights for the composite severity score (sum ~= 1.0).
W_SIZE = 0.55
W_DARK = 0.35
W_CONF = 0.10

# Score cut points -> category.
T_DEEP = 0.34     # >= this is at least "deep"
T_SEVERE = 0.60   # >= this is "severe"


@dataclass
class SeverityResult:
    level: str          # shallow | deep | severe
    score: float        # 0..1 composite
    size_ratio: float   # perspective-corrected area fraction
    darkness: float     # 0..1 interior-darkness cue
    confidence: float


def _interior_darkness(gray: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> float:
    """Return 0..1 cue: how much darker the box interior is than its surround.

    0 = interior same/brighter than surround (flat patch), 1 = interior much
    darker (deep shadowed hole).
    """
    h, w = gray.shape[:2]
    x1c, y1c = max(0, x1), max(0, y1)
    x2c, y2c = min(w, x2), min(h, y2)
    if x2c <= x1c or y2c <= y1c:
        return 0.0

    interior = gray[y1c:y2c, x1c:x2c]
    if interior.size == 0:
        return 0.0

    # Surround ring: expand box by ~50% and take the frame around the interior.
    bw, bh = (x2c - x1c), (y2c - y1c)
    ex1, ey1 = max(0, x1c - bw // 2), max(0, y1c - bh // 2)
    ex2, ey2 = min(w, x2c + bw // 2), min(h, y2c + bh // 2)
    surround = gray[ey1:ey2, ex1:ex2]
    if surround.size == 0:
        return 0.0

    interior_mean = float(interior.mean())
    surround_mean = float(surround.mean())
    if surround_mean <= 1e-6:
        return 0.0

    # Relative drop, clamped. A 40% darker interior -> ~1.0.
    drop = (surround_mean - interior_mean) / surround_mean
    return float(np.clip(drop / 0.40, 0.0, 1.0))


def classify(
    gray: np.ndarray,
    box_xyxy,
    confidence: float,
    img_w: int,
    img_h: int,
) -> SeverityResult:
    """Classify one detection's severity.

    gray      : full-frame grayscale image (H, W) uint8
    box_xyxy  : (x1, y1, x2, y2) in pixels
    """
    x1, y1, x2, y2 = [float(v) for v in box_xyxy]
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    area_frac = (bw * bh) / float(img_w * img_h)

    # Perspective correction: cy in 0..1 from top. Objects near the bottom
    # (cy->1) are closer, so scale their apparent size down; objects up high
    # (far) are boosted. Factor ranges ~0.6 (bottom) .. ~1.4 (top).
    cy = ((y1 + y2) / 2.0) / float(img_h)
    persp = 1.4 - 0.8 * cy
    size_ratio = float(np.clip(area_frac * persp, 0.0, 1.0))

    # Map size_ratio through a soft curve so typical potholes (a few % of frame)
    # spread across the 0..1 range instead of clustering near 0.
    size_cue = float(np.clip((size_ratio ** 0.5) * 2.6, 0.0, 1.0))

    darkness = _interior_darkness(gray, int(x1), int(y1), int(x2), int(y2))
    conf_cue = float(np.clip(confidence, 0.0, 1.0))

    score = W_SIZE * size_cue + W_DARK * darkness + W_CONF * conf_cue
    score = float(np.clip(score, 0.0, 1.0))

    if score >= T_SEVERE:
        level = "severe"
    elif score >= T_DEEP:
        level = "deep"
    else:
        level = "shallow"

    return SeverityResult(
        level=level,
        score=round(score, 4),
        size_ratio=round(size_ratio, 4),
        darkness=round(darkness, 4),
        confidence=round(conf_cue, 4),
    )
