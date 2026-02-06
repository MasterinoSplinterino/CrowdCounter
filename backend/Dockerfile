FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies for OpenCV (updated for Debian Bookworm/Trixie)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (includes pre-downloaded head detection models in /models)
COPY . .

# Download YOLO26m model during build (for general person detection)
RUN python -c "from ultralytics import YOLO; YOLO('yolo26m.pt')"

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
