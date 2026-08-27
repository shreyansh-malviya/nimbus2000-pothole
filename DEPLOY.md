# Deploying Nimbus2000 — Vercel (frontend) + Render FREE (backend)

Goal: a public Vercel URL where you upload a flight **ZIP** and get pothole
results from a **free** Render-hosted backend — no credit card, no laptop.

```
 you ──upload ZIP──▶ Vercel (Next.js static)  ──ZIP POSTed direct──▶ Render FREE (FastAPI + ONNX)
                         ▲                                                    │
                         └──────────────  JSON + annotated frames  ◀──────────┘
```

The backend runs **ONNX Runtime** (not PyTorch), so it fits Render's free
512 MB tier. The browser sends the ZIP straight to Render, bypassing Vercel's
4.5 MB request limit.

---

## Prerequisites
- `models/best.onnx` is committed (the backend loads it). ✅ already in the repo.
- Accounts: GitHub, [Vercel](https://vercel.com), [Render](https://render.com).
  **No credit card needed** for either free tier.

---

## Step 1 — Backend on Render (free)

**Blueprint (uses `render.yaml`)**
1. Render dashboard → **New → Blueprint**.
2. Connect the repo `shreyansh-malviya/nimbus2000-pothole`. If it's not listed,
   *"Configure GitHub App"* → grant access to this private repo.
3. Render reads `render.yaml` and proposes `nimbus2000-backend` on the **Free**
   plan. Click **Apply**. Build takes ~3–5 min (ONNX install is small).
4. Copy the URL, e.g. `https://nimbus2000-backend.onrender.com`.
5. Verify `…/health` → `{"status":"ok","model_present":true,...}` ✅

**Manual (if you skip the blueprint)**
- New → Web Service → the repo → Runtime **Python 3**, Plan **Free**.
- Build: `pip install -r backend/requirements.txt`
- Start: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
- Env: `MODEL_PATH=models/best.onnx`, `ALLOWED_ORIGINS=*`

> **Free-tier cold start:** the service sleeps after ~15 min idle and takes
> ~40 s to wake on the next request. Keep it warm with the pinger (Step 4).

---

## Step 2 — Frontend on Vercel (free)
1. Vercel → **Add New → Project** → import the repo.
2. **Set Root Directory = `frontend`** (Next.js auto-detected).
3. Env var `NEXT_PUBLIC_API_URL` = your Render URL (no trailing slash).
   *(Build-time — redeploy if you change it.)*
4. **Deploy** → `https://<your-app>.vercel.app`.

---

## Step 3 — Lock CORS (optional)
Render → service → **Environment** → `ALLOWED_ORIGINS` = your Vercel URL → save.

---

## Step 4 — Keep it awake (pinger)
Render Free sleeps when idle. The companion repo **`nimbus2000-pinger`** is a
GitHub Actions cron that hits `/health` every ~10 min so the backend stays warm
during the hackathon. Set its `BACKEND_URL` secret/variable to your Render URL.
See that repo's README.

---

## Step 5 — Use it
Open the Vercel URL → **backend online** → the two flights load with real
potholes → **Analyze Footage** → drop any `FL-*_frames.zip` → live results. 🎉

---

## Updating the model
`models/best.onnx` is exported from the trained model:
```bash
python -c "from ultralytics import YOLO; YOLO('models/best.pt').export(format='onnx', imgsz=640, opset=12, simplify=True)"
python inference/bake.py --model models/best.onnx --conf 0.35 --enhance   # refresh static flights
git add models/best.onnx frontend/public && git commit -m "update model" && git push
```
Both Render and Vercel **auto-redeploy on push to `main`**.
