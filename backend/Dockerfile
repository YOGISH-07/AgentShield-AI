# Use official slim Python 3.11 runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend code and data directory
COPY backend/ ./backend/
COPY data/ ./data/

# Create data directory if missing
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Run AgentShield FastAPI app with Uvicorn
CMD exec uvicorn backend.alert_api:app --host 0.0.0.0 --port ${PORT:-8000}
