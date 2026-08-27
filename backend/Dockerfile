# Nimbus2000 detection backend — container image (Fly.io / Railway / self-host).
# Build context = repo root:  docker build -f backend/Dockerfile -t nimbus-backend .
FROM python:3.10-slim

# OpenCV runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code + shared engine + model weights
COPY nimbus/ nimbus/
COPY backend/ backend/
COPY models/ models/

ENV MODEL_PATH=models/best.pt ALLOWED_ORIGINS=*
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
