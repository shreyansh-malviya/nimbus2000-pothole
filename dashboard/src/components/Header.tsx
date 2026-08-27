import type { DetectionsFile } from "../types";

export function Header({ data }: { data: DetectionsFile }) {
  const map50 = (data.model.metrics.mAP50 * 100).toFixed(1);
  return (
    <header className="hdr">
      <div className="hdr__brand">
        <div className="hdr__glyph" aria-hidden>
          {/* flat drone mark — four rotors, no glow */}
          <svg viewBox="0 0 40 40" width="34" height="34">
            <g fill="none" stroke="#0d0d0f" strokeWidth="2.4">
              <circle cx="9" cy="9" r="6" fill="#ffc21f" stroke="none" />
              <circle cx="31" cy="9" r="6" fill="#ff7a1a" stroke="none" />
              <circle cx="9" cy="31" r="6" fill="#ff7a1a" stroke="none" />
              <circle cx="31" cy="31" r="6" fill="#ffc21f" stroke="none" />
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
          <span className="hdr__v">{data.session_id}</span>
        </div>
        <div className="hdr__stat">
          <span className="hdr__k">MODEL</span>
          <span className="hdr__v">{data.model.weights}</span>
        </div>
        <div className="hdr__stat hdr__stat--badge">
          <span className="hdr__k">mAP@50</span>
          <span className="hdr__v hdr__v--acc">{map50}%</span>
        </div>
      </div>
    </header>
  );
}
