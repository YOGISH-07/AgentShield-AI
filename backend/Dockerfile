# Use official slim Python runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies (e.g. OpenCV / FFmpeg runtime dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend code, data directory, and video assets
COPY backend/ ./backend/
COPY data/ ./data/
COPY videos/ ./videos/

# Create data directory if missing
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Run FastAPI app with Uvicorn
CMD exec uvicorn backend.alert_api:app --host 0.0.0.0 --port ${PORT:-8000}
