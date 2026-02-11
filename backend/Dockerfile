FROM python:3.10-slim

# Copy uv for fast installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 1. Install system dependencies
# Added cmake and pkg-config for dlib/face-recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    cmake \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy requirements
COPY requirements.txt .

# 3. Install with uv (using the flags we discussed)
# Note: dlib compilation takes a few minutes, this is normal!
RUN uv pip install \
    --no-cache \
    --system \
    --index-strategy unsafe-best-match \
    --prerelease allow \
    -r requirements.txt

# 4. Copy application
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]