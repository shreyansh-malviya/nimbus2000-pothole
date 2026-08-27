"use client";
import { useRef, useState } from "react";
import { analyzeZip } from "@/lib/api";
import { API_URL } from "@/lib/constants";
import type { SessionData } from "@/lib/types";

interface Props {
  onClose: () => void;
  onResult: (data: SessionData) => void;
}

type Stage = "idle" | "uploading" | "processing" | "error";

export function UploadPanel({ onClose, onResult }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [enhance, setEnhance] = useState(true);
  const [augment, setAugment] = useState(false);
  const [conf, setConf] = useState(0.2);
  const [stage, setStage] = useState<Stage>("idle");
  const [pct, setPct] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  const [over, setOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const pick = (f: File | null) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".zip")) {
      setErr("Please choose a .zip containing the flight frames + manifest.json");
      return;
    }
    setErr(null);
    setFile(f);
  };

  const run = async () => {
    if (!file) return;
    setErr(null);
    setStage("uploading");
    setPct(0);
    try {
      const data = await analyzeZip(
        file,
        { conf, enhance, augment },
        (p) => {
          setPct(p);
          if (p >= 100) setStage("processing");
        }
      );
      onResult(data);
    } catch (e: any) {
      setErr(e?.message || String(e));
      setStage("error");
    }
  };

  const busy = stage === "uploading" || stage === "processing";

  return (
    <div className="up" onClick={busy ? undefined : onClose}>
      <div className="up__box" onClick={(e) => e.stopPropagation()}>
        <div className="up__head">
          <h3>Analyze New Footage</h3>
          {!busy && (
            <button className="modal__x" onClick={onClose}>
              ✕
            </button>
          )}
        </div>

        <div className="up__body">
          {!busy && (
            <>
              <div
                className={`up__drop ${over ? "up__drop--over" : ""}`}
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setOver(true);
                }}
                onDragLeave={() => setOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setOver(false);
                  pick(e.dataTransfer.files?.[0] ?? null);
                }}
              >
                <div className="up__drop-ic">🛰️</div>
                <div className="up__drop-main">Drop a flight ZIP here, or click to browse</div>
                <div className="up__drop-sub">
                  Frames (frame_*.jpg) + manifest.json, zipped. Up to ~200 MB.
                </div>
                <input
                  ref={inputRef}
                  type="file"
                  accept=".zip"
                  hidden
                  onChange={(e) => pick(e.target.files?.[0] ?? null)}
                />
              </div>

              {file && (
                <div className="up__file">
                  <span>📦 {file.name}</span>
                  <span>{(file.size / 1_048_576).toFixed(1)} MB</span>
                </div>
              )}

              <div className="up__opts">
                <label className="up__opt">
                  <input type="checkbox" checked={enhance} onChange={(e) => setEnhance(e.target.checked)} />
                  Night/blur enhance (CLAHE)
                </label>
                <label className="up__opt">
                  <input type="checkbox" checked={augment} onChange={(e) => setAugment(e.target.checked)} />
                  Test-time augmentation
                </label>
                <label className="up__opt">
                  Confidence
                  <input
                    type="range"
                    min={0.05}
                    max={0.6}
                    step={0.05}
                    value={conf}
                    onChange={(e) => setConf(parseFloat(e.target.value))}
                  />
                  <b style={{ color: "var(--amber)", fontFamily: "var(--mono)" }}>{conf.toFixed(2)}</b>
                </label>
              </div>

              {err && <div className="up__err">{err}</div>}

              <div className="up__hint">
                The ZIP is sent straight from your browser to the detection backend at{" "}
                <code>{API_URL}</code> — bypassing hosting upload limits. The backend runs the
                trained YOLOv8 model and returns annotated frames + GPS-tagged potholes.
              </div>

              <div className="up__actions">
                <button className="up__go" disabled={!file} onClick={run}>
                  Analyze Footage
                </button>
                <button className="up__cancel" onClick={onClose}>
                  Cancel
                </button>
              </div>
            </>
          )}

          {busy && (
            <div className="up__progress">
              <div className="up__ptrack">
                <div className="up__pfill" style={{ width: `${stage === "processing" ? 100 : pct}%` }} />
              </div>
              <div className="up__pstage">
                {stage === "uploading" ? (
                  `Uploading footage… ${pct}%`
                ) : (
                  <>
                    <span className="up__spin" />
                    Running YOLOv8 detection on the backend — this can take a minute for a full flight…
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
