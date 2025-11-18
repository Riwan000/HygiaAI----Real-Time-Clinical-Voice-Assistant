# Collection Consistency Guide

This document ensures all features use the correct Qdrant collections consistently.

## Standard Collection Architecture

### 1. `clinical_kb_collection` - Knowledge Base
**Purpose**: Medical knowledge, guidelines, textbooks, research articles

**Used By**:
- Knowledge base search endpoints
- Knowledge base file upload
- SOAP generator (for knowledge context)
- SOAP RAG enhancer
- Clinical RAG (for knowledge retrieval)

**Content**:
- NCBI Bookshelf medical textbooks
- PubMed Central Open Access articles
- WHO Global Health Observatory data
- User-uploaded knowledge files
- Medical ontologies and guidelines

### 2. `patient_memory_collection` - Patient Records
**Purpose**: All patient clinical cases (both real-time and historical)

**Used By**:
- Patient case ingestion (also stored in hygiaai_cases)
- Patient history retrieval
- SOAP generator (for patient history)
- Clinical RAG (for patient history)
- Outbreak detection
- Regional analytics
- Temporal clustering
- Pattern analysis

**Content**:
- Real-time patient consultations from HygiaAI
- Historical patient records (MIMIC, eICU, etc.)
- All patient cases for analytics

### 3. `hygiaai_cases` - Real-Time Cases
**Purpose**: Real-time patient cases from HygiaAI users (primary storage)

**Used By**:
- Case ingestion orchestrator (primary storage)
- Real-time case retrieval
- Similar case search (current consultations)

**Content**:
- Current patient consultations
- Also copied to patient_memory_collection for analytics

---

## Collection Usage Rules

### ✅ DO:
- **Knowledge Base**: Always use `clinical_kb_collection`
- **Patient Records**: Use `patient_memory_collection` for analytics, history, outbreak detection
- **Real-Time Cases**: Use `hygiaai_cases` for current consultations
- **RAG Systems**: Use `clinical_kb_collection` for knowledge + `patient_memory_collection` for patient history

### ❌ DON'T:
- Don't use `hygiaai_knowledge_base` (deprecated, use `clinical_kb_collection`)
- Don't use `hygiaai_clinical_cases` (deprecated, use `patient_memory_collection`)
- Don't mix knowledge base and patient data in same collection
- Don't use different collections for same purpose across features

---

## Feature-Specific Collection Usage

### Knowledge Base Features
- **Search**: `clinical_kb_collection`
- **Upload**: `clinical_kb_collection`
- **Domains/Sources**: `clinical_kb_collection`

### Patient Record Features
- **Ingestion**: `hygiaai_cases` (primary) + `patient_memory_collection` (copy)
- **History Retrieval**: `patient_memory_collection`
- **Similar Cases**: `patient_memory_collection` (or `hygiaai_cases` for real-time)

### Clinical RAG Features
- **Knowledge Retrieval**: `clinical_kb_collection`
- **Patient History**: `patient_memory_collection`
- **Similar Cases**: `patient_memory_collection`

### Analytics Features
- **Outbreak Detection**: `patient_memory_collection`
- **Regional Analytics**: `patient_memory_collection`
- **Temporal Clustering**: `patient_memory_collection`
- **Pattern Analysis**: `patient_memory_collection`

### SOAP Generation Features
- **Knowledge Context**: `clinical_kb_collection`
- **Patient History**: `patient_memory_collection`
- **RAG Enhancement**: `clinical_kb_collection`

---

## Verification Checklist

When adding new features or scripts, verify:

- [ ] Knowledge base operations use `clinical_kb_collection`
- [ ] Patient record operations use `patient_memory_collection` (for analytics) or `hygiaai_cases` (for real-time)
- [ ] RAG systems use both `clinical_kb_collection` and `patient_memory_collection`
- [ ] No deprecated collection names (`hygiaai_knowledge_base`, `hygiaai_clinical_cases`)
- [ ] Collection names are consistent across related features

---

## Migration Status

### ✅ Migrated to Standard Collections:
- Knowledge base search endpoints
- Knowledge base file upload
- SOAP generator knowledge retrieval
- SOAP RAG enhancer
- Clinical RAG patient history
- Outbreak scenario population script

### ⚠️ Needs Review:
- Some old population scripts may still use deprecated collections
- Documentation may reference old collection names

---

**Last Updated**: 2024
**Version**: 1.0

