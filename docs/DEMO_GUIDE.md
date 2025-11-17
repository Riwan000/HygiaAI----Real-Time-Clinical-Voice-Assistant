# 🎬 HygiaAI Clinical Voice Assistant - Demo Guide

This guide provides step-by-step instructions for demonstrating the HygiaAI system with realistic medical data.

## 📋 Prerequisites

Before starting the demo, ensure:

1. **Qdrant is running** (isolated instance on port 6334)
   ```bash
   # Check if Qdrant is running
   curl http://localhost:6334/health
   ```

2. **Backend server is running**
   ```bash
   python run_server.py
   # Server should be on http://localhost:8000
   ```

3. **Frontend is running**
   ```bash
   cd frontend
   npm run dev
   # Frontend should be on http://localhost:5173
   ```

4. **Knowledge base is populated**
   ```bash
   python scripts/populate_knowledge_base_complete.py
   ```

5. **Realistic cases are populated**
   ```bash
   python scripts/populate_realistic_cases.py
   ```

## 🚀 Demo Flow

### Step 1: Setup (5 minutes)

1. **Start all services:**
   ```bash
   # Terminal 1: Qdrant (if not already running)
   docker run -d -p 6334:6334 qdrant/qdrant
   
   # Terminal 2: Backend
   python run_server.py
   
   # Terminal 3: Frontend
   cd frontend && npm run dev
   ```

2. **Populate data:**
   ```bash
   # Populate knowledge base
   python scripts/populate_knowledge_base_complete.py
   
   # Populate realistic cases
   python scripts/populate_realistic_cases.py
   ```

3. **Verify setup:**
   - Open http://localhost:5173
   - Check that all pages load without errors
   - Verify backend API is accessible

### Step 2: Live Transcription Demo (5 minutes)

**Purpose:** Show real-time speech-to-text transcription

1. Navigate to **Live Transcription** page
2. Click **"Start Recording"**
3. Speak a realistic consultation:
   ```
   "Patient is a 35-year-old female presenting with chief complaint of 
   persistent headache for the past 5 days. The headache is throbbing in 
   nature, located in the frontal region, rated 7 out of 10 in severity. 
   Patient reports associated nausea but no vomiting. No history of head 
   trauma. On examination, vital signs are normal. Blood pressure is 120 
   over 80, heart rate 72 beats per minute, temperature 37 degrees Celsius. 
   Neurological examination is within normal limits. Assessment: Tension 
   headache. Plan: Prescribed Ibuprofen 400 milligrams three times daily 
   for 3 days, advised rest and stress management. Follow-up in one week if 
   symptoms persist."
   ```
4. Click **"Stop Recording"**
5. Click **"Save to Cases"** to store the transcript
6. Click **"Generate SOAP Note"** to show automatic SOAP extraction

**Key Points to Highlight:**
- Real-time transcription accuracy
- Automatic SOAP note generation
- Integration with knowledge base for enhanced extraction

### Step 3: Case Search & Retrieval Demo (5 minutes)

**Purpose:** Show similar case retrieval using vector search

1. Navigate to **Dashboard** (Case Search)
2. Enter search query: `"cough with fever"`
3. Show results with similarity scores
4. Click on a case to view details
5. Demonstrate filters:
   - Age group: Adult
   - Region: Kerala
   - Time range: Last 30 days
6. Show case comparison by selecting 2 cases

**Key Points to Highlight:**
- Semantic search (not just keyword matching)
- Similarity scoring
- Filtering by metadata
- Case comparison feature

### Step 4: SOAP Notes Viewer Demo (3 minutes)

**Purpose:** Show structured SOAP note viewing and export

1. Navigate to **SOAP Notes** page
2. Show list of generated SOAP notes
3. Click on a note to view full details
4. Demonstrate PDF export:
   - Click **"Export PDF"**
   - Show downloaded PDF with proper formatting
5. Demonstrate DOCX export:
   - Click **"Export DOCX"**
   - Show downloaded Word document

**Key Points to Highlight:**
- Structured SOAP format
- Professional document export
- Integration with case data

### Step 5: Analytics & Trends Demo (5 minutes)

**Purpose:** Show knowledge intelligence and trend analysis

1. Navigate to **Analytics** page
2. Show **Trend Chart:**
   - Disease trends over time
   - Confidence intervals
   - Export functionality
3. Show **Cluster Map:**
   - Disease clusters by time and location
   - Bubble sizes indicate case counts
4. Show **Heatmap:**
   - Clinic-level disease patterns
   - Color intensity shows prevalence
5. Demonstrate filters:
   - Time range selection
   - Region filtering
   - Disease type filtering

**Key Points to Highlight:**
- Visual data representation
- Pattern recognition
- Regional health trends
- Export capabilities

### Step 6: Knowledge Base Browser Demo (3 minutes)

**Purpose:** Show medical knowledge base search

1. Navigate to **Knowledge Base** page
2. Search for: `"vital signs normal values"`
3. Show search results with:
   - Domain categorization
   - Source information
   - Year of publication
4. Filter by:
   - Domain: Clinical Reference
   - Source: HygiaAI_Curated
5. Click on a knowledge entry to view details

**Key Points to Highlight:**
- Comprehensive medical knowledge
- Searchable reference database
- Source attribution
- Domain organization

### Step 7: Timeline Viewer Demo (3 minutes)

**Purpose:** Show patient case timeline visualization

1. Navigate to **Timeline** page
2. Show timeline of events:
   - Diagnosis events
   - Treatment events
   - Follow-up events
   - Outcomes
3. Filter by event type
4. Filter by date range
5. Click on an event to view details

**Key Points to Highlight:**
- Chronological case history
- Event categorization
- Visual timeline representation
- Filtering capabilities

### Step 8: Multimodal Input Demo (3 minutes)

**Purpose:** Show multimodal data ingestion

1. Navigate to **Multimodal Input** page
2. Upload a sample image (e.g., X-ray image)
3. Upload a text file (e.g., lab report)
4. Fill in metadata:
   - Patient ID
   - Age group
   - Region
   - Diagnosis
5. Submit to ingest into system
6. Show success message

**Key Points to Highlight:**
- Multiple data type support
- Metadata capture
- Integration with storage system

## 🎯 Key Demo Talking Points

### 1. **Real-Time Transcription**
- "HygiaAI uses Deepgram's advanced ASR for real-time transcription"
- "Transcription accuracy is optimized for medical terminology"
- "Automatic speaker identification for multi-party consultations"

### 2. **Intelligent SOAP Generation**
- "SOAP notes are automatically generated using RAG-enhanced extraction"
- "Knowledge base provides context for accurate entity extraction"
- "Structured format follows medical documentation standards"

### 3. **Similar Case Retrieval**
- "Vector embeddings enable semantic search, not just keyword matching"
- "Similarity scores help identify clinically relevant cases"
- "Filtering by metadata enables targeted searches"

### 4. **Knowledge Intelligence**
- "Temporal clustering identifies disease patterns over time"
- "Regional analytics help track health trends"
- "Trust scores ensure clinical reliability"

### 5. **Privacy & Compliance**
- "All data is encrypted and de-identified"
- "HIPAA-compliant architecture"
- "Federated learning preserves patient privacy"

## 📊 Demo Data Overview

The system includes **10 realistic clinical cases** covering:

- **Respiratory:** Acute Bronchitis, COPD Exacerbation, Bronchial Asthma
- **Infectious:** Febrile Illness (Suspected Dengue), Acute Gastroenteritis
- **Chronic:** Diabetic Foot Ulcer, Mild Cognitive Impairment
- **Women's Health:** Hyperemesis Gravidarum, Menorrhagia
- **Musculoskeletal:** Lumbar Strain with Sciatica

**Regions covered:**
- Kerala, Tamil Nadu, Maharashtra, Odisha, Karnataka
- West Bengal, Rajasthan, Gujarat, Andhra Pradesh, Punjab

**Age groups:**
- Pediatric (8-12 years)
- Adult (28-55 years)
- Elderly (60-65 years)

## 🔧 Troubleshooting

### Backend not responding
```bash
# Check if server is running
curl http://localhost:8000/health

# Check logs
tail -f logs/server.log
```

### Qdrant connection issues
```bash
# Verify Qdrant is running
curl http://localhost:6334/health

# Check collections
curl http://localhost:6334/collections
```

### Frontend errors
- Check browser console for errors
- Verify API endpoints are accessible
- Check network tab for failed requests

### No data showing
- Verify cases are populated: `python scripts/populate_realistic_cases.py`
- Verify knowledge base is populated: `python scripts/populate_knowledge_base_complete.py`
- Check Qdrant collections have data

## 📝 Post-Demo Checklist

After the demo:

1. ✅ Document any issues encountered
2. ✅ Note questions from audience
3. ✅ Update demo script based on feedback
4. ✅ Clean up any test data if needed
5. ✅ Reset system state if required

## 🎓 Educational Value

This demo showcases:

1. **AI-Powered Clinical Documentation:** Automatic SOAP note generation
2. **Semantic Search:** Vector-based case retrieval
3. **Knowledge Integration:** RAG-enhanced clinical decision support
4. **Data Visualization:** Trends, clusters, and patterns
5. **Multimodal Support:** Text, image, and audio processing
6. **Privacy-Preserving:** Federated learning architecture

---

**Ready to demonstrate?** Follow the steps above and highlight the key features that make HygiaAI valuable for rural healthcare providers.

