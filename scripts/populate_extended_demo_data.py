#!/usr/bin/env python3
"""
Populate Extended Demo Data - 50 Patients with Timelines

This script populates Qdrant with 50 realistic patients, each with multiple
timeline entries (visits, follow-ups, lab results) to create a comprehensive
demo dataset for showcasing all features.

Run this script to populate demo data.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random
import uuid

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

# Indian states/regions for realistic distribution
REGIONS = [
    "Kerala", "Tamil Nadu", "Karnataka", "Maharashtra", "Gujarat",
    "Rajasthan", "Punjab", "West Bengal", "Odisha", "Andhra Pradesh",
    "Telangana", "Bihar", "Uttar Pradesh", "Madhya Pradesh", "Assam"
]

# Common diagnoses for rural India
DIAGNOSES = [
    "Acute Bronchitis", "Upper Respiratory Tract Infection", "Acute Gastroenteritis",
    "Hypertension", "Type 2 Diabetes Mellitus", "Anemia", "Malaria",
    "Dengue Fever", "Tuberculosis", "Pneumonia", "Asthma", "COPD Exacerbation",
    "Urinary Tract Infection", "Skin Infection", "Conjunctivitis", "Dental Caries",
    "Musculoskeletal Pain", "Headache", "Fever of Unknown Origin", "Diarrhea"
]

# Age groups
AGE_GROUPS = ["pediatric", "adult", "elderly"]

# Outcomes
OUTCOMES = ["recovered", "improved", "under_treatment", "referred", "stable"]

# Common comorbidities
COMORBIDITIES_POOL = [
    "Type 2 Diabetes Mellitus", "Hypertension", "Asthma", "COPD",
    "Anemia", "Obesity", "Hypothyroidism", "Chronic Kidney Disease"
]


def generate_patient_timeline(patient_id: str, base_date: datetime, num_visits: int = None):
    """Generate a realistic timeline for a single patient"""
    if num_visits is None:
        num_visits = random.randint(2, 6)  # 2-6 visits per patient
    
    age_group = random.choice(AGE_GROUPS)
    region = random.choice(REGIONS)
    
    # Assign consistent comorbidities for chronic conditions
    has_chronic = random.random() < 0.4  # 40% have chronic conditions
    comorbidities = []
    if has_chronic:
        comorbidities = random.sample(COMORBIDITIES_POOL, k=random.randint(1, 2))
    
    # Primary diagnosis (consistent across visits for chronic conditions)
    primary_diagnosis = random.choice(DIAGNOSES)
    
    timeline = []
    current_date = base_date
    
    for visit_num in range(num_visits):
        # Space visits realistically
        if visit_num > 0:
            days_between = random.randint(7, 90) if has_chronic else random.randint(14, 180)
            current_date = current_date - timedelta(days=days_between)
        
        # Visit type
        if visit_num == 0:
            visit_type = "initial"
            diagnosis = primary_diagnosis
        elif visit_num == num_visits - 1:
            visit_type = "followup"
            diagnosis = primary_diagnosis
        else:
            visit_type = random.choice(["followup", "followup", "lab_review", "emergency"])
            # Sometimes different diagnosis for acute issues
            if random.random() < 0.3:
                diagnosis = random.choice(DIAGNOSES)
            else:
                diagnosis = primary_diagnosis
        
        # Generate realistic transcript based on visit type and diagnosis
        transcript = generate_transcript(
            patient_id=patient_id,
            visit_num=visit_num + 1,
            total_visits=num_visits,
            diagnosis=diagnosis,
            visit_type=visit_type,
            age_group=age_group,
            region=region,
            comorbidities=comorbidities,
            days_ago=(datetime.now(timezone.utc) - current_date).days
        )
        
        # Determine outcome based on visit progression
        if visit_num == 0:
            outcome = "under_treatment"
        elif visit_num == num_visits - 1:
            outcome = random.choice(["recovered", "improved", "stable"])
        else:
            outcome = random.choice(["improved", "under_treatment", "stable"])
        
        timeline.append({
            "transcript": transcript,
            "metadata": {
                "patient_id": patient_id,
                "visit_number": visit_num + 1,
                "total_visits": num_visits,
                "visit_type": visit_type,
                "age_group": age_group,
                "region": region,
                "diagnosis": diagnosis,
                "outcome": outcome,
                "comorbidities": comorbidities,
                "timestamp": current_date.isoformat()
            }
        })
    
    return timeline


def generate_transcript(patient_id: str, visit_num: int, total_visits: int, diagnosis: str,
                        visit_type: str, age_group: str, region: str, comorbidities: list,
                        days_ago: int):
    """Generate realistic transcript text"""
    
    # Age based on age group
    if age_group == "pediatric":
        age = random.randint(5, 17)
        gender = random.choice(["male", "female"])
        pronoun = "he" if gender == "male" else "she"
    elif age_group == "elderly":
        age = random.randint(60, 80)
        gender = random.choice(["male", "female"])
        pronoun = "he" if gender == "male" else "she"
    else:
        age = random.randint(18, 59)
        gender = random.choice(["male", "female"])
        pronoun = "he" if gender == "male" else "she"
    
    # Build transcript based on diagnosis and visit type
    transcript_parts = []
    
    # Opening
    if visit_type == "initial":
        transcript_parts.append(
            f"Patient is a {age}-year-old {gender} from rural {region}."
        )
        if comorbidities:
            transcript_parts.append(
                f"Known medical history includes: {', '.join(comorbidities)}."
            )
    else:
        transcript_parts.append(
            f"Follow-up visit for {age}-year-old {gender} patient from {region}."
        )
        if visit_num > 1:
            transcript_parts.append(f"This is visit number {visit_num}.")
    
    # Chief complaint based on diagnosis
    complaint = get_complaint_for_diagnosis(diagnosis, visit_type, visit_num)
    transcript_parts.append(f"Chief complaint: {complaint}")
    
    # History of present illness
    hpi = get_hpi_for_diagnosis(diagnosis, visit_type, days_ago)
    transcript_parts.append(f"History: {hpi}")
    
    # Physical examination
    exam = get_examination_for_diagnosis(diagnosis, age_group)
    transcript_parts.append(f"On examination: {exam}")
    
    # Assessment and plan
    assessment = f"Assessment: {diagnosis}"
    if visit_type != "initial":
        assessment += f", {get_progress_note(visit_num, total_visits)}"
    
    plan = get_plan_for_diagnosis(diagnosis, visit_type, visit_num, total_visits)
    
    transcript_parts.append(assessment)
    transcript_parts.append(f"Plan: {plan}")
    
    return " ".join(transcript_parts)


def get_complaint_for_diagnosis(diagnosis: str, visit_type: str, visit_num: int) -> str:
    """Get chief complaint based on diagnosis"""
    complaints = {
        "Acute Bronchitis": "persistent cough with sputum" if visit_type == "initial" else "cough improving but still present",
        "Upper Respiratory Tract Infection": "sore throat, runny nose, and mild fever" if visit_type == "initial" else "symptoms resolving",
        "Acute Gastroenteritis": "abdominal pain and loose stools" if visit_type == "initial" else "diarrhea improving",
        "Hypertension": "routine follow-up for blood pressure control" if visit_type != "initial" else "elevated blood pressure detected during routine check",
        "Type 2 Diabetes Mellitus": "routine diabetes follow-up" if visit_type != "initial" else "high blood sugar levels",
        "Anemia": "fatigue and weakness" if visit_type == "initial" else "follow-up for anemia treatment",
        "Malaria": "high fever with chills" if visit_type == "initial" else "fever resolved, monitoring",
        "Dengue Fever": "fever, headache, and body pain" if visit_type == "initial" else "symptoms improving",
        "Pneumonia": "cough, fever, and difficulty breathing" if visit_type == "initial" else "respiratory symptoms improving",
        "Asthma": "wheezing and shortness of breath" if visit_type == "initial" else "asthma control review",
    }
    return complaints.get(diagnosis, "presenting for medical consultation")


def get_hpi_for_diagnosis(diagnosis: str, visit_type: str, days_ago: int) -> str:
    """Get history of present illness"""
    if visit_type == "initial":
        durations = {
            "Acute Bronchitis": "symptoms started 2 weeks ago",
            "Upper Respiratory Tract Infection": "symptoms for 3-4 days",
            "Acute Gastroenteritis": "symptoms for 2 days",
            "Hypertension": "detected during routine screening",
            "Type 2 Diabetes Mellitus": "elevated blood sugar detected",
            "Anemia": "symptoms for several weeks",
            "Malaria": "fever started 5 days ago",
            "Dengue Fever": "symptoms started 4 days ago",
            "Pneumonia": "symptoms for 1 week",
            "Asthma": "recurrent episodes over past month",
        }
        return durations.get(diagnosis, "symptoms present")
    else:
        return f"Patient reports improvement since last visit {days_ago} days ago"


def get_examination_for_diagnosis(diagnosis: str, age_group: str) -> str:
    """Get physical examination findings"""
    bp = f"{random.randint(110, 140)}/{random.randint(70, 90)} mmHg"
    hr = f"{random.randint(70, 100)} bpm"
    temp = f"{random.uniform(36.5, 38.5):.1f}°C"
    
    exam_parts = [f"Vital signs: Blood pressure {bp}, heart rate {hr}, temperature {temp}"]
    
    if "Respiratory" in diagnosis or "Bronchitis" in diagnosis or "Pneumonia" in diagnosis:
        exam_parts.append("Chest examination reveals bilateral breath sounds with occasional rhonchi.")
    elif "Gastroenteritis" in diagnosis or "Diarrhea" in diagnosis:
        exam_parts.append("Abdomen is soft with mild tenderness. Bowel sounds hyperactive.")
    elif "Hypertension" in diagnosis:
        exam_parts.append("Cardiovascular examination normal. No signs of end-organ damage.")
    elif "Diabetes" in diagnosis:
        exam_parts.append("General examination normal. Feet examination shows no ulcers.")
    elif "Anemia" in diagnosis:
        exam_parts.append("Pallor present. Cardiovascular examination normal.")
    
    return " ".join(exam_parts)


def get_progress_note(visit_num: int, total_visits: int) -> str:
    """Get progress note based on visit number"""
    progress = visit_num / total_visits
    if progress < 0.4:
        return "treatment ongoing"
    elif progress < 0.7:
        return "showing improvement"
    else:
        return "significant improvement noted"


def get_plan_for_diagnosis(diagnosis: str, visit_type: str, visit_num: int, total_visits: int) -> str:
    """Get treatment plan"""
    if visit_type == "initial":
        plans = {
            "Acute Bronchitis": "Amoxicillin 500mg TID for 5 days, cough syrup, rest",
            "Upper Respiratory Tract Infection": "Symptomatic treatment, Paracetamol for fever",
            "Acute Gastroenteritis": "Oral rehydration solution, Zinc supplements",
            "Hypertension": "Lifestyle modifications, Amlodipine 5mg OD, follow-up in 2 weeks",
            "Type 2 Diabetes Mellitus": "Metformin 500mg BID, dietary counseling, blood sugar monitoring",
            "Anemia": "Iron supplements, dietary advice, repeat hemoglobin in 1 month",
            "Malaria": "Artemisinin-based combination therapy, follow-up in 3 days",
            "Dengue Fever": "Supportive care, Paracetamol, monitor platelet count",
            "Pneumonia": "Amoxicillin-Clavulanate 625mg TID for 7 days, rest",
            "Asthma": "Salbutamol inhaler PRN, Beclomethasone inhaler BID",
        }
        return plans.get(diagnosis, "Treatment as indicated, follow-up scheduled")
    else:
        if visit_num == total_visits:
            return "Continue current treatment, discharge if stable, return if symptoms recur"
        else:
            return "Continue current medications, follow-up in 1-2 weeks"


def populate_extended_demo_data():
    """Populate Qdrant with 50 patients and their timelines"""
    print("=" * 80)
    print("  Populating Extended Demo Data - 50 Patients with Timelines")
    print("=" * 80)
    print()
    
    # Initialize components
    print("🔧 Initializing components...")
    
    qdrant_storage = QdrantStorage(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6334")),
        collection_name="hygiaai_clinical_cases",
        vector_size=768,
        enable_encryption=False,
        enable_deidentification=False
    )
    print("✅ Qdrant storage initialized")
    
    print("🔧 Initializing BioBERT embedding generator...")
    try:
        embedding_generator = BioBERTEmbeddingGenerator()
        print("✅ BioBERT embedding generator initialized")
    except Exception as e:
        print(f"⚠️  BioBERT initialization failed: {e}")
        embedding_generator = None
    
    print("🔧 Initializing SOAP generator...")
    try:
        soap_generator = SOAPGenerator()
        print("✅ SOAP generator initialized")
    except Exception as e:
        print(f"⚠️  SOAP generator initialization failed: {e}")
        soap_generator = None
    
    print()
    
    # Generate 50 patients
    print("📋 Generating 50 patients with timelines...")
    print()
    
    base_date = datetime.now(timezone.utc)
    all_cases = []
    
    for patient_num in range(1, 51):
        patient_id = f"patient_{patient_num:03d}"
        num_visits = random.randint(2, 6)
        
        timeline = generate_patient_timeline(patient_id, base_date, num_visits)
        all_cases.extend(timeline)
        
        if patient_num % 10 == 0:
            print(f"   Generated {patient_num}/50 patients...")
    
    print(f"✅ Generated {len(all_cases)} total case entries")
    print()
    
    # Store all cases
    print("📦 Storing cases in Qdrant...")
    print()
    
    stored_count = 0
    for i, case_data in enumerate(all_cases, 1):
        if i % 20 == 0:
            print(f"   Storing case {i}/{len(all_cases)}...")
        
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
                    # Try different method names
                    if hasattr(soap_generator, 'generate_soap_note'):
                        soap_result = soap_generator.generate_soap_note(case_data["transcript"])
                    elif hasattr(soap_generator, 'generate'):
                        soap_result = soap_generator.generate(case_data["transcript"])
                    else:
                        soap_result = None
                    
                    if soap_result:
                        if hasattr(soap_result, 'subjective'):
                            soap_note = {
                                "subjective": soap_result.subjective,
                                "objective": soap_result.objective,
                                "assessment": soap_result.assessment,
                                "plan": soap_result.plan
                            }
                        elif isinstance(soap_result, dict):
                            soap_note = soap_result
                except Exception as e:
                    logger.debug(f"SOAP generation failed: {e}")
            
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
                    "outcome": case_data["metadata"]["outcome"],
                    "visit_number": case_data["metadata"].get("visit_number"),
                    "visit_type": case_data["metadata"].get("visit_type"),
                },
                embedding=embedding,
                metadata={
                    "session_id": f"demo-case-{i:04d}",
                    "patient_id": case_data["metadata"]["patient_id"],
                    "timestamp": case_data["metadata"]["timestamp"],
                    "modality": "text",
                    "visit_number": case_data["metadata"].get("visit_number"),
                    "visit_type": case_data["metadata"].get("visit_type"),
                    **metadata.model_dump()
                }
            )
            
            if stored_id:
                stored_count += 1
        
        except Exception as e:
            logger.error(f"Error storing case {i}: {e}")
    
    # Summary
    print()
    print("=" * 80)
    print("  Summary")
    print("=" * 80)
    print(f"✅ Patients generated: 50")
    print(f"✅ Total case entries: {len(all_cases)}")
    print(f"✅ Cases stored: {stored_count}")
    print()
    print("Demo data is now available for:")
    print("   - Patient timeline visualization")
    print("   - Similar case retrieval")
    print("   - SOAP note generation")
    print("   - Analytics and trend analysis")
    print("   - Knowledge intelligence")
    print()
    print("Patient IDs range from: patient_001 to patient_050")
    print("Each patient has 2-6 timeline entries")
    print("=" * 80)


if __name__ == "__main__":
    populate_extended_demo_data()

