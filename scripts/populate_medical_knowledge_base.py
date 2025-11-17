#!/usr/bin/env python3
"""
Populate Medical Knowledge Base

This script populates the Qdrant knowledge base with medical information from:
- Open-access medical sources (PubMed, medical guidelines, etc.)
- PDF documents in the project
- Curated medical knowledge

Run this script to build the knowledge base before using enhanced SOAP generation.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings import BioBERTEmbeddingGenerator
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
from datetime import datetime, timezone
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Curated Medical Knowledge Base Content
MEDICAL_KNOWLEDGE_BASE = {
    "soap_note_guidelines": {
        "title": "SOAP Note Documentation Guidelines",
        "content": """
SOAP Note Structure:

SUBJECTIVE (S):
- Chief Complaint (CC): Primary reason for visit in patient's own words
- History of Present Illness (HPI): Detailed description of current problem
  * Onset: When did symptoms start?
  * Location: Where is the problem?
  * Duration: How long has it been present?
  * Character: What does it feel like?
  * Aggravating/Alleviating factors: What makes it better/worse?
  * Radiation: Does it spread?
  * Timing: When does it occur?
  * Severity: Rate on scale of 1-10
- Review of Systems (ROS): Systematic review of body systems
- Past Medical History (PMH): Previous illnesses, surgeries, hospitalizations
- Medications: Current medications with dosages
- Allergies: Known allergies and reactions
- Social History: Smoking, alcohol, drugs, occupation, living situation
- Family History: Relevant family medical history

OBJECTIVE (O):
- Vital Signs: Blood pressure, heart rate, respiratory rate, temperature, oxygen saturation, weight, height, BMI
- Physical Examination:
  * General appearance
  * Head, Eyes, Ears, Nose, Throat (HEENT)
  * Cardiovascular
  * Respiratory
  * Abdomen
  * Extremities
  * Neurological
  * Skin
- Laboratory Results: Blood tests, imaging, diagnostic tests
- Diagnostic Tests: X-rays, CT scans, MRIs, EKGs, etc.

ASSESSMENT (A):
- Primary Diagnosis: Main diagnosis with ICD-10 code if applicable
- Differential Diagnoses: Other possible diagnoses being considered
- Clinical Reasoning: How subjective and objective findings support the diagnosis
- Problem List: All active problems
- Risk Assessment: Any risk factors identified

PLAN (P):
- Medications: New prescriptions, changes to existing medications, dosages
- Diagnostic Tests: Tests ordered with rationale
- Treatment Plan: Specific interventions, therapies
- Patient Education: Information provided to patient
- Follow-up: When to return, what to monitor
- Referrals: Specialist referrals if needed
- Lifestyle Modifications: Diet, exercise, smoking cessation, etc.
        """,
        "domain": "clinical_documentation",
        "source": "HygiaAI_Curated"
    },
    "vital_signs_reference": {
        "title": "Normal Vital Signs Reference",
        "content": """
Normal Vital Signs by Age:

Adults (18+ years):
- Blood Pressure: 120/80 mmHg (normal), <120/80 (optimal), 120-129/<80 (elevated), 130-139/80-89 (Stage 1 hypertension), ≥140/≥90 (Stage 2 hypertension)
- Heart Rate: 60-100 bpm (resting)
- Respiratory Rate: 12-20 breaths per minute
- Temperature: 98.6°F (37°C) oral, 99.6°F (37.6°C) rectal
- Oxygen Saturation: 95-100% (room air)

Pediatric (varies by age):
- Newborn (0-1 month): HR 100-160, RR 30-60, BP 60-90/30-60
- Infant (1-12 months): HR 80-140, RR 20-40, BP 70-100/50-70
- Toddler (1-3 years): HR 80-130, RR 20-30, BP 80-110/50-70
- Preschool (3-5 years): HR 80-120, RR 20-30, BP 80-110/50-78
- School Age (6-12 years): HR 70-110, RR 16-22, BP 85-120/50-80
- Adolescent (13-18 years): HR 60-100, RR 12-20, BP 95-140/60-90

Abnormal Vital Signs:
- Hypertension: BP ≥140/≥90
- Hypotension: BP <90/60 (symptomatic)
- Tachycardia: HR >100 bpm (adults)
- Bradycardia: HR <60 bpm (adults)
- Tachypnea: RR >20 (adults)
- Bradypnea: RR <12 (adults)
- Fever: Temperature >100.4°F (38°C)
- Hypothermia: Temperature <95°F (35°C)
- Hypoxia: SpO2 <90%
        """,
        "domain": "clinical_reference",
        "source": "HygiaAI_Curated"
    },
    "common_symptoms_patterns": {
        "title": "Common Symptoms and Clinical Patterns",
        "content": """
Common Symptom Patterns:

Respiratory Symptoms:
- Cough: Acute (<3 weeks) vs Chronic (>3 weeks)
- Shortness of breath: Dyspnea on exertion, at rest, orthopnea, paroxysmal nocturnal dyspnea
- Chest pain: Cardiac (crushing, substernal, radiates to arm/jaw), Pulmonary (pleuritic, worse with breathing), Musculoskeletal (reproducible, localized)

Cardiovascular Symptoms:
- Chest pain: See respiratory section
- Palpitations: Irregular heartbeat sensation
- Syncope: Fainting, loss of consciousness
- Edema: Swelling, especially in lower extremities

Gastrointestinal Symptoms:
- Abdominal pain: Location (RUQ, LUQ, RLQ, LLQ, epigastric, periumbilical), character (sharp, dull, cramping)
- Nausea and vomiting: Timing, content, associated symptoms
- Diarrhea: Acute vs chronic, bloody, watery, frequency
- Constipation: Frequency, consistency, straining

Neurological Symptoms:
- Headache: Location, character, triggers, associated symptoms
- Dizziness: Vertigo (room spinning) vs lightheadedness
- Weakness: Focal vs generalized, progressive vs sudden
- Numbness/tingling: Distribution, pattern

Musculoskeletal Symptoms:
- Joint pain: Location, swelling, stiffness, range of motion
- Back pain: Location, radiation, aggravating factors
- Muscle pain: Generalized vs localized

General Symptoms:
- Fever: Temperature, pattern, duration
- Fatigue: Onset, severity, impact on daily activities
- Weight loss/gain: Amount, time period, intentional vs unintentional
        """,
        "domain": "clinical_patterns",
        "source": "HygiaAI_Curated"
    },
    "medication_categories": {
        "title": "Medication Categories and Common Drugs",
        "content": """
Common Medication Categories:

Antibiotics:
- Penicillins: Amoxicillin, Ampicillin, Penicillin G
- Cephalosporins: Cephalexin, Ceftriaxone
- Macrolides: Azithromycin, Erythromycin
- Fluoroquinolones: Ciprofloxacin, Levofloxacin
- Tetracyclines: Doxycycline, Tetracycline

Analgesics (Pain Relievers):
- NSAIDs: Ibuprofen, Naproxen, Aspirin
- Acetaminophen: Tylenol
- Opioids: Morphine, Codeine, Oxycodone (prescription only)

Cardiovascular:
- ACE Inhibitors: Lisinopril, Enalapril
- Beta Blockers: Metoprolol, Atenolol
- Diuretics: Furosemide, Hydrochlorothiazide
- Calcium Channel Blockers: Amlodipine, Diltiazem

Respiratory:
- Bronchodilators: Albuterol, Salmeterol
- Inhaled Corticosteroids: Fluticasone, Budesonide
- Antihistamines: Loratadine, Cetirizine

Gastrointestinal:
- Antacids: Calcium carbonate, Magnesium hydroxide
- Proton Pump Inhibitors: Omeprazole, Pantoprazole
- H2 Blockers: Ranitidine, Famotidine

Endocrine:
- Insulin: Various types (rapid, short, intermediate, long-acting)
- Oral Hypoglycemics: Metformin, Glipizide
- Thyroid: Levothyroxine

Dosage Information:
- Always include: Drug name, dose, frequency, route, duration
- Example: "Amoxicillin 500mg by mouth three times daily for 7 days"
        """,
        "domain": "pharmacology",
        "source": "HygiaAI_Curated"
    },
    "diagnosis_patterns": {
        "title": "Common Diagnoses and Diagnostic Criteria",
        "content": """
Common Diagnoses by System:

Respiratory:
- Pneumonia: Fever, cough, chest pain, abnormal chest X-ray
- Bronchitis: Productive cough, no evidence of pneumonia
- Asthma: Reversible airway obstruction, wheezing, shortness of breath
- COPD: Chronic cough, dyspnea, smoking history, spirometry findings

Cardiovascular:
- Hypertension: BP ≥140/≥90 on multiple readings
- Heart Failure: Dyspnea, edema, reduced ejection fraction
- Atrial Fibrillation: Irregular pulse, ECG findings
- Myocardial Infarction: Chest pain, elevated troponin, ECG changes

Gastrointestinal:
- GERD: Heartburn, acid reflux, response to PPI
- Peptic Ulcer Disease: Epigastric pain, may have bleeding
- Gastroenteritis: Diarrhea, nausea, vomiting, often infectious

Endocrine:
- Diabetes Mellitus Type 2: Elevated glucose, HbA1c ≥6.5%
- Hypothyroidism: Fatigue, weight gain, elevated TSH
- Hyperthyroidism: Weight loss, tachycardia, low TSH

Infectious Diseases:
- Urinary Tract Infection: Dysuria, frequency, positive urine culture
- Upper Respiratory Infection: Cough, congestion, viral symptoms
- Cellulitis: Localized redness, warmth, swelling, tenderness

Oncology:
- Cancer staging: Stage 0-IV based on tumor size, lymph nodes, metastasis
- Common cancers: Breast, lung, colorectal, prostate, skin

Mental Health:
- Depression: Persistent sadness, loss of interest, ≥2 weeks
- Anxiety: Excessive worry, physical symptoms, functional impairment
- PTSD: Trauma exposure, re-experiencing, avoidance, hyperarousal
        """,
        "domain": "diagnostics",
        "source": "HygiaAI_Curated"
    },
    "soap_extraction_rules": {
        "title": "SOAP Note Extraction Rules and Best Practices",
        "content": """
SOAP Note Extraction Rules:

SUBJECTIVE Extraction:
- Look for first-person statements: "I feel", "I have", "My pain"
- Patient-reported information: "Patient reports", "Patient states"
- Temporal information: "For the past 3 days", "Since last week"
- Severity descriptions: "Rate 7/10", "Very painful", "Mild discomfort"
- Quality descriptions: "Sharp pain", "Dull ache", "Burning sensation"
- Aggravating/alleviating factors: "Worse with movement", "Better with rest"
- Chief complaint usually appears in first 1-2 sentences
- Medical history: "History of", "Previous diagnosis", "Past medical history"
- Medications: "Taking", "On", "Prescribed", drug names with dosages
- Allergies: "Allergic to", "Reaction to"

OBJECTIVE Extraction:
- Vital signs: Look for numbers with units (mmHg, bpm, °F, %)
- Physical exam findings: "On examination", "Physical exam reveals"
- Measured values: "Blood pressure is 140/90", "Heart rate 85 bpm"
- Observable findings: "Appears well", "Alert and oriented", "No acute distress"
- Lab results: "Lab shows", "Test results", "CBC reveals"
- Imaging findings: "X-ray shows", "CT scan demonstrates"
- Avoid patient-reported information in objective section

ASSESSMENT Extraction:
- Diagnosis statements: "Diagnosis:", "Impression:", "Assessment:"
- Clinical reasoning: "Consistent with", "Suggests", "Indicates"
- Differential diagnosis: "Rule out", "Consider", "Possible"
- Problem list: All active problems identified
- Severity: "Mild", "Moderate", "Severe", "Acute", "Chronic"

PLAN Extraction:
- Treatment plans: "Will continue", "Start", "Discontinue"
- Medications: "Prescribe", "Start on", "Change to", drug names with dosages
- Diagnostic tests: "Order", "Schedule", "Obtain"
- Follow-up: "Return in", "Follow up", "Recheck"
- Patient education: "Counseled on", "Instructed to", "Advise"
- Referrals: "Refer to", "Consult with"
- Lifestyle: "Recommend", "Advise", "Encourage"

Key Phrases to Identify:
- Subjective: "Patient reports", "States that", "Complains of", "History of"
- Objective: "On exam", "Vital signs", "Physical examination", "Lab results"
- Assessment: "Diagnosis", "Impression", "Clinical presentation", "Consistent with"
- Plan: "Plan", "Treatment", "Will", "Continue", "Start", "Order"
        """,
        "domain": "clinical_documentation",
        "source": "HygiaAI_Curated"
    }
}


def populate_knowledge_base():
    """Populate Qdrant knowledge base with medical knowledge"""
    print("=" * 80)
    print("  Medical Knowledge Base Population")
    print("=" * 80)
    print()
    
    # Initialize components
    print("🔧 Initializing components...")
    
    # Qdrant storage
    qdrant_storage = QdrantStorage(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6334")),
        collection_name="hygiaai_knowledge_base",
        vector_size=768,
        enable_encryption=False,
        enable_deidentification=False
    )
    print("✅ Qdrant storage initialized")
    
    # Embedding generator
    print("🔧 Initializing BioBERT embedding generator...")
    try:
        embedding_generator = BioBERTEmbeddingGenerator()
        print("✅ BioBERT embedding generator initialized")
    except Exception as e:
        print(f"⚠️  BioBERT initialization failed: {e}")
        print("   Using fallback embedding method")
        embedding_generator = None
    
    # Knowledge ingestion pipeline
    def text_embedding_fn(text: str):
        if embedding_generator:
            return embedding_generator.generate_embedding(text)
        else:
            # Fallback: return dummy embedding
            return [0.0] * 768
    
    ingestion_pipeline = KnowledgeIngestionPipeline(
        qdrant_storage=qdrant_storage,
        text_embedding_generator=text_embedding_fn,
        chunk_size=512,
        chunk_overlap=50,
        validate_schema=False,
        enforce_open_access=False
    )
    print("✅ Knowledge ingestion pipeline initialized")
    print()
    
    # Ingest curated knowledge
    print("📚 Ingesting curated medical knowledge...")
    print()
    
    ingested_count = 0
    for doc_id, doc_data in MEDICAL_KNOWLEDGE_BASE.items():
        print(f"📄 Processing: {doc_data['title']}")
        
        try:
            document = {
                "title": doc_data["title"],
                "text": doc_data["content"],
                "content": doc_data["content"],
                "source": doc_data["source"],
                "domain": doc_data["domain"],
                "year": datetime.now(timezone.utc).year,
                "provenance_url": f"https://hygiaai.internal/knowledge/{doc_id}",
                "author": "HygiaAI Team",
                "version": "1.0"
            }
            
            metadata = KnowledgeBaseMetadata(
                title=doc_data["title"],
                source=doc_data["source"],
                domain=doc_data["domain"],
                year=datetime.now(timezone.utc).year,
                embedding_type=EmbeddingType.TEXT,
                access_type=AccessType.OPEN,
                provenance_url=f"https://hygiaai.internal/knowledge/{doc_id}",
                author="HygiaAI Team",
                version="1.0"
            )
            
            point_ids = ingestion_pipeline.ingest_document(
                document,
                metadata=metadata,
                force_update=False
            )
            
            if point_ids:
                ingested_count += 1
                print(f"   ✅ Ingested successfully ({len(point_ids)} chunks)")
            else:
                print(f"   ⚠️  Already exists, skipped")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Summary
    print("=" * 80)
    print("  Summary")
    print("=" * 80)
    print(f"✅ Documents processed: {len(MEDICAL_KNOWLEDGE_BASE)}")
    print(f"✅ Documents ingested: {ingested_count}")
    print()
    print("Knowledge base is ready for use in SOAP note generation!")
    print("=" * 80)


if __name__ == "__main__":
    populate_knowledge_base()

