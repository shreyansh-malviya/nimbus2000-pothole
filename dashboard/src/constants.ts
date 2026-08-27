import type { Severity } from "./types";

export const SEVERITY_ORDER: Severity[] = ["shallow", "deep", "severe"];

export const SEVERITY_COLOR: Record<Severity, string> = {
  shallow: "#ffc21f",
  deep: "#ff7a1a",
  severe: "#d1341a",
};

export const SEVERITY_LABEL: Record<Severity, string> = {
  shallow: "Shallow",
  deep: "Deep",
  severe: "Severe",
};

export const SEVERITY_DESC: Record<Severity, string> = {
  shallow: "Minor surface break — monitor",
  deep: "Pronounced cavity — schedule repair",
  severe: "Hazardous depth/size — priority repair",
};
