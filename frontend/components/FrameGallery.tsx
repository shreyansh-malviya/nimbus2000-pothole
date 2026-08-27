"use client";
import { useEffect, useMemo, useState } from "react";
import type { Detection, Severity } from "@/lib/types";
import { frameSrc } from "@/lib/types";
import { SEVERITY_COLOR, SEVERITY_LABEL, SEVERITY_ORDER } from "@/lib/constants";

interface Props {
  detections: Detection[];
  severityFilter: Severity | "all";
  activeFrame: string | null;
  onSelect: (frame: string) => void;
}

export function FrameGallery({ detections, severityFilter, activeFrame, onSelect }: Props) {
  const [modal, setModal] = useState<Detection | null>(null);

  const filtered = useMemo(
    () =>
      severityFilter === "all"
        ? detections
        : detections.filter((d) => d.potholes.some((p) => p.severity === severityFilter)),
    [detections, severityFilter]
  );

  useEffect(() => {
    if (activeFrame) {
      const d = detections.find((x) => x.frame_id === activeFrame);
      if (d) setModal(d);
    }
  }, [activeFrame, detections]);

  if (filtered.length === 0) {
    return <div className="empty">No frames match this severity filter.</div>;
  }

  return (
    <>
      <div className="gallery">
        {filtered.map((d) => {
          const worst = d.potholes
            .map((p) => p.severity)
            .reduce(
              (w, s) => (SEVERITY_ORDER.indexOf(s) > SEVERITY_ORDER.indexOf(w) ? s : w),
              "shallow" as Severity
            );
          return (
            <button
              key={d.frame_id}
              className={`card ${activeFrame === d.frame_id ? "card--active" : ""}`}
              onClick={() => {
                onSelect(d.frame_id);
                setModal(d);
              }}
              style={{ ["--accent" as any]: SEVERITY_COLOR[worst] }}
            >
              <div className="card__imgwrap">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={frameSrc(d)} alt={d.frame_id} loading="lazy" />
                <span className="card__count">{d.potholes.length}</span>
              </div>
              <div className="card__meta">
                <span className="card__id">{d.frame_id.replace(".jpg", "")}</span>
                <span className="card__gps">
                  {d.gps?.lat?.toFixed(4)}, {d.gps?.lon?.toFixed(4)}
                </span>
              </div>
              <div className="card__sev">
                {SEVERITY_ORDER.filter((s) => d.potholes.some((p) => p.severity === s)).map((s) => (
                  <span
                    key={s}
                    className="card__dot"
                    style={{ background: SEVERITY_COLOR[s] }}
                    title={SEVERITY_LABEL[s]}
                  />
                ))}
              </div>
            </button>
          );
        })}
      </div>

      {modal && <FrameModal detection={modal} onClose={() => setModal(null)} />}
    </>
  );
}

function FrameModal({ detection: d, onClose }: { detection: Detection; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const g = d.gps;
  return (
    <div className="modal" onClick={onClose}>
      <div className="modal__box" onClick={(e) => e.stopPropagation()}>
        <div className="modal__head">
          <div>
            <h3>{d.frame_id}</h3>
            <span className="modal__ts">
              t+{d.timestamp} · {d.potholes.length} pothole(s)
            </span>
          </div>
          <button className="modal__x" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal__body">
          <div className="modal__imgwrap">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={frameSrc(d)} alt={d.frame_id} />
          </div>

          <div className="modal__side">
            {g && (
              <div className="modal__gps">
                <div className="kv"><span>Latitude</span><b>{g.lat.toFixed(6)}</b></div>
                <div className="kv"><span>Longitude</span><b>{g.lon.toFixed(6)}</b></div>
                <div className="kv"><span>Altitude</span><b>{g.alt.toFixed(1)} m</b></div>
                <div className="kv"><span>Heading</span><b>{g.heading.toFixed(0)}°</b></div>
                <div className="kv"><span>GPS accuracy</span><b>±{g.accuracy.toFixed(1)} m</b></div>
              </div>
            )}

            <div className="modal__list">
              {d.potholes.map((p, i) => (
                <div key={p.id} className="pdet" style={{ ["--accent" as any]: SEVERITY_COLOR[p.severity] }}>
                  <div className="pdet__top">
                    <span className="pdet__idx">#{i + 1}</span>
                    <span className="pdet__sev">{SEVERITY_LABEL[p.severity]}</span>
                    <span className="pdet__conf">{(p.conf * 100).toFixed(0)}%</span>
                  </div>
                  <div className="pdet__bars">
                    <Bar label="size" v={p.size_ratio} />
                    <Bar label="depth cue" v={p.darkness} />
                    <Bar label="score" v={p.score} />
                  </div>
                </div>
              ))}
            </div>

            {g && (
              <a
                className="modal__maplink"
                href={`https://www.openstreetmap.org/?mlat=${g.lat}&mlon=${g.lon}#map=19/${g.lat}/${g.lon}`}
                target="_blank"
                rel="noreferrer"
              >
                Open location in OpenStreetMap ↗
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Bar({ label, v }: { label: string; v: number }) {
  return (
    <div className="bar">
      <span className="bar__label">{label}</span>
      <span className="bar__track">
        <span className="bar__fill" style={{ width: `${Math.round(v * 100)}%` }} />
      </span>
      <span className="bar__val">{v.toFixed(2)}</span>
    </div>
  );
}
