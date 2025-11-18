# Multi-stage Dockerfile optimized for Railway deployment
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel first (better caching)
RUN pip install --no-cache-dir --user --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install PyTorch CPU-only versions first (largest packages, better caching)
# Split into individual packages for better error handling and caching
RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0+cpu

RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torchvision==0.16.0+cpu

RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torchaudio==2.1.0+cpu

# Install transformers and sentence-transformers (depend on torch)
RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    transformers>=4.35.0 sentence-transformers>=2.2.0

# Install other dependencies with timeout (split into batches for better caching)
RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    fastapi>=0.104.0 uvicorn[standard]>=0.24.0 pydantic>=2.0.0

RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    qdrant-client>=1.7.0 python-dotenv>=1.0.0

RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    reportlab>=4.0.0 python-docx>=1.1.0 PyPDF2>=3.0.0 beautifulsoup4>=4.12.0 lxml>=4.9.0

RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    deepgram-sdk>=5.3.0 google-generativeai>=0.3.0

RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    python-socketio websockets requests assemblyai

RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    pytest>=7.4.0 pytest-asyncio>=0.21.0 httpx>=0.24.0

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
