# Multi-stage Dockerfile optimized for Railway deployment
# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production=false

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Stage 2: Build Python dependencies
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
# Using PyTorch 2.2.0 with transformers 4.34.0 for compatibility
# transformers 4.35.0+ requires PyTorch >= 2.3.0, but 2.3.0+cpu may not be available
# Using transformers 4.34.0 which is compatible with PyTorch 2.2.0
# Split into individual packages for better error handling and caching
RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.2.0+cpu

RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torchvision==0.17.0+cpu

RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torchaudio==2.2.0+cpu

# Install NumPy first (pin to <2.0 for PyTorch 2.2.0 compatibility)
# PyTorch 2.2.0 was compiled with NumPy 1.x and may have issues with NumPy 2.x
RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    "numpy<2.0"

# Install transformers and sentence-transformers (depend on torch)
# Pin transformers to 4.34.0 for compatibility with PyTorch 2.2.0
RUN pip install --no-cache-dir --user \
    --default-timeout=600 \
    --retries=5 \
    transformers==4.34.0 sentence-transformers>=2.2.0

# Install FastAPI core dependencies first
RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    fastapi>=0.104.0 uvicorn[standard]>=0.24.0 pydantic>=2.0.0

# Install python-multipart separately to ensure it's available
# This is REQUIRED for FastAPI form data and file uploads (Form(), File(), UploadFile)
RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    python-multipart>=0.0.6

# Verify python-multipart is installed
RUN python -c "import multipart; print(f'python-multipart installed: {multipart.__file__}')" || \
    (echo "ERROR: python-multipart installation failed" && exit 1)

RUN pip install --no-cache-dir --user \
    --default-timeout=300 \
    --retries=3 \
    qdrant-client>=1.7.0 python-dotenv>=1.0.0 cryptography>=41.0.0

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

# Make sure scripts in .local are usable - CRITICAL for Railway
# This ensures uvicorn and other pip --user installed scripts are found
ENV PATH="/root/.local/bin:${PATH}"

# Verify python-multipart is available in runtime stage
RUN python -c "import multipart; print(f'python-multipart verified in runtime: {multipart.__file__}')" || \
    (echo "WARNING: python-multipart not found in runtime stage, will attempt install at startup" && \
     pip install --user python-multipart>=0.0.6)

# Copy only necessary application files
COPY src/ ./src/
COPY config/ ./config/
COPY run_server.py .
COPY start_server.sh .
COPY start_server.py .

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Make startup scripts executable
RUN chmod +x start_server.sh start_server.py

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

# Run the application (Railway provides $PORT via railway.json startCommand)
# This CMD is a fallback - Railway will use startCommand from railway.json
# Option A: Use startup script (better diagnostics)
CMD ["python", "start_server.py"]
# Option B: Direct uvicorn command (simpler, faster)
# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
