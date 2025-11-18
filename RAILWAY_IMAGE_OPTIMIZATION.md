# Railway Image Size Optimization

## Problem
The Docker image was 8.6 GB, exceeding Railway's 4.0 GB limit.

## Solution
Optimized the Dockerfile with the following strategies:

### 1. **Multi-Stage Build**
- Separate build and runtime stages
- Only copy necessary files to final image
- Reduces final image size significantly

### 2. **CPU-Only PyTorch**
- Using `torch==2.1.0+cpu` instead of full PyTorch
- Reduces size from ~5GB to ~500MB for PyTorch alone
- Sufficient for CPU-based inference (transformers, sentence-transformers)

### 3. **Dockerignore File**
- Excludes unnecessary files from build context:
  - `node_modules/`, `frontend/dist/`, `data/`, `logs/`
  - Test files, documentation, scripts
  - Large media files (audio, video, images)

### 4. **Optimized Dependencies**
- Removed `torch>=2.1.0` from `requirements.txt` (installed separately in Dockerfile)
- Using `--no-cache-dir` for pip installs
- Cleaning apt cache after installations

### 5. **Minimal Runtime Dependencies**
- Only installing `curl` for health checks in runtime stage
- Removed build tools (gcc, g++) from final image

## Expected Results
- **Before:** ~8.6 GB
- **After:** ~2-3 GB (well under 4.0 GB limit)

## Files Changed
1. `Dockerfile` - Multi-stage build with CPU-only PyTorch
2. `.dockerignore` - Excludes unnecessary files
3. `railway.json` - Changed from NIXPACKS to DOCKERFILE builder
4. `requirements.txt` - Commented out torch (installed separately)

## Deployment
Railway will now:
1. Use the Dockerfile instead of auto-detecting
2. Build a much smaller image
3. Deploy successfully within the 4.0 GB limit

## Local Development
For local development, you may need to install PyTorch separately:
```bash
pip install torch torchvision torchaudio
```

Or use the CPU-only version:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

