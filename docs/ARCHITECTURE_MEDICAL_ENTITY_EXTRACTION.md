# Medical Entity Extraction Architecture

## Overview

This document defines the high-level architecture for the Medical Entity Extraction system in HygiaAI. The system extracts structured medical entities from unstructured clinical transcripts with >90% accuracy.

## System Goals

- Extract medical entities (symptoms, diagnoses, medications, vital signs) from transcripts
- Achieve >90% accuracy in entity extraction
- Support real-time processing for live consultations
- Integrate with SOAP note generation pipeline
- Enable extensibility for new entity types and models

## Architecture Components

### 1. Data Flow Pipeline

```
Raw Transcript
    ↓
[Preprocessing Module]
    ↓
[Entity Extraction Engine]
    ├── Pattern Matching
    ├── Dictionary Lookup
    ├── ML-based NER (BioBERT)
    └── Rule-based Extraction
    ↓
[Post-processing Module]
    ├── Entity Normalization
    ├── Confidence Scoring
    ├── Deduplication
    └── Context Enrichment
    ↓
[Validation Module]
    ├── Medical Terminology Validation
    ├── Spell Checking
    └── Entity Classification Verification
    ↓
Structured Entity Output
```

### 2. Core Components

#### 2.1 Preprocessing Module (`preprocessing.py`)
**Purpose**: Prepare raw transcript text for entity extraction

**Responsibilities**:
- Text normalization (lowercase, whitespace cleanup)
- Sentence segmentation
- Speaker diarization handling (doctor vs patient)
- Noise removal (filler words, repetitions)
- Abbreviation expansion

**Input**: Raw transcript string
**Output**: Cleaned, normalized text with metadata

**Integration Points**:
- Receives input from transcription module
- Passes processed text to extraction engine

---

#### 2.2 Entity Extraction Engine (`medical_ner.py`)
**Purpose**: Core entity extraction using multiple strategies

**Components**:

**A. Pattern Matching Engine**
- Regex patterns for common medical terms
- Context-aware pattern matching
- Multi-word entity detection

**B. Dictionary Lookup**
- Medical terminology dictionaries
- ICD-10/SNOMED CT mappings
- Drug name databases (RxNorm)
- Symptom lexicons

**C. ML-based NER (BioBERT)**
- Fine-tuned BioBERT model for medical NER
- Handles complex entity boundaries
- Contextual understanding
- High accuracy for rare entities

**D. Rule-based Extraction**
- Clinical note patterns
- Temporal expressions
- Vital sign extraction rules
- Medication dosage patterns

**Input**: Preprocessed text
**Output**: List of candidate entities with positions and confidence scores

**Integration Points**:
- Uses BioBERT embedding generator (from `src/embeddings`)
- Integrates with medical terminology validator
- Passes entities to post-processing

---

#### 2.3 Post-processing Module (`post_processing.py`)
**Purpose**: Refine and enhance extracted entities

**Responsibilities**:
- **Entity Normalization**: Standardize entity text (e.g., "BP" → "blood pressure")
- **Confidence Scoring**: Calculate confidence based on multiple signals
- **Deduplication**: Remove overlapping/duplicate entities
- **Context Enrichment**: Add surrounding context to entities
- **Entity Linking**: Link entities to medical knowledge bases

**Input**: Raw extracted entities
**Output**: Refined, normalized entities with metadata

**Integration Points**:
- Receives entities from extraction engine
- Uses terminology validator for normalization
- Passes to validation module

---

#### 2.4 Validation Module

**A. Medical Terminology Validator (`medical_terminology.py`)**
**Purpose**: Validate and correct medical terms

**Responsibilities**:
- Verify entity spelling against medical dictionaries
- Suggest corrections for misspellings
- Normalize terminology (e.g., "HTN" → "hypertension")
- Expand abbreviations

**B. Spell Checker (`spell_checker.py`)**
**Purpose**: Medical domain-specific spell checking

**Responsibilities**:
- Detect spelling errors in medical terms
- Provide context-aware suggestions
- Handle medical abbreviations

**C. Entity Classification Verification**
**Purpose**: Verify entity type classification

**Responsibilities**:
- Cross-validate entity types
- Resolve ambiguous classifications
- Apply domain-specific rules

**Input**: Extracted entities
**Output**: Validated and corrected entities

---

#### 2.5 Evaluation Module (`evaluation.py`)
**Purpose**: Measure extraction accuracy and performance

**Responsibilities**:
- Calculate precision, recall, F1-score
- Entity-level matching (exact, partial, semantic)
- Performance benchmarking
- Accuracy reporting

**Input**: Extracted entities + ground truth
**Output**: Evaluation metrics

---

### 3. Entity Types

The system extracts the following entity types:

1. **SYMPTOM**: Patient-reported symptoms (fever, cough, pain)
2. **DIAGNOSIS**: Medical diagnoses (pneumonia, diabetes)
3. **MEDICATION**: Drugs and medications (aspirin, antibiotics)
4. **VITAL_SIGN**: Vital signs (blood pressure, heart rate, temperature)
5. **PROCEDURE**: Medical procedures (surgery, tests)
6. **BODY_PART**: Anatomical locations (chest, arm, lung)
7. **CONDITION**: Medical conditions (chronic diseases)
8. **DISEASE**: Specific diseases
9. **LAB_TEST**: Laboratory tests

### 4. Data Structures

#### MedicalEntity
```python
@dataclass
class MedicalEntity:
    text: str                    # Original entity text
    entity_type: EntityType      # Entity classification
    start_pos: int              # Start position in text
    end_pos: int                # End position in text
    confidence: float           # Confidence score (0.0-1.0)
    normalized_form: str        # Normalized/standardized form
    context: str                # Surrounding context
    metadata: Dict[str, Any]    # Additional metadata
```

#### ExtractionResult
```python
@dataclass
class ExtractionResult:
    entities: List[MedicalEntity]
    processing_time: float
    confidence_scores: Dict[EntityType, float]
    extraction_method: str      # "pattern", "dictionary", "ml", "hybrid"
    metadata: Dict[str, Any]
```

### 5. Integration Points

#### 5.1 With Transcription Module
- Receives transcripts from `DeepgramClient`
- Handles speaker-segmented transcripts
- Processes real-time streaming transcripts

#### 5.2 With SOAP Generator
- Provides extracted entities to `SOAPGenerator`
- Enables structured SOAP note generation
- Supports field-specific entity filtering

#### 5.3 With Embedding System
- Uses `BioBERTEmbeddingGenerator` for ML-based NER
- Generates embeddings for entity normalization
- Supports semantic entity matching

#### 5.4 With Storage System
- Stores extracted entities in Qdrant
- Enables entity-based case retrieval
- Supports entity filtering in searches

### 6. Performance Requirements

- **Accuracy**: >90% precision and recall for all entity types
- **Latency**: <500ms for typical consultation transcript (1000-2000 words)
- **Throughput**: Support real-time processing (1 transcript/second)
- **Scalability**: Handle batch processing for historical transcripts

### 7. Extensibility

#### Adding New Entity Types
1. Add entity type to `EntityType` enum
2. Create extraction patterns/rules
3. Add to medical dictionary
4. Update evaluation metrics

#### Adding New Models
1. Implement model interface
2. Integrate with extraction engine
3. Add confidence scoring
4. Update configuration

#### Adding New Languages
1. Create language-specific dictionaries
2. Train/fine-tune models for target language
3. Update preprocessing rules
4. Add language detection

### 8. Configuration

The system supports configuration via:
- Environment variables
- Configuration files (YAML/JSON)
- Runtime parameters

**Key Configuration Options**:
- Model selection (pattern-only, ML-based, hybrid)
- Confidence thresholds per entity type
- Dictionary sources
- Processing mode (real-time vs batch)

### 9. Error Handling

- **Graceful Degradation**: Fallback to simpler methods if ML models fail
- **Partial Results**: Return entities even if some extraction methods fail
- **Logging**: Comprehensive logging for debugging and monitoring
- **Validation**: Input validation and error reporting

### 10. Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test full pipeline with sample transcripts
- **Accuracy Tests**: Validate >90% accuracy requirement
- **Performance Tests**: Measure latency and throughput
- **Edge Case Tests**: Handle malformed input, missing data

### 11. Future Enhancements

- **Active Learning**: Improve models with user feedback
- **Multi-modal Extraction**: Extract from images (X-rays, lab reports)
- **Temporal Extraction**: Extract time-based information
- **Relationship Extraction**: Extract entity relationships
- **Clinical Coding**: Automatic ICD-10/SNOMED CT coding

## Implementation Phases

### Phase 1: Foundation (Current)
- ✅ Basic pattern matching
- ✅ Dictionary lookup
- ✅ Entity data structures
- ✅ Basic validation

### Phase 2: ML Integration
- ⏳ BioBERT NER model integration
- ⏳ Hybrid extraction (pattern + ML)
- ⏳ Confidence scoring
- ⏳ Model fine-tuning

### Phase 3: Enhancement
- ⏳ Advanced normalization
- ⏳ Entity linking
- ⏳ Relationship extraction
- ⏳ Performance optimization

### Phase 4: Production
- ⏳ Comprehensive testing
- ⏳ Documentation
- ⏳ Monitoring and logging
- ⏳ Deployment

## Dependencies

### External Libraries
- `transformers`: For BioBERT model
- `torch`: PyTorch for ML models
- `spacy`: Optional NLP preprocessing
- `scispacy`: Medical NLP models

### Internal Modules
- `src.embeddings.BioBERTEmbeddingGenerator`: For ML-based extraction
- `src.transcription.DeepgramClient`: For transcript input
- `src.entity_extraction.soap_generator`: For SOAP integration

## Security and Privacy

- **HIPAA Compliance**: No PII stored in entity extraction
- **Data Encryption**: Encrypt sensitive medical data
- **Audit Logging**: Log all entity extractions
- **Access Control**: Restrict access to extraction results

## Monitoring and Metrics

- **Accuracy Metrics**: Track precision/recall per entity type
- **Performance Metrics**: Latency, throughput
- **Error Rates**: Failed extractions, model errors
- **Usage Statistics**: Entity types extracted, volume

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-16  
**Author**: HygiaAI Development Team

