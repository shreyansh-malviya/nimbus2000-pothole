export type Severity = "shallow" | "deep" | "severe";

export interface Pothole {
  id: string;
  bbox: [number, number, number, number];
  cx: number;
  cy: number;
  r: number;
  conf: number;
  severity: Severity;
  score: number;
  size_ratio: number;
  darkness: number;
}

export interface Gps {
  lat: number;
  lon: number;
  alt: number;
  heading: number;
  accuracy: number;
}

export interface Detection {
  frame_id: string;
  annotated?: string; // relative URL (pre-baked)
  annotated_uri?: string; // base64 data URI (live upload)
  raw?: string;
  timestamp: string;
  img_w: number;
  img_h: number;
  gps: Gps;
  potholes: Pothole[];
}

export interface PathPoint {
  frame_id: string;
  lat: number;
  lon: number;
}

export interface Metrics {
  mAP50: number;
  mAP50_95: number;
  precision: number;
  recall: number;
}

export interface Summary {
  frames_total: number;
  frames_with_potholes: number;
  potholes_total: number;
  severity_counts: Record<Severity, number>;
  distance_covered_m: number;
  avg_confidence: number;
  area_bounds: { min_lat: number; max_lat: number; min_lon: number; max_lon: number };
}

export interface SessionData {
  drone: string;
  session_id: string;
  generated_at: string;
  model: { weights: string; imgsz: number; conf: number; metrics: Metrics };
  summary: Summary;
  path: PathPoint[];
  detections: Detection[];
}

export interface SessionIndexEntry {
  session_id: string;
  drone: string;
  frames_total: number;
  potholes_total: number;
  severity_counts: Record<Severity, number>;
  distance_covered_m: number;
  area_bounds: { min_lat: number; max_lat: number; min_lon: number; max_lon: number };
  data: string; // relative URL to detections.json
}

export interface SessionsIndex {
  drone: string;
  model: { weights: string; metrics: Metrics };
  sessions: SessionIndexEntry[];
}

/** Resolve the correct image src for a detection (base64 upload or baked URL). */
export function frameSrc(d: Detection): string {
  if (d.annotated_uri) return d.annotated_uri;
  if (d.annotated) return "/" + d.annotated.replace(/^\//, "");
  return "";
}
