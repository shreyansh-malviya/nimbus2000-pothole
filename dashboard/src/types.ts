export type Severity = "shallow" | "deep" | "severe";

export interface Pothole {
  id: string;
  bbox: [number, number, number, number]; // x1,y1,x2,y2 in pixels
  cx: number; // circle center x (px)
  cy: number; // circle center y (px)
  r: number; // circle radius (px)
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
  annotated: string;
  raw: string;
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

export interface ModelInfo {
  weights: string;
  imgsz: number;
  conf: number;
  metrics: {
    mAP50: number;
    mAP50_95: number;
    precision: number;
    recall: number;
  };
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

export interface DetectionsFile {
  drone: string;
  session_id: string;
  generated_at: string;
  model: ModelInfo;
  summary: Summary;
  path: PathPoint[];
  detections: Detection[];
}
