# Quick Deployment Guide

## 🚀 Fastest Way to Deploy (5 Steps)

### 1. Start Qdrant
```bash
docker run -d -p 6334:6333 -p 6335:6334 --name hygiaai-qdrant qdrant/qdrant
```

### 2. Populate Data
```bash
python scripts/populate_realistic_cases.py
python scripts/populate_knowledge_base_complete.py
```

### 3. Start Backend
```bash
python run_server.py
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Open Browser
```
http://localhost:3000
```

---

## ✅ Verify Everything Works

- Qdrant: http://localhost:6334/health
- Backend: http://localhost:8000/health  
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## 📋 Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 20+ installed
- [ ] Docker running
- [ ] `.env` file with `DEEPGRAM_API_KEY`

---

**That's it!** Your deployment is ready for demo. 🎉

