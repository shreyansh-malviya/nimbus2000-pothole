import { useEffect, useMemo, useState } from "react";
import type { DetectionsFile, Severity } from "./types";
import { Header } from "./components/Header";
import { StatStrip } from "./components/StatStrip";
import { SeverityPie } from "./components/SeverityPie";
import { FlightMap } from "./components/FlightMap";
import { FrameGallery } from "./components/FrameGallery";
import { SEVERITY_ORDER } from "./constants";

export default function App() {
  const [data, setData] = useState<DetectionsFile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");
  const [activeFrame, setActiveFrame] = useState<string | null>(null);

  useEffect(() => {
    fetch("data/detections.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: DetectionsFile) => setData(d))
      .catch((e) => setError(String(e)));
  }, []);

  const framesWithPotholes = useMemo(
    () => (data ? data.detections.filter((d) => d.potholes.length > 0) : []),
    [data]
  );

  if (error) {
    return (
      <div className="boot boot--err">
        <div className="boot__code">DATA LOAD FAILED</div>
        <p>{error}</p>
        <p className="boot__hint">
          Run the inference pipeline to generate{" "}
          <code>dashboard/public/data/detections.json</code>.
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="boot">
        <div className="boot__spin" />
        <div className="boot__code">NIMBUS2000 · LOADING SURVEY DATA</div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header data={data} />
      <StatStrip data={data} />

      <main className="grid">
        <section className="panel panel--map">
          <div className="panel__head">
            <h3>Flight Path &amp; Pothole Geolocation</h3>
            <span className="panel__meta">
              {data.path.length} GPS fixes · session {data.session_id}
            </span>
          </div>
          <FlightMap
            data={data}
            severityFilter={severityFilter}
            activeFrame={activeFrame}
            onSelect={setActiveFrame}
          />
        </section>

        <section className="panel panel--pie">
          <div className="panel__head">
            <h3>Severity Distribution</h3>
            <span className="panel__meta">{data.summary.potholes_total} detections</span>
          </div>
          <SeverityPie
            counts={data.summary.severity_counts}
            active={severityFilter}
            onPick={(s) =>
              setSeverityFilter((cur) => (cur === s ? "all" : s))
            }
          />
        </section>
      </main>

      <section className="panel panel--gallery">
        <div className="panel__head">
          <h3>Detected Potholes — Annotated Frames</h3>
          <div className="filter-row">
            <button
              className={`chip ${severityFilter === "all" ? "chip--on" : ""}`}
              onClick={() => setSeverityFilter("all")}
            >
              All
            </button>
            {SEVERITY_ORDER.map((s) => (
              <button
                key={s}
                className={`chip chip--${s} ${severityFilter === s ? "chip--on" : ""}`}
                onClick={() =>
                  setSeverityFilter((cur) => (cur === s ? "all" : s))
                }
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <FrameGallery
          detections={framesWithPotholes}
          severityFilter={severityFilter}
          activeFrame={activeFrame}
          onSelect={setActiveFrame}
        />
      </section>

      <footer className="foot">
        <span>
          {data.drone} · autonomous road-survey · model {data.model.weights}
        </span>
        <span className="foot__mono">
          mAP@50 {(data.model.metrics.mAP50 * 100).toFixed(1)}% · generated{" "}
          {data.generated_at}
        </span>
      </footer>
    </div>
  );
}
