"use client";
import { checkBackend } from "@/lib/api";
import { useEffect, useState } from "react";

export function Header({
  sessionId,
  weights,
  map50,
}: {
  sessionId: string;
  weights: string;
  map50: number;
}) {
  const [backendUp, setBackendUp] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    checkBackend().then((ok) => alive && setBackendUp(ok));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <header className="hdr">
      <div className="hdr__brand">
        <div className="hdr__glyph" aria-hidden>
          <svg viewBox="0 0 40 40" width="34" height="34">
            <g>
              <circle cx="9" cy="9" r="6" fill="#ffc21f" />
              <circle cx="31" cy="9" r="6" fill="#ff7a1a" />
              <circle cx="9" cy="31" r="6" fill="#ff7a1a" />
              <circle cx="31" cy="31" r="6" fill="#ffc21f" />
            </g>
            <path d="M9 9 L20 20 L31 31 M31 9 L20 20 L9 31" stroke="#0d0d0f" strokeWidth="3" />
            <rect x="15" y="15" width="10" height="10" rx="2" fill="#0d0d0f" />
          </svg>
        </div>
        <div>
          <h1 className="hdr__title">
            NIMBUS<span>2000</span>
          </h1>
          <div className="hdr__sub">Aerial Road-Surface Pothole Survey</div>
        </div>
      </div>

      <div className="hdr__stats">
        <div className="hdr__stat">
          <span className="hdr__k">SESSION</span>
          <span className="hdr__v">{sessionId}</span>
        </div>
        <div className="hdr__stat">
          <span className="hdr__k">MODEL</span>
          <span className="hdr__v">{weights}</span>
        </div>
        <div className="hdr__stat hdr__stat--badge">
          <span className="hdr__k">mAP@50</span>
          <span className="hdr__v hdr__v--acc">{(map50 * 100).toFixed(1)}%</span>
        </div>
      </div>

      <div
        className={`backend-dot ${
          backendUp === null ? "" : backendUp ? "backend-dot--up" : "backend-dot--down"
        }`}
        title="Detection backend status"
      >
        <i />
        {backendUp === null ? "checking…" : backendUp ? "backend online" : "backend offline"}
      </div>
    </header>
  );
}
