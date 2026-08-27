import { API_URL } from "./constants";
import type { SessionData } from "./types";

export interface UploadOpts {
  conf?: number;
  enhance?: boolean;
  augment?: boolean;
}

/** Upload a flight ZIP directly to the Python backend (bypasses Vercel's body
 *  limit) and return the detection payload. onProgress reports upload %. */
export function analyzeZip(
  file: File,
  opts: UploadOpts = {},
  onProgress?: (pct: number) => void
): Promise<SessionData> {
  const { conf = 0.2, enhance = true, augment = false } = opts;
  const qs = new URLSearchParams({
    conf: String(conf),
    enhance: String(enhance),
    augment: String(augment),
  });
  const url = `${API_URL}/analyze?${qs.toString()}`;

  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append("file", file, file.name);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (e) {
          reject(new Error("Malformed response from backend."));
        }
      } else {
        let msg = `Backend error ${xhr.status}`;
        try {
          const j = JSON.parse(xhr.responseText);
          if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
        } catch {}
        reject(new Error(msg));
      }
    };
    xhr.onerror = () =>
      reject(
        new Error(
          `Could not reach the detection backend at ${API_URL}. Is it running / awake?`
        )
      );
    xhr.send(form);
  });
}

export async function checkBackend(): Promise<boolean> {
  try {
    const r = await fetch(`${API_URL}/health`, { method: "GET" });
    return r.ok;
  } catch {
    return false;
  }
}
