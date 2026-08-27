import type { Summary } from "@/lib/types";

function Stat({
  label,
  value,
  unit,
  accent,
}: {
  label: string;
  value: string | number;
  unit?: string;
  accent?: "amber" | "orange" | "rust" | "plain";
}) {
  return (
    <div className={`stat stat--${accent ?? "plain"}`}>
      <div className="stat__label">{label}</div>
      <div className="stat__value">
        {value}
        {unit && <span className="stat__unit">{unit}</span>}
      </div>
    </div>
  );
}

export function StatStrip({ summary }: { summary: Summary }) {
  const s = summary;
  const km = (s.distance_covered_m / 1000).toFixed(2);
  const density =
    s.frames_with_potholes > 0 ? (s.potholes_total / s.frames_with_potholes).toFixed(2) : "0";
  return (
    <div className="strip">
      <Stat label="Frames Scanned" value={s.frames_total} accent="plain" />
      <Stat label="Potholes Detected" value={s.potholes_total} accent="amber" />
      <Stat label="Severe" value={s.severity_counts.severe} accent="rust" />
      <Stat label="Deep" value={s.severity_counts.deep} accent="orange" />
      <Stat label="Shallow" value={s.severity_counts.shallow} accent="amber" />
      <Stat label="Route Covered" value={km} unit="km" accent="plain" />
      <Stat label="Avg Confidence" value={(s.avg_confidence * 100).toFixed(0)} unit="%" accent="plain" />
      <Stat label="Density / Frame" value={density} accent="plain" />
    </div>
  );
}
