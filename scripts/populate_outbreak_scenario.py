#!/usr/bin/env python3
"""
Populate Outbreak Scenario Data for Demo

This script creates a realistic outbreak scenario by populating multiple cases
with similar symptoms and diagnoses in the same region within a recent time window.

Perfect for demonstrating outbreak detection features.

Usage:
    python scripts/populate_outbreak_scenario.py
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
from src.api.clinical_memory_api import get_qdrant_storage

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Outbreak scenarios to create
OUTBREAK_SCENARIOS = [
    {
        "name": "Dengue Fever Outbreak - Kerala",
        "region": "Kerala",
        "diagnosis": "Dengue Fever",
        "symptoms": ["fever", "headache", "body aches", "rash", "nausea"],
        "num_cases": 8,
        "days_ago": 3,  # Cases within last 3 days
    },
    {
        "name": "Acute Gastroenteritis Outbreak - Tamil Nadu",
        "region": "Tamil Nadu",
        "diagnosis": "Acute Gastroenteritis",
        "symptoms": ["diarrhea", "vomiting", "abdominal pain", "fever", "dehydration"],
        "num_cases": 6,
        "days_ago": 5,  # Cases within last 5 days
    },
    {
        "name": "Respiratory Infection Cluster - Karnataka",
        "region": "Karnataka",
        "diagnosis": "Upper Respiratory Tract Infection",
        "symptoms": ["cough", "fever", "sore throat", "runny nose", "fatigue"],
        "num_cases": 5,
        "days_ago": 4,  # Cases within last 4 days
    },
]

# Age groups
AGE_GROUPS = {
    "pediatric": (5, 15),
    "adult": (18, 65),
    "elderly": (65, 80)
}

GENDERS = ["male", "female"]


def generate_outbreak_transcript(patient_id: str, age: int, gender: str, region: str,
                                diagnosis: str, symptoms: list, days_ago: int):
    """Generate a realistic consultation transcript for outbreak case"""
    
    # Base consultation
    transcript_parts = [
        f"Patient: {patient_id}",
        f"Age: {age} years",
        f"Gender: {gender}",
        f"Region: {region}",
        f"Visit Date: {datetime.now(timezone.utc) - timedelta(days=days_ago)}",
        "",
        "Doctor: What brings you in today?",
    ]
    
    # Patient complaint based on symptoms
    symptom_text = ", ".join(symptoms[:3])  # Use first 3 symptoms
    transcript_parts.append(
        f"Patient: I've been experiencing {symptom_text} for the past few days."
    )
    
    # Add symptom details
    if "fever" in symptoms:
        transcript_parts.append("Patient: I have a high fever, around 38-39 degrees Celsius.")
    
    if "cough" in symptoms:
        transcript_parts.append("Patient: I have a persistent cough, especially at night.")
    
    if "diarrhea" in symptoms:
        transcript_parts.append("Patient: I've had loose stools multiple times today.")
    
    if "headache" in symptoms:
        transcript_parts.append("Patient: I have a severe headache that won't go away.")
    
    if "body aches" in symptoms:
        transcript_parts.append("Patient: My whole body aches, especially my joints.")
    
    # Doctor response
    transcript_parts.extend([
        "",
        "Doctor: Let me examine you.",
        "Doctor: I can see signs of infection. Let me check your vital signs.",
    ])
    
    # Add vital signs
    if "fever" in symptoms:
        temp = round(random.uniform(38.0, 39.5), 1)
        transcript_parts.append(f"Doctor: Temperature is {temp}°C - elevated.")
    
    bp = f"{random.randint(110, 130)}/{random.randint(70, 85)}"
    transcript_parts.append(f"Doctor: Blood pressure is {bp} mmHg.")
    
    pulse = random.randint(75, 95)
    transcript_parts.append(f"Doctor: Pulse is {pulse} beats per minute.")
    
    # Assessment
    transcript_parts.extend([
        "",
        f"Doctor: Based on your symptoms and examination, this appears to be {diagnosis}.",
        "Doctor: This is consistent with what we've been seeing in the area recently.",
    ])
    
    # Treatment plan
    if "Dengue" in diagnosis:
        transcript_parts.extend([
            "Doctor: I'll prescribe paracetamol for fever and pain.",
            "Doctor: Rest and plenty of fluids are important.",
            "Doctor: Monitor for warning signs like severe abdominal pain or bleeding.",
        ])
    elif "Gastroenteritis" in diagnosis:
        transcript_parts.extend([
            "Doctor: I'll prescribe oral rehydration solution.",
            "Doctor: Avoid solid foods for 24 hours.",
            "Doctor: If symptoms worsen, come back immediately.",
        ])
    else:
        transcript_parts.extend([
            "Doctor: I'll prescribe symptomatic treatment.",
            "Doctor: Rest and stay hydrated.",
            "Doctor: Follow up if symptoms persist.",
        ])
    
    return " ".join(transcript_parts)


def populate_outbreak_scenarios():
    """Populate outbreak scenario data"""
    logger.info("="*80)
    logger.info("Populating Outbreak Scenario Data for Demo")
    logger.info("="*80)
    
    # Get storage
    storage = get_qdrant_storage(collection_name="patient_memory_collection")
    embedder = BioBERTEmbeddingGenerator()
    
    total_cases = 0
    
    for scenario in OUTBREAK_SCENARIOS:
        logger.info(f"\n📋 Creating: {scenario['name']}")
        logger.info(f"   Region: {scenario['region']}")
        logger.info(f"   Cases: {scenario['num_cases']}")
        logger.info(f"   Time Window: Last {scenario['days_ago']} days")
        
        cases_created = 0
        
        for i in range(scenario['num_cases']):
            try:
                # Generate patient details
                age_group = random.choice(list(AGE_GROUPS.keys()))
                age_min, age_max = AGE_GROUPS[age_group]
                age = random.randint(age_min, age_max)
                gender = random.choice(GENDERS)
                
                # Vary days ago slightly (within scenario window)
                days_ago = scenario['days_ago'] + random.randint(0, 2)
                
                # Generate case ID
                case_id = f"OUTBREAK_{scenario['region'].upper().replace(' ', '_')}_{i+1:03d}"
                
                # Generate transcript
                transcript = generate_outbreak_transcript(
                    patient_id=case_id,
                    age=age,
                    gender=gender,
                    region=scenario['region'],
                    diagnosis=scenario['diagnosis'],
                    symptoms=scenario['symptoms'],
                    days_ago=days_ago
                )
                
                # Generate embedding
                embedding = embedder.generate_embedding(transcript)
                
                # Create timestamp
                timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)
                
                # Determine age_group from age
                if age < 18:
                    age_group = "pediatric"
                elif age >= 65:
                    age_group = "elderly"
                else:
                    age_group = "adult"
                
                # Prepare case_metadata according to CaseMetadata model
                case_metadata = {
                    "timestamp": timestamp.isoformat(),
                    "age_group": age_group,
                    "region": scenario['region'],
                    "comorbidities": [],  # Can add comorbidities if needed
                    "diagnosis": scenario['diagnosis'],
                    "outcome": None  # Can set outcome if needed
                }
                
                # Create medical_entities structure for outbreak detection compatibility
                medical_entities = []
                # Add symptoms as entities
                for symptom in scenario['symptoms']:
                    medical_entities.append({
                        "text": symptom,
                        "entity_type": "symptom",
                        "confidence": 0.9,
                        "normalized_form": symptom.lower()
                    })
                # Add diagnosis as entity
                medical_entities.append({
                    "text": scenario['diagnosis'],
                    "entity_type": "diagnosis",
                    "confidence": 0.9,
                    "normalized_form": scenario['diagnosis'].lower()
                })
                
                # Prepare payload matching the structure used by case ingestion orchestrator
                # Also include fields needed for outbreak detection
                payload = {
                    "modality_type": "text",
                    "transcript": transcript,
                    "case_metadata": case_metadata,
                    "timestamp": timestamp.isoformat(),
                    # Additional fields for outbreak detection compatibility
                    "patient_id": case_id,
                    "region": scenario['region'],  # Direct access for filtering
                    "diagnosis": scenario['diagnosis'],  # Direct access for filtering
                    "symptoms": scenario['symptoms'],  # For outbreak detection
                    "medical_entities": medical_entities,  # Structured entities for outbreak detection
                    "age_group": age_group,
                    "source": "outbreak_demo"
                }
                
                # Store in Qdrant
                point_id = str(uuid.uuid4())
                from qdrant_client.models import PointStruct
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                storage.client.upsert(
                    collection_name=storage.collection_name,
                    points=[point]
                )
                
                cases_created += 1
                total_cases += 1
                
                logger.info(f"   ✓ Created case {i+1}/{scenario['num_cases']}: {case_id}")
                
            except Exception as e:
                logger.error(f"   ✗ Error creating case {i+1}: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"   ✅ Created {cases_created} cases for {scenario['name']}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("Summary")
    logger.info("="*80)
    logger.info(f"✅ Total scenarios created: {len(OUTBREAK_SCENARIOS)}")
    logger.info(f"✅ Total cases created: {total_cases}")
    logger.info("\n📊 Outbreak Detection Ready!")
    logger.info("\nTo view outbreaks:")
    logger.info("1. Open Analytics page in frontend")
    logger.info("2. Select a region (Kerala, Tamil Nadu, or Karnataka)")
    logger.info("3. Set time range to last 7 days")
    logger.info("4. Outbreak alerts should appear automatically")
    logger.info("\n" + "="*80)


if __name__ == "__main__":
    populate_outbreak_scenarios()

