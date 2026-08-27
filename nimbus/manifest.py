"""Load the Nimbus2000 flight manifest and expose per-frame GPS telemetry."""
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

from .config import MANIFEST_PATH


@dataclass
class FrameTelemetry:
    frame_id: str
    video_timestamp: str
    offset_ms: int
    latitude: float
    longitude: float
    altitude_m: float
    accuracy_m: float
    heading_deg: float

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class FlightManifest:
    session_id: str
    interval_sec: float
    frames: List[FrameTelemetry]

    @property
    def by_frame(self) -> Dict[str, FrameTelemetry]:
        return {f.frame_id: f for f in self.frames}


def load_manifest(path: Path = MANIFEST_PATH) -> FlightManifest:
    """Parse manifest.json into a typed FlightManifest."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    frames = [
        FrameTelemetry(
            frame_id=f["frameId"],
            video_timestamp=f.get("videoTimestamp", ""),
            offset_ms=int(f.get("offsetMs", 0)),
            latitude=float(f["latitude"]),
            longitude=float(f["longitude"]),
            altitude_m=float(f.get("altitudeM", 0.0)),
            accuracy_m=float(f.get("accuracyM", 0.0)),
            heading_deg=float(f.get("headingDeg", 0.0)),
        )
        for f in raw["frames"]
    ]
    return FlightManifest(
        session_id=raw.get("sessionId", "unknown"),
        interval_sec=float(raw.get("intervalSec", 1)),
        frames=frames,
    )


if __name__ == "__main__":
    m = load_manifest()
    print(f"session={m.session_id} interval={m.interval_sec}s frames={len(m.frames)}")
    print("first:", m.frames[0].as_dict())
