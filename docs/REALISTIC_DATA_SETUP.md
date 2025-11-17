# Realistic Data Setup Guide

This guide explains how to populate HygiaAI with realistic medical data and remove test data.

## 🎯 Overview

The system now uses **realistic clinical cases** based on common rural healthcare scenarios in India, replacing all test/mock data.

## 📊 What's Included

### Realistic Clinical Cases (10 cases)

1. **Acute Bronchitis** - 45-year-old male farmer from Kerala
2. **Febrile Illness (Suspected Dengue)** - 28-year-old female from Tamil Nadu
3. **Diabetic Foot Ulcer** - 55-year-old male from Maharashtra
4. **Hyperemesis Gravidarum** - 35-year-old pregnant woman from Odisha
5. **Bronchial Asthma** - 12-year-old boy from Karnataka
6. **Mild Cognitive Impairment** - 60-year-old female from West Bengal
7. **Acute Gastroenteritis** - 8-year-old girl from Rajasthan
8. **Lumbar Strain with Sciatica** - 42-year-old construction worker from Gujarat
9. **Menorrhagia with Anemia** - 30-year-old female from Andhra Pradesh
10. **COPD Exacerbation** - 65-year-old male from Punjab

**Coverage:**
- **Age Groups:** Pediatric (8-12), Adult (28-55), Elderly (60-65)
- **Regions:** 10 different states across India
- **Diagnoses:** Respiratory, Infectious, Chronic, Women's Health, Musculoskeletal
- **Comorbidities:** Diabetes, Hypertension, Pregnancy, COPD

### Medical Knowledge Base

- SOAP Note Documentation Guidelines
- Normal Vital Signs Reference (all age groups)
- Common Symptoms and Clinical Patterns
- Medication Categories and Common Drugs
- Common Diagnoses and Diagnostic Criteria
- SOAP Note Extraction Rules and Best Practices

## 🚀 Setup Instructions

### Step 1: Clean Up Test Data (Optional)

If you have existing test data, clean it up first:

```bash
python scripts/cleanup_test_data.py
```

**Note:** This script provides guidance. For automated cleanup, use Qdrant's delete API with filters.

### Step 2: Populate Knowledge Base

Populate the medical knowledge base with curated and internet-sourced knowledge:

```bash
python scripts/populate_knowledge_base_complete.py
```

This will:
- Add curated medical knowledge (SOAP guidelines, vital signs, etc.)
- Fetch knowledge from WHO, CDC, and medical references
- Store everything in Qdrant knowledge base collection

**Expected Output:**
```
✅ Documents processed: 6+ (curated)
✅ Documents ingested from internet sources
✅ Knowledge base ready for use
```

### Step 3: Populate Realistic Cases

Add realistic clinical cases to the system:

```bash
python scripts/populate_realistic_cases.py
```

This will:
- Generate embeddings for each case transcript
- Generate SOAP notes automatically
- Store cases in Qdrant clinical cases collection

**Expected Output:**
```
✅ Cases processed: 10
✅ Cases stored: 10
✅ Realistic clinical cases are now available
```

### Step 4: Verify Data

Check that data is populated:

```bash
# Check Qdrant collections
curl http://localhost:6334/collections

# Check case count (approximate)
curl http://localhost:6334/collections/hygiaai_clinical_cases
```

## 🎬 Demo Instructions

See **[DEMO_GUIDE.md](./DEMO_GUIDE.md)** for complete step-by-step demo instructions.

### Quick Demo Flow:

1. **Live Transcription** → Record a consultation
2. **Case Search** → Search for similar cases
3. **SOAP Notes** → View generated SOAP notes
4. **Analytics** → View trends and patterns
5. **Knowledge Base** → Search medical knowledge
6. **Timeline** → View case timelines

## 🔍 Data Characteristics

### Realistic Transcripts

All transcripts include:
- **Chief Complaint:** Patient's primary concern
- **History:** Onset, duration, character, severity
- **Physical Examination:** Vital signs, findings
- **Assessment:** Clinical diagnosis with reasoning
- **Plan:** Treatment, medications, follow-up

### Metadata

Each case includes:
- **Age Group:** pediatric, adult, elderly
- **Region:** Specific state/district in India
- **Diagnosis:** Clinical diagnosis
- **Outcome:** recovered, improved, under_treatment
- **Comorbidities:** Existing conditions
- **Timestamp:** Realistic date/time

### SOAP Notes

Automatically generated SOAP notes include:
- **Subjective:** Patient-reported information
- **Objective:** Measurable findings
- **Assessment:** Clinical diagnosis
- **Plan:** Treatment plan with medications

## 🧹 Maintenance

### Adding More Cases

Edit `scripts/populate_realistic_cases.py` and add to `REALISTIC_CASES` list:

```python
{
    "transcript": "Your realistic transcript here...",
    "metadata": {
        "age_group": "adult",
        "region": "State, India",
        "diagnosis": "Diagnosis Name",
        "outcome": "improved",
        "comorbidities": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
}
```

### Updating Knowledge Base

Edit `scripts/populate_medical_knowledge_base.py` to add more knowledge entries.

### Removing Test Data

Use Qdrant's delete API:

```bash
# Delete by session_id pattern
curl -X POST http://localhost:6334/collections/hygiaai_clinical_cases/points/delete \
  -H 'Content-Type: application/json' \
  -d '{
    "filter": {
      "must": [
        {
          "key": "session_id",
          "match": {
            "value": "demo-"
          }
        }
      ]
    }
  }'
```

## ✅ Verification Checklist

Before demo, verify:

- [ ] Knowledge base is populated (6+ documents)
- [ ] Realistic cases are stored (10 cases)
- [ ] SOAP notes are generated for cases
- [ ] Backend API is accessible
- [ ] Frontend loads without errors
- [ ] Search functionality works
- [ ] Analytics show data
- [ ] Knowledge base search works

## 📝 Notes

- **All data is anonymized** - No real patient information
- **Data is realistic** - Based on common rural healthcare scenarios
- **SOAP notes are auto-generated** - Using RAG-enhanced extraction
- **Knowledge base is comprehensive** - Covers common clinical scenarios

## 🆘 Troubleshooting

### Cases not showing in frontend

1. Check Qdrant is running: `curl http://localhost:6334/health`
2. Verify cases are stored: Check collection count
3. Check backend logs for errors
4. Verify API endpoints are accessible

### SOAP notes not generating

1. Check knowledge base is populated
2. Verify SOAP generator is initialized
3. Check backend logs for errors
4. Ensure transcript format is correct

### Knowledge base search not working

1. Verify knowledge base collection exists
2. Check documents are ingested
3. Verify embedding generation is working
4. Check API endpoint is accessible

---

**Ready to demo?** Follow the setup instructions above and refer to [DEMO_GUIDE.md](./DEMO_GUIDE.md) for the complete demo flow.

