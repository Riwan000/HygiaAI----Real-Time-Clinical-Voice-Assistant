# Multi-stage Dockerfile optimized for Railway deployment
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with optimizations
# Use CPU-only PyTorch to reduce image size significantly (from ~8GB to ~2GB)
RUN pip install --no-cache-dir --user \
    --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    torchaudio==2.1.0+cpu && \
    pip install --no-cache-dir --user \
    -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy only necessary application files
COPY src/ ./src/
COPY config/ ./config/
COPY run_server.py .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/.cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Health check (Railway will use its own healthcheckPath, but this is for Docker)
# Increased start-period to allow app to fully initialize (PyTorch/transformers can take time)
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application (Railway provides $PORT)
# Use shell form to expand PORT variable
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
