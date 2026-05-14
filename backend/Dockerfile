# ── Backend Dockerfile ────────────────────────────────────────────
# FastAPI + Uvicorn on Python 3.12-slim
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Prevent .pyc files and enable unbuffered logs (great for CloudWatch)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps needed by some Python packages (cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-caching friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Expose FastAPI port
EXPOSE 8000

# Run with uvicorn (prod: remove --reload, add workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
