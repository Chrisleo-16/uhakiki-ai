FROM python:3.10-slim

WORKDIR /app

# 1. Install system dependencies + Build tools (needed for scikit-image/numpy compilation)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# 2. Upgrade core pip tools to avoid metadata errors
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 3. Install NumPy FIRST as a standalone layer 
# This fixes the "No module named 'numpy'" error during scikit-image setup
RUN pip install --no-cache-dir numpy==1.24.3

# 4. Copy requirements and install the rest
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application
COPY . .

# 6. Set Environment Variables for Phase 3
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]