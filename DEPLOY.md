# Deploying Nimbus2000 — Vercel (frontend) + Render (backend)

Goal: a public Vercel URL where you upload a flight **ZIP** and get pothole
results back from the Render-hosted detection backend.

```
 you ──upload ZIP──▶ Vercel (Next.js static)  ──ZIP POSTed direct──▶ Render (FastAPI + YOLOv8)
                         ▲                                                    │
                         └──────────────  JSON + annotated frames  ◀──────────┘
```

The browser sends the ZIP **straight to Render**, so Vercel's 4.5 MB request
limit never applies.

---

## Prerequisites
- The trained model exists at `models/best.pt` **and is committed** (it ships to
  Render for inference). Training writes it; then `git add -f models/best.pt`.
- Accounts: GitHub, [Vercel](https://vercel.com), [Render](https://render.com).

---

## Step 0 — Push the repo to GitHub
```bash
git remote add origin https://github.com/<you>/nimbus2000-pothole.git
git push -u origin main        # (or master)
```
Confirm `models/best.pt` is in the pushed tree (it's whitelisted in .gitignore).

---

## Step 1 — Backend on Render (do this first; you need its URL)

**Option A — Blueprint (uses `render.yaml`, recommended)**
1. Render dashboard → **New → Blueprint**.
2. Connect the GitHub repo. Render reads `render.yaml` and proposes the
   `nimbus2000-backend` web service (Python, **Standard** plan — needs ≥2 GB RAM;
   the 512 MB free/starter tiers OOM on torch).
3. **Apply**. First build takes ~5–10 min (CPU torch install).
4. When live, copy the URL, e.g. `https://nimbus2000-backend.onrender.com`.
5. Verify: open `…/health` → `{"status":"ok","model_present":true,...}`.

**Option B — Manual web service**
- New → Web Service → the repo → Runtime **Python 3**, Plan **Standard**.
- Build command:
  ```
  pip install --no-cache-dir torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r backend/requirements.txt
  ```
- Start command: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
- Env: `MODEL_PATH=models/best.pt`, `ALLOWED_ORIGINS=*` (tighten in Step 3).

---

## Step 2 — Frontend on Vercel
1. Vercel → **Add New → Project** → import the repo.
2. **IMPORTANT: set Root Directory = `frontend`** (Framework auto-detects Next.js).
3. Add an Environment Variable:
   - `NEXT_PUBLIC_API_URL` = your Render URL from Step 1 (no trailing slash).
   - This is **build-time** — if you change it later you must **redeploy**.
4. **Deploy**. You get `https://<your-app>.vercel.app`.

---

## Step 3 — Lock down CORS (optional but recommended)
On Render, set env `ALLOWED_ORIGINS` = your Vercel URL
(`https://<your-app>.vercel.app`) and redeploy. Now only your site may call the API.

---

## Step 4 — Use it
1. Open the Vercel URL.
2. The header shows **backend online** once Render is awake.
3. Click **Analyze Footage** → drop a flight ZIP (`frame_*.jpg` + `manifest.json`
   — your `FL-*_frames.zip` files work as-is) → **Analyze Footage**.
4. Results render live: map + severity pie + annotated frames. It also appears as
   a **LIVE** flight tab.

---

## Gotchas
- **Cold start**: Render spins down on idle (free/low tiers). The first request
  after a nap waits ~30–60 s while the service + model load — the UI shows an
  "analyzing" state; just wait.
- **`backend offline` in the header**: Render is asleep or `NEXT_PUBLIC_API_URL`
  is wrong. Open `…/health` directly to wake/verify it.
- **Big ZIPs**: fine — they go browser→Render directly. Render Standard handles
  the provided 124–196 MB flights.
- **Pre-baked flights on the site**: to also show the provided flights without
  the backend, run `python inference/bake.py --enhance`, commit
  `frontend/public/sessions/**` + `frontend/public/data/sessions.json`, and
  redeploy. (Without this, the site opens on the upload landing — still fully
  functional.)
