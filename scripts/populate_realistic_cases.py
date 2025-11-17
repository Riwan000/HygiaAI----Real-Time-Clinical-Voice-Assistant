#!/usr/bin/env python3
"""
Populate Realistic Clinical Cases

This script populates Qdrant with realistic clinical cases based on common
rural healthcare scenarios in India. All data is anonymized and realistic.

Run this before demonstrating the system.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
from src.embeddings.text_embeddings import BioBERTEmbeddingGenerator
from src.entity_extraction.soap_generator import SOAPGenerator
from src.models.case_models import CaseMetadata

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Realistic Clinical Cases for Rural India
REALISTIC_CASES = [
    {
        "transcript": """Patient is a 45-year-old male farmer from Wayanad, Kerala. He presents with chief complaint of persistent cough for the past 3 weeks, associated with low-grade fever and occasional chest discomfort. The cough is productive with yellowish sputum, worse in the mornings. He reports mild shortness of breath on exertion. No history of smoking. Patient works in paddy fields and has been exposed to agricultural dust. Past medical history is unremarkable. No known drug allergies. On examination, vital signs show: Blood pressure 130/85 mmHg, heart rate 88 bpm, respiratory rate 20 per minute, temperature 37.8°C, oxygen saturation 96% on room air. Physical examination reveals clear breath sounds bilaterally with occasional scattered rhonchi. No wheezing or rales. Cardiovascular examination is normal. Abdomen is soft and non-tender. Assessment: Acute bronchitis, likely secondary to environmental exposure. Plan: Prescribed Amoxicillin 500mg three times daily for 5 days, cough suppressant syrup, advised rest and increased fluid intake. Follow-up scheduled in one week if symptoms persist. Patient counseled on avoiding dust exposure during work.""",
        "metadata": {
            "age_group": "adult",
            "region": "Wayanad, Kerala",
            "diagnosis": "Acute Bronchitis",
            "outcome": "improved",
            "comorbidities": [],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        }
    },
    {
        "transcript": """28-year-old female from rural Tamil Nadu presents with chief complaint of high-grade fever for 4 days, associated with severe headache, body aches, and joint pain. She also reports nausea and loss of appetite. Patient denies cough, chest pain, or difficulty breathing. No history of travel outside the district. Physical examination shows: Temperature 39.2°C, blood pressure 110/70 mmHg, heart rate 102 bpm, respiratory rate 18 per minute. Patient appears fatigued but alert. Skin examination reveals no rash. Cardiovascular and respiratory examinations are within normal limits. Abdomen is soft, non-tender. Laboratory tests ordered: Complete blood count, malaria rapid diagnostic test, dengue NS1 antigen test. Assessment: Febrile illness, rule out dengue fever or malaria. Plan: Symptomatic treatment with Paracetamol 500mg every 6 hours for fever and pain. Advised rest and oral rehydration. Laboratory tests sent. Patient instructed to return immediately if symptoms worsen or if bleeding manifestations appear. Follow-up in 2 days.""",
        "metadata": {
            "age_group": "adult",
            "region": "Tamil Nadu",
            "diagnosis": "Febrile Illness - Suspected Dengue",
            "outcome": "under_treatment",
            "comorbidities": [],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        }
    },
    {
        "transcript": """55-year-old male patient from rural Maharashtra with known history of type 2 diabetes mellitus for 8 years presents with complaint of non-healing ulcer on the right foot for the past 6 weeks. The ulcer started as a small blister after wearing tight footwear and has progressively worsened. Patient reports pain at the ulcer site, especially at night. He has been taking Metformin 500mg twice daily but admits to irregular blood sugar monitoring. On examination, vital signs: Blood pressure 140/90 mmHg, heart rate 78 bpm. Right foot examination reveals a 3cm x 2cm ulcer on the plantar aspect with surrounding erythema and mild discharge. No signs of deep tissue involvement. Peripheral pulses are palpable. Sensation is reduced in both feet. Random blood sugar: 280 mg/dL. Assessment: Diabetic foot ulcer, poorly controlled diabetes. Plan: Wound care with daily dressing changes, prescribed Ciprofloxacin 500mg twice daily for 7 days, increased Metformin to 1000mg twice daily, referred to diabetic foot care clinic. Patient counseled on importance of blood sugar control, proper foot care, and regular monitoring. Follow-up in one week.""",
        "metadata": {
            "age_group": "adult",
            "region": "Maharashtra",
            "diagnosis": "Diabetic Foot Ulcer",
            "outcome": "under_treatment",
            "comorbidities": ["Type 2 Diabetes Mellitus"],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        }
    },
    {
        "transcript": """35-year-old pregnant woman in her 28th week of gestation from rural Odisha presents with complaint of persistent vomiting for the past 5 days, unable to keep any food or fluids down. She reports feeling weak and dizzy. Patient has had 3 previous normal deliveries. Current pregnancy has been uncomplicated until now. On examination: Blood pressure 100/60 mmHg, heart rate 110 bpm, temperature 37.1°C. Patient appears dehydrated with dry mucous membranes. Abdominal examination shows gravid uterus appropriate for gestational age, fetal heart rate 140 bpm. Urine ketones: positive. Assessment: Hyperemesis gravidarum with dehydration. Plan: Intravenous fluid replacement with normal saline, antiemetic medication Ondansetron 4mg intravenous, advised small frequent meals, oral rehydration solution. Patient admitted for observation and hydration. Obstetric consultation arranged. Follow-up in 2 days.""",
        "metadata": {
            "age_group": "adult",
            "region": "Odisha",
            "diagnosis": "Hyperemesis Gravidarum",
            "outcome": "improved",
            "comorbidities": ["Pregnancy - 28 weeks"],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        }
    },
    {
        "transcript": """12-year-old boy from rural Karnataka brought by parents with complaint of recurrent episodes of wheezing and shortness of breath for the past 2 months. Episodes occur 2-3 times per week, worse at night and with physical activity. Patient has been unable to participate in school sports. Family history reveals mother has asthma. On examination: Blood pressure 100/65 mmHg, heart rate 95 bpm, respiratory rate 24 per minute, oxygen saturation 94% on room air. Chest examination reveals bilateral expiratory wheezing. No signs of respiratory distress at rest. Peak expiratory flow rate: 65% of predicted. Assessment: Bronchial asthma, moderate persistent. Plan: Prescribed Salbutamol inhaler 100mcg as needed for acute episodes, Beclomethasone inhaler 100mcg twice daily for maintenance. Spacer device provided. Patient and parents counseled on asthma triggers, proper inhaler technique, and when to seek emergency care. Follow-up in 2 weeks to assess response to treatment.""",
        "metadata": {
            "age_group": "pediatric",
            "region": "Karnataka",
            "diagnosis": "Bronchial Asthma",
            "outcome": "improved",
            "comorbidities": [],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        }
    },
    {
        "transcript": """60-year-old female from rural West Bengal with history of hypertension presents with complaint of gradual onset of memory problems and confusion over the past 6 months. Family reports patient has been forgetting recent events, repeating questions, and having difficulty with daily tasks. Patient has been taking Amlodipine 5mg once daily for hypertension. On examination: Blood pressure 150/95 mmHg, heart rate 82 bpm. Mini-Mental State Examination score: 22/30, indicating mild cognitive impairment. Neurological examination is otherwise normal. No focal deficits. Assessment: Mild cognitive impairment, possible early dementia. Hypertension not well controlled. Plan: Increased Amlodipine to 10mg once daily, prescribed Donepezil 5mg once daily, advised regular mental exercises and social engagement. Referred to neurology for further evaluation and brain imaging. Family counseling provided on safety measures and support strategies. Follow-up in one month.""",
        "metadata": {
            "age_group": "elderly",
            "region": "West Bengal",
            "diagnosis": "Mild Cognitive Impairment",
            "outcome": "under_treatment",
            "comorbidities": ["Hypertension"],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        }
    },
    {
        "transcript": """8-year-old girl from rural Rajasthan brought with complaint of abdominal pain and loose stools for 3 days. Stools are watery, 5-6 times per day, no blood or mucus. Patient also has low-grade fever. No vomiting. Patient appears mildly dehydrated. On examination: Temperature 37.6°C, heart rate 105 bpm, blood pressure 95/60 mmHg. Abdomen is soft with mild periumbilical tenderness, no guarding or rigidity. Bowel sounds are hyperactive. Assessment: Acute gastroenteritis, likely viral. Plan: Oral rehydration solution advised, continued breastfeeding, prescribed Zinc sulfate 20mg once daily for 14 days. Advised to return if signs of severe dehydration develop or if symptoms persist beyond 5 days. Follow-up in 2 days if not improved.""",
        "metadata": {
            "age_group": "pediatric",
            "region": "Rajasthan",
            "diagnosis": "Acute Gastroenteritis",
            "outcome": "recovered",
            "comorbidities": [],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        }
    },
    {
        "transcript": """42-year-old male construction worker from rural Gujarat presents with complaint of lower back pain for the past 2 weeks. Pain started after lifting heavy materials at work. Pain is localized to lower back, radiates to right leg, worse with standing and bending. Patient has difficulty sleeping due to pain. On examination: Blood pressure 125/80 mmHg, heart rate 76 bpm. Straight leg raise test positive on right side at 45 degrees. Neurological examination shows normal strength and sensation. Assessment: Lumbar strain with right sciatica. Plan: Prescribed Ibuprofen 400mg three times daily for 5 days, advised rest, hot fomentation, and back strengthening exercises. Patient counseled on proper lifting techniques. Return to work after 1 week if improved. Follow-up in one week.""",
        "metadata": {
            "age_group": "adult",
            "region": "Gujarat",
            "diagnosis": "Lumbar Strain with Sciatica",
            "outcome": "improved",
            "comorbidities": [],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat()
        }
    },
    {
        "transcript": """30-year-old female from rural Andhra Pradesh presents with complaint of irregular menstrual cycles and excessive bleeding during periods for the past 6 months. Menstrual cycles occur every 20-45 days, bleeding lasts 8-10 days with heavy flow. Patient reports fatigue and weakness. On examination: Blood pressure 110/70 mmHg, heart rate 98 bpm, pallor present. Abdominal examination is normal. Pelvic examination deferred. Hemoglobin: 8.5 g/dL, indicating moderate anemia. Assessment: Menorrhagia with iron deficiency anemia. Plan: Prescribed Iron supplements, started on combined oral contraceptive pills for cycle regulation, advised to increase iron-rich foods in diet. Referred to gynecology for further evaluation including ultrasound. Follow-up in one month with repeat hemoglobin check.""",
        "metadata": {
            "age_group": "adult",
            "region": "Andhra Pradesh",
            "diagnosis": "Menorrhagia with Iron Deficiency Anemia",
            "outcome": "under_treatment",
            "comorbidities": [],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        }
    },
    {
        "transcript": """65-year-old male farmer from rural Punjab with history of chronic obstructive pulmonary disease presents with complaint of increased shortness of breath and productive cough for the past week. Cough produces greenish sputum. Patient is a former smoker, quit 5 years ago. On examination: Blood pressure 130/85 mmHg, heart rate 92 bpm, respiratory rate 24 per minute, oxygen saturation 90% on room air. Chest examination reveals bilateral expiratory wheezing and scattered rhonchi. Patient appears in mild respiratory distress. Assessment: COPD exacerbation, likely infective. Plan: Prescribed Amoxicillin-Clavulanate 625mg three times daily for 7 days, Salbutamol nebulization, oral Prednisolone 30mg once daily for 5 days. Oxygen therapy initiated. Patient counseled on smoking cessation and inhaler technique. Follow-up in 3 days.""",
        "metadata": {
            "age_group": "elderly",
            "region": "Punjab",
            "diagnosis": "COPD Exacerbation",
            "outcome": "improved",
            "comorbidities": ["Chronic Obstructive Pulmonary Disease"],
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
        }
    }
]


def populate_realistic_cases():
    """Populate Qdrant with realistic clinical cases"""
    print("=" * 80)
    print("  Populating Realistic Clinical Cases")
    print("=" * 80)
    print()
    
    # Initialize components
    print("🔧 Initializing components...")
    
    # Qdrant storage
    qdrant_storage = QdrantStorage(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6334")),
        collection_name="hygiaai_clinical_cases",
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
    
    # SOAP generator
    print("🔧 Initializing SOAP generator...")
    try:
        soap_generator = SOAPGenerator()
        print("✅ SOAP generator initialized")
    except Exception as e:
        print(f"⚠️  SOAP generator initialization failed: {e}")
        soap_generator = None
    
    print()
    
    # Process each case
    print("📋 Processing realistic clinical cases...")
    print()
    
    stored_count = 0
    for i, case_data in enumerate(REALISTIC_CASES, 1):
        print(f"📄 Case {i}/{len(REALISTIC_CASES)}: {case_data['metadata']['diagnosis']}")
        
        try:
            # Generate embedding
            if embedding_generator:
                embedding = embedding_generator.generate_embedding(case_data["transcript"])
            else:
                embedding = [0.0] * 768
            
            # Generate SOAP note
            soap_note = None
            if soap_generator:
                try:
                    soap_result = soap_generator.generate_soap_note(case_data["transcript"])
                    if soap_result:
                        soap_note = {
                            "subjective": soap_result.subjective,
                            "objective": soap_result.objective,
                            "assessment": soap_result.assessment,
                            "plan": soap_result.plan
                        }
                except Exception as e:
                    logger.warning(f"SOAP generation failed: {e}")
            
            # Prepare metadata
            metadata = CaseMetadata(
                age_group=case_data["metadata"]["age_group"],
                region=case_data["metadata"]["region"],
                diagnosis=case_data["metadata"]["diagnosis"],
                outcome=case_data["metadata"]["outcome"],
                comorbidities=case_data["metadata"].get("comorbidities", []),
                timestamp=case_data["metadata"]["timestamp"]
            )
            
            # Store in Qdrant
            stored_id = qdrant_storage.store_transcript(
                transcript_data={
                    "transcript": case_data["transcript"],
                    "soap_note": soap_note,
                    "diagnosis": case_data["metadata"]["diagnosis"],
                    "outcome": case_data["metadata"]["outcome"]
                },
                embedding=embedding,
                metadata={
                    "session_id": f"realistic-case-{i:03d}",
                    "patient_id": f"patient-{i:03d}",
                    "timestamp": case_data["metadata"]["timestamp"],
                    "modality": "text",
                    **metadata.dict()
                }
            )
            
            if stored_id:
                stored_count += 1
                print(f"   ✅ Stored successfully (ID: {stored_id})")
            else:
                print(f"   ⚠️  Storage failed")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Summary
    print("=" * 80)
    print("  Summary")
    print("=" * 80)
    print(f"✅ Cases processed: {len(REALISTIC_CASES)}")
    print(f"✅ Cases stored: {stored_count}")
    print()
    print("Realistic clinical cases are now available for:")
    print("   - Similar case retrieval")
    print("   - SOAP note generation")
    print("   - Analytics and trend analysis")
    print("   - Knowledge intelligence")
    print("=" * 80)


if __name__ == "__main__":
    populate_realistic_cases()

