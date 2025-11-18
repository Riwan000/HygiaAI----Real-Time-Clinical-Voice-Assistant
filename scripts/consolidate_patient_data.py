#!/usr/bin/env python3
"""
Consolidate Patient Data
Combines all patient/case data from different collections into patient_memory_collection
with standardized patient IDs (patient_1, patient_2, etc.)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from src.embeddings import BioBERTEmbeddingGenerator

def get_qdrant_client():
    """Get Qdrant client based on environment configuration"""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if qdrant_url:
        return QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
    else:
        return QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            api_key=qdrant_api_key
        )

def normalize_patient_data(payload, patient_id, embedder):
    """Normalize patient data to multimodal format"""
    # Extract transcript
    transcript = payload.get("transcript", "")
    if not transcript:
        # Try to get from case_data
        case_data = payload.get("case_data", {})
        if isinstance(case_data, dict):
            transcript = case_data.get("transcript", "")
    
    # Generate embedding if transcript exists
    embedding = None
    if transcript:
        try:
            embedding = embedder.generate_embedding(transcript)
        except Exception as e:
            print(f"  Warning: Could not generate embedding: {e}")
            return None
    
    # Extract timestamp
    timestamp = payload.get("timestamp")
    if not timestamp:
        timestamp = payload.get("case_metadata", {}).get("timestamp") if isinstance(payload.get("case_metadata"), dict) else None
    if not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat()
    elif isinstance(timestamp, str):
        pass  # Already ISO string
    else:
        timestamp = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
    
    # Extract case_metadata
    case_metadata = payload.get("case_metadata", {})
    if not case_metadata or not isinstance(case_metadata, dict):
        # Build from payload fields
        case_metadata = {
            "timestamp": timestamp,
            "age_group": payload.get("age_group"),
            "region": payload.get("region"),
            "comorbidities": payload.get("comorbidities", []),
            "diagnosis": payload.get("diagnosis"),
            "outcome": payload.get("outcome")
        }
    
    # Extract medical entities
    medical_entities = payload.get("medical_entities", [])
    if not medical_entities:
        # Try to build from symptoms/diagnosis if available
        medical_entities = []
        symptoms = payload.get("symptoms", [])
        if isinstance(symptoms, list):
            for symptom in symptoms[:10]:
                medical_entities.append({
                    "text": str(symptom),
                    "entity_type": "symptom",
                    "confidence": 0.9,
                    "normalized_form": str(symptom).lower()
                })
        
        diagnosis = payload.get("diagnosis") or case_metadata.get("diagnosis")
        if diagnosis:
            medical_entities.append({
                "text": str(diagnosis),
                "entity_type": "diagnosis",
                "confidence": 0.9,
                "normalized_form": str(diagnosis).lower()
            })
    
    # Build normalized payload
    normalized_payload = {
        "modality_type": payload.get("modality_type", "text"),
        "transcript": transcript[:5000] if transcript else "",  # Limit transcript length
        "case_metadata": case_metadata,
        "timestamp": timestamp,
        "patient_id": patient_id,
        "region": payload.get("region") or case_metadata.get("region"),
        "diagnosis": payload.get("diagnosis") or case_metadata.get("diagnosis"),
        "symptoms": payload.get("symptoms", []),
        "medical_entities": medical_entities,
        "age_group": payload.get("age_group") or case_metadata.get("age_group"),
        "source": payload.get("source", "consolidated"),
    }
    
    # Add additional fields if present
    for key in ["covid_positive", "severity", "visit_number", "outcome"]:
        if key in payload:
            normalized_payload[key] = payload[key]
    
    return {
        "payload": normalized_payload,
        "embedding": embedding
    }

def main():
    """Main consolidation function"""
    print("Patient Data Consolidation")
    print("=" * 80)
    
    try:
        client = get_qdrant_client()
        embedder = BioBERTEmbeddingGenerator()
        
        target_collection = "patient_memory_collection"
        
        # Collections to read from
        source_collections = [
            "hygiaai_cases",
            "patient_memory_collection"  # Also consolidate existing data
        ]
        
        all_patient_points = []
        patient_counter = 1
        
        print(f"\nReading data from source collections...")
        
        for collection_name in source_collections:
            try:
                collection_info = client.get_collection(collection_name)
                if collection_info.points_count == 0:
                    print(f"  {collection_name}: No points (skipping)")
                    continue
                
                print(f"  {collection_name}: {collection_info.points_count} points")
                
                # Scroll through all points
                offset = None
                batch_count = 0
                
                while True:
                    scroll_result = client.scroll(
                        collection_name=collection_name,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                        with_vectors=True
                    )
                    
                    points, next_offset = scroll_result
                    
                    if not points:
                        break
                    
                    for point in points:
                        payload = point.payload or {}
                        
                        # Skip if already has standardized patient_id format
                        existing_patient_id = payload.get("patient_id", "")
                        if existing_patient_id and existing_patient_id.startswith("patient_"):
                            # Already standardized, skip
                            continue
                        
                        # Assign new patient ID
                        new_patient_id = f"patient_{patient_counter}"
                        patient_counter += 1
                        
                        # Normalize data
                        normalized = normalize_patient_data(payload, new_patient_id, embedder)
                        
                        if normalized and normalized["embedding"]:
                            # Use existing vector if available, otherwise use generated embedding
                            vector = point.vector if point.vector else normalized["embedding"]
                            
                            all_patient_points.append({
                                "id": str(uuid.uuid4()),
                                "vector": vector,
                                "payload": normalized["payload"]
                            })
                            batch_count += 1
                    
                    if next_offset is None:
                        break
                    offset = next_offset
                
                print(f"    Processed {batch_count} points from {collection_name}")
                
            except Exception as e:
                print(f"  Error reading {collection_name}: {e}")
                continue
        
        print(f"\nTotal points to add: {len(all_patient_points)}")
        
        if not all_patient_points:
            print("No new patient data to consolidate.")
            return
        
        # Batch insert into target collection
        print(f"\nInserting into {target_collection}...")
        batch_size = 50
        
        for i in range(0, len(all_patient_points), batch_size):
            batch = all_patient_points[i:i + batch_size]
            points_to_insert = [
                PointStruct(
                    id=item["id"],
                    vector=item["vector"],
                    payload=item["payload"]
                )
                for item in batch
            ]
            
            try:
                client.upsert(
                    collection_name=target_collection,
                    points=points_to_insert
                )
                print(f"  Inserted batch {i//batch_size + 1} ({len(batch)} points)")
            except Exception as e:
                print(f"  Error inserting batch {i//batch_size + 1}: {e}")
        
        # Show final statistics
        final_info = client.get_collection(target_collection)
        print(f"\n{'='*80}")
        print(f"Consolidation Complete!")
        print(f"{'='*80}")
        print(f"Target Collection: {target_collection}")
        print(f"Total Points: {final_info.points_count}")
        print(f"New Patient IDs Assigned: patient_1 to patient_{patient_counter - 1}")
        print(f"\nYou can now query patients using IDs like: patient_1, patient_2, etc.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

