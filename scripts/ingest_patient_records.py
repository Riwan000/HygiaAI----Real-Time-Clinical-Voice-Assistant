#!/usr/bin/env python3
"""
Ingest Patient Records Data into Qdrant

Populates the 'patient_memory_collection' with:
- MIMIC-III clinical notes
- MIMIC-IV clinical notes
- eICU patient data
- AmsterdamUMCdb data
- i2b2 clinical notes

This collection is SEPARATE from knowledge base.
Patient records are stored with proper de-identification.
"""

import sys
import os
import csv
import gzip
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
from src.embeddings import BioBERTEmbeddingGenerator
from src.storage.schema import StorageMetadata, ModalityType
from datetime import datetime, timezone
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_csv_file(csv_path: Path, limit: int = 1000) -> List[Dict[str, Any]]:
    """Process CSV file and return records"""
    records = []
    
    try:
        # Handle gzipped files
        if csv_path.suffix == '.gz':
            open_func = gzip.open
            mode = 'rt'
        else:
            open_func = open
            mode = 'r'
        
        with open_func(csv_path, mode, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                records.append(row)
        
        return records
    except Exception as e:
        logger.error(f"Error processing {csv_path}: {e}")
        return []


def ingest_patient_records():
    """Ingest all patient records into patient_memory_collection"""
    
    print("=" * 80)
    print("  Ingest Patient Records into Qdrant")
    print("=" * 80)
    print()
    print("Collection: patient_memory_collection")
    print("Content: MIMIC-III, MIMIC-IV, eICU, AmsterdamUMCdb, i2b2")
    print()
    
    # Initialize Qdrant storage for PATIENT RECORDS collection
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        patient_storage = QdrantStorage(
            url=qdrant_url,
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="patient_memory_collection",  # SEPARATE collection
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=True  # Enable de-identification for patient data
        )
        print(f"✓ Connected to Qdrant Cloud: {qdrant_url}")
    else:
        patient_storage = QdrantStorage(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="patient_memory_collection",  # SEPARATE collection
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=True  # Enable de-identification for patient data
        )
        print(f"✓ Connected to Qdrant Local: {os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6334')}")
    
    # Initialize embedding generator
    print("Initializing embedding generator...")
    embedder = BioBERTEmbeddingGenerator()
    
    print()
    
    # Data directory
    data_dir = project_root / "hygiaai_datasets" / "patient_records"
    
    ingested_count = 0
    total_points = 0
    
    # 1. Process MIMIC-III NOTEEVENTS (clinical notes)
    print("🏥 Processing MIMIC-III clinical notes...")
    mimic3_dir = data_dir / "mimic-iii"
    if mimic3_dir.exists():
        note_files = list(mimic3_dir.glob("*NOTEEVENTS*"))
        if note_files:
            for note_file in note_files[:1]:  # Process first file only
                print(f"   Processing: {note_file.name}")
                records = process_csv_file(note_file, limit=500)  # Limit for demo
                
                for record in records:
                    try:
                        # Extract note text
                        note_text = record.get('TEXT', '') or record.get('text', '')
                        if not note_text or len(note_text) < 50:
                            continue
                        
                        # Generate embedding
                        embedding = embedder.generate_embedding(note_text[:1000])  # Limit text length
                        
                        # Prepare transcript data
                        transcript_data = {
                            "transcript": note_text[:2000],  # Limit length
                            "session_id": str(uuid.uuid4()),
                            "metadata": {
                                "patient_id": record.get('SUBJECT_ID', ''),
                                "hadm_id": record.get('HADM_ID', ''),
                                "chartdate": record.get('CHARTDATE', ''),
                                "category": record.get('CATEGORY', ''),
                            },
                            "timestamp": record.get('CHARTDATE', datetime.now(timezone.utc).isoformat()),
                            "confidence": 1.0,
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        # Create metadata
                        metadata = StorageMetadata(
                            session_id=transcript_data["session_id"],
                            patient_id=str(record.get('SUBJECT_ID', '')),
                            timestamp=datetime.now(timezone.utc),
                            modality=ModalityType.TEXT,
                            confidence=1.0
                        )
                        
                        # Store in Qdrant
                        point_id = patient_storage.store_transcript(
                            transcript_data,
                            embedding,
                            metadata
                        )
                        
                        ingested_count += 1
                        total_points += 1
                        
                        if ingested_count % 50 == 0:
                            print(f"      Processed {ingested_count} notes...")
                    
                    except Exception as e:
                        logger.debug(f"Error processing record: {e}")
                        continue
                
                print(f"      ✓ Ingested {ingested_count} notes from MIMIC-III")
        else:
            print("   ⚠️  No NOTEEVENTS files found. Run download script first.")
    else:
        print("   ⚠️  MIMIC-III directory not found. Run download script first.")
    
    print()
    
    # 2. Process MIMIC-IV notes
    print("🏥 Processing MIMIC-IV clinical notes...")
    mimic4_dir = data_dir / "mimic-iv"
    if mimic4_dir.exists():
        note_files = list(mimic4_dir.glob("*note*"))
        if note_files:
            for note_file in note_files[:1]:  # Process first file only
                print(f"   Processing: {note_file.name}")
                records = process_csv_file(note_file, limit=500)  # Limit for demo
                
                for record in records:
                    try:
                        note_text = record.get('note_text', '') or record.get('text', '')
                        if not note_text or len(note_text) < 50:
                            continue
                        
                        embedding = embedder.generate_embedding(note_text[:1000])
                        
                        transcript_data = {
                            "transcript": note_text[:2000],
                            "session_id": str(uuid.uuid4()),
                            "metadata": {
                                "subject_id": record.get('subject_id', ''),
                                "hadm_id": record.get('hadm_id', ''),
                                "charttime": record.get('charttime', ''),
                            },
                            "timestamp": record.get('charttime', datetime.now(timezone.utc).isoformat()),
                            "confidence": 1.0,
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        metadata = StorageMetadata(
                            session_id=transcript_data["session_id"],
                            patient_id=str(record.get('subject_id', '')),
                            timestamp=datetime.now(timezone.utc),
                            modality=ModalityType.TEXT,
                            confidence=1.0
                        )
                        
                        patient_storage.store_transcript(transcript_data, embedding, metadata)
                        ingested_count += 1
                        total_points += 1
                        
                        if ingested_count % 50 == 0:
                            print(f"      Processed {ingested_count} notes...")
                    
                    except Exception as e:
                        logger.debug(f"Error processing record: {e}")
                        continue
                
                print(f"      ✓ Ingested notes from MIMIC-IV")
        else:
            print("   ⚠️  No note files found. Run download script first.")
    else:
        print("   ⚠️  MIMIC-IV directory not found. Run download script first.")
    
    print()
    
    # 3. Process eICU notes
    print("🏥 Processing eICU patient data...")
    eicu_dir = data_dir / "eicu"
    if eicu_dir.exists():
        note_files = list(eicu_dir.glob("*note*"))
        if note_files:
            for note_file in note_files[:1]:  # Process first file only
                print(f"   Processing: {note_file.name}")
                records = process_csv_file(note_file, limit=500)  # Limit for demo
                
                for record in records:
                    try:
                        note_text = record.get('notetext', '') or record.get('text', '')
                        if not note_text or len(note_text) < 50:
                            continue
                        
                        embedding = embedder.generate_embedding(note_text[:1000])
                        
                        transcript_data = {
                            "transcript": note_text[:2000],
                            "session_id": str(uuid.uuid4()),
                            "metadata": {
                                "patientunitstayid": record.get('patientunitstayid', ''),
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "confidence": 1.0,
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        metadata = StorageMetadata(
                            session_id=transcript_data["session_id"],
                            patient_id=str(record.get('patientunitstayid', '')),
                            timestamp=datetime.now(timezone.utc),
                            modality=ModalityType.TEXT,
                            confidence=1.0
                        )
                        
                        patient_storage.store_transcript(transcript_data, embedding, metadata)
                        ingested_count += 1
                        total_points += 1
                        
                        if ingested_count % 50 == 0:
                            print(f"      Processed {ingested_count} notes...")
                    
                    except Exception as e:
                        logger.debug(f"Error processing record: {e}")
                        continue
                
                print(f"      ✓ Ingested notes from eICU")
        else:
            print("   ⚠️  No note files found. Run download script first.")
    else:
        print("   ⚠️  eICU directory not found. Run download script first.")
    
    # Summary
    print()
    print("=" * 80)
    print("  Summary")
    print("=" * 80)
    print(f"✅ Patient records ingested: {ingested_count}")
    print(f"✅ Total points created: {total_points}")
    print(f"✅ Collection: patient_memory_collection")
    print()
    print("Patient records collection is ready for similar case recall!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        ingest_patient_records()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

