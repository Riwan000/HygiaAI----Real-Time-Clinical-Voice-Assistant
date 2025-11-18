#!/usr/bin/env python3
"""
Populate COVID-19 Patient Database

This script populates Qdrant with:
- 50 patients with confirmed COVID-19
- 30 patients with COVID-like symptoms but different diagnoses (flu, pneumonia, etc.)

Run this script to populate COVID-related patient data.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random
import uuid
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
from src.embeddings import BioBERTEmbeddingGenerator
from src.storage.schema import StorageMetadata, ModalityType
from src.api.clinical_memory_api import get_qdrant_storage

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Indian states/regions
REGIONS = [
    "Kerala", "Tamil Nadu", "Karnataka", "Maharashtra", "Gujarat",
    "Rajasthan", "Punjab", "West Bengal", "Odisha", "Andhra Pradesh",
    "Telangana", "Bihar", "Uttar Pradesh", "Madhya Pradesh", "Assam"
]

# COVID-19 symptoms
COVID_SYMPTOMS = [
    "fever", "dry cough", "fatigue", "loss of taste", "loss of smell",
    "sore throat", "headache", "body aches", "shortness of breath",
    "chest pain", "diarrhea", "nausea", "vomiting", "congestion",
    "runny nose", "chills", "muscle pain"
]

# COVID-like symptoms (but not COVID)
COVID_LIKE_SYMPTOMS = {
    "Influenza": ["fever", "cough", "sore throat", "body aches", "fatigue", "headache", "chills"],
    "Community-Acquired Pneumonia": ["fever", "cough", "shortness of breath", "chest pain", "fatigue"],
    "Acute Bronchitis": ["cough", "sore throat", "fatigue", "mild fever", "congestion"],
    "Upper Respiratory Tract Infection": ["sore throat", "runny nose", "congestion", "mild fever", "cough"],
    "Allergic Rhinitis": ["runny nose", "congestion", "sneezing", "itchy eyes", "sore throat"],
    "Seasonal Allergies": ["runny nose", "congestion", "sneezing", "itchy eyes", "fatigue"]
}

# COVID-19 severity levels
COVID_SEVERITY = ["mild", "moderate", "severe", "critical"]

# Common comorbidities for COVID patients
COVID_COMORBIDITIES = [
    "Hypertension", "Type 2 Diabetes Mellitus", "Obesity", "Asthma",
    "COPD", "Chronic Kidney Disease", "Heart Disease", "Immunocompromised"
]


def generate_covid_transcript(patient_id: str, age: int, gender: str, region: str, 
                              severity: str, comorbidities: list, visit_num: int, 
                              days_since_onset: int, is_positive: bool = True):
    """Generate realistic COVID-19 transcript"""
    
    # Select symptoms based on severity
    if severity == "mild":
        num_symptoms = random.randint(3, 5)
        symptoms = random.sample(COVID_SYMPTOMS[:8], num_symptoms)  # Common symptoms
    elif severity == "moderate":
        num_symptoms = random.randint(5, 8)
        symptoms = random.sample(COVID_SYMPTOMS[:12], num_symptoms)
    else:  # severe or critical
        num_symptoms = random.randint(7, 10)
        symptoms = random.sample(COVID_SYMPTOMS, num_symptoms)
    
    # Build transcript
    transcript_parts = []
    
    # Patient info
    transcript_parts.append(
        f"Patient is a {age}-year-old {gender} from {region}."
    )
    
    if comorbidities:
        transcript_parts.append(
            f"Medical history: {', '.join(comorbidities)}."
        )
    
    # Chief complaint
    if visit_num == 1:
        transcript_parts.append(
            f"Chief complaint: {', '.join(symptoms[:3])} for {days_since_onset} days."
        )
    else:
        transcript_parts.append(
            f"Follow-up visit {visit_num} for COVID-19."
        )
    
    # History of present illness
    if visit_num == 1:
        hpi = f"Patient reports onset of symptoms {days_since_onset} days ago. "
        hpi += f"Started with {symptoms[0]} and {symptoms[1] if len(symptoms) > 1 else 'fatigue'}. "
        
        if "loss of taste" in symptoms or "loss of smell" in symptoms:
            hpi += "Noted loss of taste and smell. "
        
        if "shortness of breath" in symptoms:
            hpi += "Experiencing difficulty breathing, worse with activity. "
        
        if "fever" in symptoms:
            hpi += f"Fever up to {random.randint(100, 103)}°F. "
        
        hpi += "No recent travel history. Possible exposure to COVID-19 positive individual."
        transcript_parts.append(f"History: {hpi}")
    else:
        transcript_parts.append(
            f"Patient reports {random.choice(['improvement', 'persistent symptoms', 'worsening'])} since last visit."
        )
    
    # Physical examination
    bp = f"{random.randint(110, 150)}/{random.randint(70, 95)} mmHg"
    hr = f"{random.randint(75, 110)} bpm"
    rr = f"{random.randint(16, 24)} bpm"
    temp = f"{random.randint(98, 102)}°F"
    spo2 = random.randint(88, 98) if severity in ["severe", "critical"] else random.randint(94, 99)
    
    exam = f"Vital signs: BP {bp}, HR {hr}, RR {rr}, Temp {temp}, SpO2 {spo2}% on room air. "
    
    if severity == "mild":
        exam += "General appearance: Well-appearing, in no acute distress. "
        exam += "Lungs: Clear to auscultation bilaterally. "
    elif severity == "moderate":
        exam += "General appearance: Mildly ill-appearing. "
        exam += "Lungs: Decreased breath sounds, mild crackles bilaterally. "
    else:  # severe/critical
        exam += "General appearance: Ill-appearing, in respiratory distress. "
        exam += "Lungs: Decreased breath sounds, bilateral crackles, tachypnea. "
        exam += "Using accessory muscles for breathing. "
    
    exam += "Heart: Regular rhythm, no murmurs. "
    exam += "No lymphadenopathy. "
    
    if "loss of taste" in symptoms or "loss of smell" in symptoms:
        exam += "Anosmia and ageusia noted. "
    
    transcript_parts.append(f"Physical examination: {exam}")
    
    # Assessment
    if is_positive:
        assessment = f"Assessment: COVID-19, {severity} severity"
        if comorbidities:
            assessment += f". Comorbidities: {', '.join(comorbidities)}"
    else:
        # For COVID-like symptoms but not COVID
        diagnosis = random.choice(list(COVID_LIKE_SYMPTOMS.keys()))
        assessment = f"Assessment: {diagnosis}. COVID-19 test negative."
    
    transcript_parts.append(assessment)
    
    # Plan
    if is_positive:
        if severity == "mild":
            plan = "Home isolation for 10 days. Symptomatic treatment: Paracetamol 500mg Q6H for fever, "
            plan += "steam inhalation, warm saline gargles. Monitor SpO2 daily. "
            plan += "Return if symptoms worsen or SpO2 drops below 94%. "
            plan += "Contact tracing initiated."
        elif severity == "moderate":
            plan = "Hospital admission for monitoring. Oxygen support if SpO2 <94%. "
            plan += "Dexamethasone 6mg daily x10 days. Remdesivir if indicated. "
            plan += "Anticoagulation prophylaxis. Monitor for complications. "
            plan += "Chest X-ray and lab work ordered."
        else:  # severe/critical
            plan = "ICU admission. High-flow oxygen or mechanical ventilation if needed. "
            plan += "Dexamethasone 6mg daily. Remdesivir. Anticoagulation. "
            plan += "Monitor for ARDS, sepsis, multi-organ failure. "
            plan += "Critical care management."
    else:
        diagnosis = random.choice(list(COVID_LIKE_SYMPTOMS.keys()))
        if diagnosis == "Influenza":
            plan = "Oseltamivir 75mg BID x5 days. Symptomatic treatment. Rest and hydration. "
            plan += "Isolate until afebrile for 24 hours. "
        elif diagnosis == "Community-Acquired Pneumonia":
            plan = "Amoxicillin-Clavulanate 875/125mg BID + Azithromycin 500mg daily x7 days. "
            plan += "Chest X-ray ordered. Follow-up in 48-72 hours."
        else:
            plan = "Symptomatic treatment. Rest and hydration. Monitor for improvement."
    
    transcript_parts.append(f"Plan: {plan}")
    
    return " ".join(transcript_parts)


def generate_covid_like_transcript(patient_id: str, age: int, gender: str, region: str,
                                   diagnosis: str, visit_num: int, days_since_onset: int):
    """Generate transcript for COVID-like symptoms but not COVID"""
    
    symptoms = COVID_LIKE_SYMPTOMS[diagnosis]
    selected_symptoms = random.sample(symptoms, min(len(symptoms), random.randint(3, len(symptoms))))
    
    transcript_parts = []
    
    # Patient info
    transcript_parts.append(
        f"Patient is a {age}-year-old {gender} from {region}."
    )
    
    # Chief complaint
    if visit_num == 1:
        transcript_parts.append(
            f"Chief complaint: {', '.join(selected_symptoms[:3])} for {days_since_onset} days."
        )
    else:
        transcript_parts.append(
            f"Follow-up visit {visit_num} for {diagnosis}."
        )
    
    # History
    if visit_num == 1:
        hpi = f"Patient reports onset of symptoms {days_since_onset} days ago. "
        hpi += f"Started with {selected_symptoms[0]}. "
        
        if diagnosis == "Influenza":
            hpi += "Sudden onset of fever and body aches. "
            hpi += "COVID-19 RT-PCR test performed - negative. "
        elif diagnosis == "Community-Acquired Pneumonia":
            hpi += "Productive cough with yellow sputum. "
            hpi += "COVID-19 test negative. "
        else:
            hpi += "Symptoms consistent with seasonal illness. "
            hpi += "COVID-19 test negative. "
        
        transcript_parts.append(f"History: {hpi}")
    else:
        transcript_parts.append(
            f"Patient reports improvement since last visit."
        )
    
    # Physical examination
    bp = f"{random.randint(110, 140)}/{random.randint(70, 90)} mmHg"
    hr = f"{random.randint(75, 100)} bpm"
    rr = f"{random.randint(16, 22)} bpm"
    temp = f"{random.randint(98, 101)}°F"
    spo2 = random.randint(95, 99)
    
    exam = f"Vital signs: BP {bp}, HR {hr}, RR {rr}, Temp {temp}, SpO2 {spo2}% on room air. "
    exam += "General appearance: Well to mildly ill-appearing. "
    
    if diagnosis == "Community-Acquired Pneumonia":
        exam += "Lungs: Decreased breath sounds, crackles in lower lobes. "
    elif diagnosis in ["Acute Bronchitis", "Upper Respiratory Tract Infection"]:
        exam += "Lungs: Clear to auscultation, occasional rhonchi. "
    else:
        exam += "Lungs: Clear bilaterally. "
    
    exam += "Heart: Regular rhythm. "
    exam += "No acute distress."
    
    transcript_parts.append(f"Physical examination: {exam}")
    
    # Assessment
    assessment = f"Assessment: {diagnosis}. COVID-19 RT-PCR negative."
    transcript_parts.append(assessment)
    
    # Plan (already handled in generate_covid_transcript for non-COVID cases)
    if diagnosis == "Influenza":
        plan = "Oseltamivir 75mg BID x5 days. Symptomatic treatment. Rest and hydration."
    elif diagnosis == "Community-Acquired Pneumonia":
        plan = "Amoxicillin-Clavulanate 875/125mg BID + Azithromycin 500mg daily x7 days. Chest X-ray ordered."
    else:
        plan = "Symptomatic treatment. Rest and hydration. Monitor for improvement."
    
    transcript_parts.append(f"Plan: {plan}")
    
    return " ".join(transcript_parts)


def populate_covid_patients():
    """Populate 50 COVID-19 patients"""
    logger.info("="*80)
    logger.info("Populating COVID-19 Patient Database")
    logger.info("="*80)
    
    # Get storage
    patient_storage = get_qdrant_storage(collection_name="patient_memory_collection")
    embedder = BioBERTEmbeddingGenerator()
    
    # Generate 50 COVID-19 patients
    logger.info("\n📋 Generating 50 COVID-19 patients...")
    covid_patients = []
    
    for i in range(1, 51):
        patient_id = f"COVID_PATIENT_{i:03d}"
        age = random.randint(18, 80)
        gender = random.choice(["male", "female"])
        region = random.choice(REGIONS)
        severity = random.choice(COVID_SEVERITY)
        
        # Comorbidities (higher risk for severe cases)
        comorbidities = []
        if severity in ["severe", "critical"]:
            num_comorbidities = random.randint(1, 3)
            comorbidities = random.sample(COVID_COMORBIDITIES, num_comorbidities)
        elif random.random() < 0.4:  # 40% of mild/moderate have comorbidities
            comorbidities = random.sample(COVID_COMORBIDITIES, random.randint(1, 2))
        
        # Generate 1-3 visits per patient
        num_visits = random.randint(1, 3)
        base_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))
        
        for visit_num in range(1, num_visits + 1):
            days_since_onset = random.randint(1, 14) if visit_num == 1 else random.randint(15, 30)
            visit_date = base_date + timedelta(days=(visit_num - 1) * random.randint(3, 10))
            
            transcript = generate_covid_transcript(
                patient_id=patient_id,
                age=age,
                gender=gender,
                region=region,
                severity=severity,
                comorbidities=comorbidities,
                visit_num=visit_num,
                days_since_onset=days_since_onset,
                is_positive=True
            )
            
            # Generate embedding
            embedding = embedder.generate_embedding(transcript[:2000])
            
            # Create transcript data
            transcript_data = {
                "transcript": transcript[:5000],
                "session_id": f"case_{visit_date.strftime('%Y%m%d%H%M%S')}_{patient_id}_visit{visit_num}",
                "metadata": {
                    "patient_id": patient_id,
                    "age_group": "elderly" if age >= 60 else "adult",
                    "region": region,
                    "comorbidities": comorbidities,
                    "diagnosis": f"COVID-19, {severity} severity",
                    "outcome": "recovered" if visit_num == num_visits and random.random() > 0.2 else "under_treatment",
                    "visit_number": visit_num,
                    "covid_positive": True,
                    "severity": severity
                },
                "timestamp": visit_date.isoformat(),
                "confidence": 1.0,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Create metadata
            metadata = StorageMetadata(
                session_id=transcript_data["session_id"],
                patient_id=patient_id,
                timestamp=visit_date,
                modality=ModalityType.TEXT,
                confidence=1.0
            )
            
            # Store
            patient_storage.store_transcript(transcript_data, embedding, metadata)
            covid_patients.append(patient_id)
            
            logger.info(f"  ✓ Stored visit {visit_num} for {patient_id} ({severity} severity)")
    
    # Count total visits
    total_visits = sum(1 for _ in covid_patients)  # Each entry is a visit
    unique_patients = len(set(covid_patients))
    logger.info(f"\n✅ Stored {unique_patients} unique COVID-19 patients with {total_visits} total visits")
    
    # Generate 30 patients with COVID-like symptoms but not COVID
    logger.info("\n📋 Generating 30 patients with COVID-like symptoms (not COVID)...")
    covid_like_patients = []
    
    diagnoses_list = list(COVID_LIKE_SYMPTOMS.keys())
    
    for i in range(1, 31):
        patient_id = f"COVID_LIKE_PATIENT_{i:03d}"
        age = random.randint(18, 75)
        gender = random.choice(["male", "female"])
        region = random.choice(REGIONS)
        diagnosis = random.choice(diagnoses_list)
        
        # Generate 1-2 visits
        num_visits = random.randint(1, 2)
        base_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))
        
        for visit_num in range(1, num_visits + 1):
            days_since_onset = random.randint(2, 10) if visit_num == 1 else random.randint(11, 20)
            visit_date = base_date + timedelta(days=(visit_num - 1) * random.randint(5, 14))
            
            transcript = generate_covid_like_transcript(
                patient_id=patient_id,
                age=age,
                gender=gender,
                region=region,
                diagnosis=diagnosis,
                visit_num=visit_num,
                days_since_onset=days_since_onset
            )
            
            # Generate embedding
            embedding = embedder.generate_embedding(transcript[:2000])
            
            # Create transcript data
            transcript_data = {
                "transcript": transcript[:5000],
                "session_id": f"case_{visit_date.strftime('%Y%m%d%H%M%S')}_{patient_id}_visit{visit_num}",
                "metadata": {
                    "patient_id": patient_id,
                    "age_group": "elderly" if age >= 60 else "adult",
                    "region": region,
                    "comorbidities": [],
                    "diagnosis": diagnosis,
                    "outcome": "recovered" if visit_num == num_visits else "improved",
                    "visit_number": visit_num,
                    "covid_positive": False,
                    "covid_test_result": "negative"
                },
                "timestamp": visit_date.isoformat(),
                "confidence": 1.0,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Create metadata
            metadata = StorageMetadata(
                session_id=transcript_data["session_id"],
                patient_id=patient_id,
                timestamp=visit_date,
                modality=ModalityType.TEXT,
                confidence=1.0
            )
            
            # Store
            patient_storage.store_transcript(transcript_data, embedding, metadata)
            covid_like_patients.append(patient_id)
            
            logger.info(f"  ✓ Stored visit {visit_num} for {patient_id} ({diagnosis})")
    
    # Count total visits for COVID-like patients
    total_covid_like_visits = sum(1 for _ in covid_like_patients)
    unique_covid_like_patients = len(set(covid_like_patients))
    logger.info(f"\n✅ Stored {unique_covid_like_patients} unique COVID-like symptom patients with {total_covid_like_visits} total visits")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("Summary")
    logger.info("="*80)
    logger.info(f"COVID-19 Patients: {unique_patients}")
    logger.info(f"COVID-19 Total Visits: {total_visits}")
    logger.info(f"COVID-like Symptom Patients: {unique_covid_like_patients}")
    logger.info(f"COVID-like Total Visits: {total_covid_like_visits}")
    logger.info(f"Total Unique Patients: {unique_patients + unique_covid_like_patients}")
    logger.info(f"Total Visits: {total_visits + total_covid_like_visits}")
    
    # Check collection status
    try:
        collection_info = patient_storage.get_collection_info()
        logger.info(f"\n📊 Patient Memory Collection Status:")
        logger.info(f"  Total points: {collection_info.get('points_count', 0)}")
    except Exception as e:
        logger.warning(f"Could not get collection info: {e}")
    
    logger.info("\n✅ COVID patient database population complete!")


if __name__ == "__main__":
    try:
        populate_covid_patients()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        sys.exit(1)

