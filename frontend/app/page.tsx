"use client";
import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type { SessionData, SessionsIndex, Severity } from "@/lib/types";
import { Header } from "@/components/Header";
import { StatStrip } from "@/components/StatStrip";
import { SeverityPie } from "@/components/SeverityPie";
import { FrameGallery } from "@/components/FrameGallery";
import { UploadPanel } from "@/components/UploadPanel";
import { SEVERITY_ORDER } from "@/lib/constants";

// Leaflet touches `window` at import time — load client-only.
const FlightMap = dynamic(() => import("@/components/FlightMap").then((m) => m.FlightMap), {
  ssr: false,
  loading: () => <div className="leaflet-root" style={{ display: "grid", placeItems: "center", color: "var(--text-faint)", fontFamily: "var(--mono)" }}>loading map…</div>,
});

export default function Page() {
  const [index, setIndex] = useState<SessionsIndex | null>(null);
  const [data, setData] = useState<SessionData | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [liveData, setLiveData] = useState<SessionData | null>(null);
  const [cache] = useState<Map<string, SessionData>>(new Map());
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");
  const [activeFrame, setActiveFrame] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  // Load the sessions index, then the first session. A missing/empty index is
  // NOT an error — the app still works as an upload-and-detect tool (important
  // for a fresh deploy before any sessions are baked).
  const EMPTY_INDEX: SessionsIndex = {
    drone: "Nimbus2000",
    model: { weights: "best.pt", metrics: { mAP50: 0, mAP50_95: 0, precision: 0, recall: 0 } },
    sessions: [],
  };
  useEffect(() => {
    fetch("/data/sessions.json")
      .then((r) => (r.ok ? r.json() : EMPTY_INDEX))
      .then((idx: SessionsIndex) => {
        setIndex(idx);
        if (idx.sessions?.length) loadSession(idx.sessions[0].session_id, idx);
      })
      .catch(() => setIndex(EMPTY_INDEX));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadSession(id: string, idx = index) {
    setActiveFrame(null);
    setSeverityFilter("all");
    if (id === "__live__" && liveData) {
      setActiveId(id);
      setData(liveData);
      return;
    }
    if (cache.has(id)) {
      setActiveId(id);
      setData(cache.get(id)!);
      return;
    }
    const entry = idx?.sessions.find((s) => s.session_id === id);
    if (!entry) return;
    try {
      const r = await fetch("/" + entry.data.replace(/^\//, ""));
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const sd: SessionData = await r.json();
      cache.set(id, sd);
      setActiveId(id);
      setData(sd);
    } catch (e) {
      console.error(`Failed to load ${id}:`, e);
    }
  }

  const framesWithPotholes = useMemo(
    () => (data ? data.detections.filter((d) => d.potholes.length > 0) : []),
    [data]
  );

  if (!index) {
    return (
      <div className="boot">
        <div className="boot__spin" />
        <div className="boot__code">NIMBUS2000 · LOADING SURVEY DATA</div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header
        sessionId={data ? data.session_id : "—"}
        weights={data ? data.model.weights : index.model.weights}
        map50={data ? data.model.metrics.mAP50 : index.model.metrics.mAP50}
      />

      {/* Session switcher + Analyze Footage */}
      <div className="controls">
        <div className="sessions">
          <span className="sessions__label">Flights</span>
          {index.sessions.map((s) => (
            <button
              key={s.session_id}
              className={`stab ${activeId === s.session_id ? "stab--on" : ""}`}
              onClick={() => loadSession(s.session_id)}
            >
              <span className="stab__id">{s.session_id}</span>
              <span className="stab__meta">
                {s.frames_total} frames · {s.potholes_total} potholes
              </span>
            </button>
          ))}
          {liveData && (
            <button
              className={`stab stab--live ${activeId === "__live__" ? "stab--on" : ""}`}
              onClick={() => loadSession("__live__")}
            >
              <span className="stab__id">
                {liveData.session_id} <span className="live-badge">live</span>
              </span>
              <span className="stab__meta">
                {liveData.summary.frames_total} frames · {liveData.summary.potholes_total} potholes
              </span>
            </button>
          )}
        </div>

        <button className="analyze-btn" onClick={() => setUploadOpen(true)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d0d0f" strokeWidth="2.4">
            <path d="M12 5v14M5 12h14" strokeLinecap="round" />
          </svg>
          Analyze Footage
        </button>
      </div>

      {!data ? (
        <div className="landing">
          <div className="landing__glyph">🛰️</div>
          <h2 className="landing__title">No survey loaded yet</h2>
          <p className="landing__sub">
            Click <b>Analyze Footage</b> and drop a flight ZIP (frame_*.jpg +
            manifest.json). It’s sent to the detection backend, which runs the
            trained YOLOv8 model and returns geolocated, severity-graded potholes.
          </p>
          <button className="analyze-btn" onClick={() => setUploadOpen(true)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d0d0f" strokeWidth="2.4">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            Analyze Footage
          </button>
        </div>
      ) : (
      <>
      <StatStrip summary={data.summary} />

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
            onPick={(s) => setSeverityFilter((cur) => (cur === s ? "all" : s))}
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
                onClick={() => setSeverityFilter((cur) => (cur === s ? "all" : s))}
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
          mAP@50 {(data.model.metrics.mAP50 * 100).toFixed(1)}% · generated {data.generated_at}
        </span>
      </footer>
      </>
      )}

      {uploadOpen && (
        <UploadPanel
          onClose={() => setUploadOpen(false)}
          onResult={(sd) => {
            setLiveData(sd);
            cache.set("__live__", sd);
            setUploadOpen(false);
            setActiveFrame(null);
            setSeverityFilter("all");
            setActiveId("__live__");
            setData(sd);
          }}
        />
      )}
    </div>
  );
}
