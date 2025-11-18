#!/usr/bin/env python3
"""
Ingest Patient Cases from JSON Data

This script ingests patient cases from JSON format into Qdrant,
generates SOAP reports, and makes them available in timeline and analytics.
"""

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
INGEST_ENDPOINT = f"{API_BASE_URL}/api/v1/clinical_memory/ingest"

# Patient cases data
PATIENT_CASES = [
    {
        "patient_id": "P-DEN-001",
        "age_group": "18-30",
        "region": "Philippines",
        "diagnosis": "Dengue Fever (Non-severe)",
        "comorbidities": [],
        "outcome": "Recovered with outpatient monitoring; platelets normalized by Day 6.",
        "symptoms": ["fever", "joint pain", "retro-orbital pain", "rash"],
        "metadata": {
            "disease_category": "Infectious",
            "country": "Philippines",
            "risk_level": "moderate"
        },
        "file_references": []
    },
    {
        "patient_id": "P-DM-012",
        "age_group": "40-60",
        "region": "India",
        "diagnosis": "Newly Diagnosed Type 2 Diabetes",
        "comorbidities": ["Hypertension", "Obesity"],
        "outcome": "Stable on Metformin; fasting sugars improved to 120 mg/dL after 4 weeks.",
        "symptoms": ["fatigue", "polyuria", "polydipsia", "blurry vision"],
        "metadata": {
            "disease_category": "Chronic",
            "country": "India",
            "risk_level": "high"
        },
        "file_references": []
    },
    {
        "patient_id": "P-PNM-022",
        "age_group": "30-45",
        "region": "UAE",
        "diagnosis": "Community Acquired Pneumonia",
        "comorbidities": ["Smoking"],
        "outcome": "Improved after 5 days of azithromycin; CXR follow-up clear.",
        "symptoms": ["cough", "breathlessness", "fever"],
        "metadata": {
            "disease_category": "Respiratory",
            "country": "UAE",
            "risk_level": "high"
        },
        "file_references": []
    },
    {
        "patient_id": "P-GE-004",
        "age_group": "18-30",
        "region": "Peru",
        "diagnosis": "Viral Gastroenteritis",
        "comorbidities": [],
        "outcome": "Recovered fully after ORS and zinc.",
        "symptoms": ["vomiting", "diarrhea", "abdominal cramps"],
        "metadata": {
            "disease_category": "Gastrointestinal",
            "country": "Peru",
            "risk_level": "low"
        },
        "file_references": []
    },
    {
        "patient_id": "P-AST-009",
        "age_group": "5-12",
        "region": "Indonesia",
        "diagnosis": "Acute Asthma Exacerbation",
        "comorbidities": ["Allergic Rhinitis"],
        "outcome": "Stable after nebulization and steroids.",
        "symptoms": ["wheezing", "night cough", "difficulty breathing"],
        "metadata": {
            "disease_category": "Respiratory",
            "country": "Indonesia",
            "risk_level": "high"
        },
        "file_references": []
    },
    {
        "patient_id": "P-TB-031",
        "age_group": "25-40",
        "region": "Uganda",
        "diagnosis": "Suspected Pulmonary Tuberculosis",
        "comorbidities": ["Mild malnutrition"],
        "outcome": "Confirmed TB positive on GeneXpert; started HRZE regimen.",
        "symptoms": ["chronic cough", "weight loss", "night sweats"],
        "metadata": {
            "disease_category": "Infectious",
            "country": "Uganda",
            "risk_level": "high"
        },
        "file_references": []
    },
    {
        "patient_id": "P-HTN-055",
        "age_group": "60+",
        "region": "India",
        "diagnosis": "Hypertensive Urgency",
        "comorbidities": ["Type 2 Diabetes", "Hyperlipidemia"],
        "outcome": "Stabilized after BP control; discharged same day.",
        "symptoms": ["headache", "chest pressure"],
        "metadata": {
            "disease_category": "Cardiovascular",
            "country": "India",
            "risk_level": "high"
        },
        "file_references": []
    },
    {
        "patient_id": "P-PEDPNM-007",
        "age_group": "0-5",
        "region": "Vietnam",
        "diagnosis": "Pediatric Pneumonia",
        "comorbidities": ["Low birth weight"],
        "outcome": "Improved after IV ampicillin; discharged Day 4.",
        "symptoms": ["fever", "cough", "fast breathing"],
        "metadata": {
            "disease_category": "Respiratory",
            "country": "Vietnam",
            "risk_level": "high"
        },
        "file_references": []
    },
    {
        "patient_id": "P-COV-114",
        "age_group": "20-40",
        "region": "UAE",
        "diagnosis": "Mild COVID-19",
        "comorbidities": [],
        "outcome": "Recovered after home isolation and symptomatic treatment.",
        "symptoms": ["fever", "sore throat", "body aches"],
        "metadata": {
            "disease_category": "Infectious",
            "country": "UAE",
            "risk_level": "moderate"
        },
        "file_references": []
    },
    {
        "patient_id": "P-IDA-016",
        "age_group": "13-18",
        "region": "India",
        "diagnosis": "Iron Deficiency Anemia",
        "comorbidities": ["Dysmenorrhea"],
        "outcome": "Hemoglobin improved after 8 weeks of iron therapy.",
        "symptoms": ["fatigue", "hair fall", "dizziness"],
        "metadata": {
            "disease_category": "Hematology",
            "country": "India",
            "risk_level": "moderate"
        },
        "file_references": []
    },
    {
        "patient_id": "P-GERD-028",
        "age_group": "25-40",
        "region": "UAE",
        "diagnosis": "Gastroesophageal Reflux Disease (GERD)",
        "comorbidities": ["Overweight"],
        "outcome": "Symptoms resolved after PPI and lifestyle changes.",
        "symptoms": ["heartburn", "acid reflux"],
        "metadata": {
            "disease_category": "Gastrointestinal",
            "country": "UAE",
            "risk_level": "low"
        },
        "file_references": []
    },
    {
        "patient_id": "P-DEHY-010",
        "age_group": "0-5",
        "region": "Kenya",
        "diagnosis": "Severe Dehydration due to Diarrhea",
        "comorbidities": [],
        "outcome": "Responded well to IV rehydration; admitted 24 hours.",
        "symptoms": ["diarrhea", "lethargy", "no urine output"],
        "metadata": {
            "disease_category": "Pediatrics",
            "country": "Kenya",
            "risk_level": "high"
        },
        "file_references": []
    }
]


def create_transcript_from_case(case_data: dict) -> str:
    """Create a realistic clinical transcript from case data"""
    patient_id = case_data["patient_id"]
    age_group = case_data["age_group"]
    symptoms = case_data["symptoms"]
    diagnosis = case_data["diagnosis"]
    comorbidities = case_data.get("comorbidities", [])
    outcome = case_data.get("outcome", "")
    region = case_data.get("region", "")
    
    # Build transcript
    transcript_parts = []
    
    # Patient presentation
    transcript_parts.append(f"Patient ID: {patient_id}")
    transcript_parts.append(f"Age Group: {age_group}")
    if region:
        transcript_parts.append(f"Region: {region}")
    
    # Chief complaint
    if symptoms:
        symptoms_text = ", ".join(symptoms)
        transcript_parts.append(f"\nChief Complaint: Patient presents with {symptoms_text}.")
    
    # History of present illness
    if symptoms:
        transcript_parts.append(f"\nHistory of Present Illness:")
        transcript_parts.append(f"Patient reports experiencing {', '.join(symptoms)}.")
        if len(symptoms) > 1:
            transcript_parts.append("Symptoms have been progressively affecting daily activities.")
    
    # Past medical history
    if comorbidities:
        transcript_parts.append(f"\nPast Medical History:")
        transcript_parts.append(f"Known comorbidities include: {', '.join(comorbidities)}.")
    
    # Clinical assessment
    transcript_parts.append(f"\nClinical Assessment:")
    transcript_parts.append(f"Based on clinical presentation and examination, diagnosis: {diagnosis}.")
    
    # Plan and outcome
    if outcome:
        transcript_parts.append(f"\nTreatment Plan and Outcome:")
        transcript_parts.append(f"{outcome}")
    
    # Additional metadata
    metadata = case_data.get("metadata", {})
    if metadata:
        disease_category = metadata.get("disease_category", "")
        risk_level = metadata.get("risk_level", "")
        if disease_category or risk_level:
            transcript_parts.append(f"\nClinical Notes:")
            if disease_category:
                transcript_parts.append(f"Disease Category: {disease_category}")
            if risk_level:
                transcript_parts.append(f"Risk Level: {risk_level}")
    
    return "\n".join(transcript_parts)


def ingest_case(case_data: dict, delay_seconds: float = 0.5) -> dict:
    """Ingest a single case via API"""
    try:
        # Create transcript
        transcript = create_transcript_from_case(case_data)
        
        # Map age_group to standard format
        age_group = case_data["age_group"]
        if "0-5" in age_group or "5-12" in age_group:
            age_group_standard = "pediatric"
        elif "60+" in age_group:
            age_group_standard = "elderly"
        else:
            age_group_standard = "adult"
        
        # Prepare form data
        form_data = {
            "patient_id": case_data["patient_id"],
            "age_group": age_group_standard,
            "region": case_data.get("region", ""),
            "comorbidities": json.dumps(case_data.get("comorbidities", [])),
            "diagnosis": case_data.get("diagnosis", ""),
            "outcome": case_data.get("outcome", ""),
            "transcript_text": transcript
        }
        
        # Make API request
        logger.info(f"Ingesting case for patient {case_data['patient_id']}...")
        response = requests.post(
            INGEST_ENDPOINT,
            data=form_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Successfully ingested case {result.get('case_id')} for patient {case_data['patient_id']}")
            logger.info(f"   SOAP Generated: {result.get('soap_generated', False)}")
            return {"success": True, "data": result}
        else:
            error_msg = f"API returned status {response.status_code}: {response.text}"
            logger.error(f"❌ Failed to ingest case for patient {case_data['patient_id']}: {error_msg}")
            return {"success": False, "error": error_msg}
    
    except Exception as e:
        logger.error(f"❌ Error ingesting case for patient {case_data['patient_id']}: {str(e)}")
        return {"success": False, "error": str(e)}


def main():
    """Main ingestion function"""
    logger.info("=" * 80)
    logger.info("Patient Cases Ingestion Script")
    logger.info("=" * 80)
    logger.info(f"API Endpoint: {INGEST_ENDPOINT}")
    logger.info(f"Total cases to ingest: {len(PATIENT_CASES)}")
    logger.info("")
    
    # Check if API is accessible
    try:
        health_url = f"{API_BASE_URL}/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code != 200:
            logger.warning(f"⚠️  API health check returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Cannot connect to API at {API_BASE_URL}")
        logger.error(f"   Error: {str(e)}")
        logger.error("   Please ensure the backend server is running: python run_server.py")
        return
    
    logger.info("✅ API is accessible")
    logger.info("")
    
    # Ingest each case
    results = []
    successful = 0
    failed = 0
    
    for idx, case_data in enumerate(PATIENT_CASES, 1):
        logger.info(f"[{idx}/{len(PATIENT_CASES)}] Processing patient {case_data['patient_id']}...")
        
        result = ingest_case(case_data)
        results.append({
            "patient_id": case_data["patient_id"],
            "result": result
        })
        
        if result["success"]:
            successful += 1
        else:
            failed += 1
        
        # Add delay between requests to avoid overwhelming the API
        if idx < len(PATIENT_CASES):
            time.sleep(0.5)
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("Ingestion Summary")
    logger.info("=" * 80)
    logger.info(f"✅ Successful: {successful}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📊 Total: {len(PATIENT_CASES)}")
    logger.info("")
    
    # Show failed cases
    if failed > 0:
        logger.info("Failed Cases:")
        for result in results:
            if not result["result"]["success"]:
                logger.info(f"  - {result['patient_id']}: {result['result'].get('error', 'Unknown error')}")
    
    logger.info("")
    logger.info("✅ Ingestion complete!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Check the Timeline page to view patient case histories")
    logger.info("2. Check the SOAP Notes page to view generated SOAP reports")
    logger.info("3. Check the Analytics page to view trend analytics")
    logger.info("")


if __name__ == "__main__":
    main()

