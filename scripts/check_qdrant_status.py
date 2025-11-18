#!/usr/bin/env python3
"""
Check Qdrant Database Status

This script helps verify if Qdrant collections are being updated
by showing collection information, point counts, and recent entries.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_collection_status(collection_name: str):
    """Check status of a specific collection"""
    print(f"\n{'='*80}")
    print(f"Collection: {collection_name}")
    print(f"{'='*80}")
    
    try:
        # Initialize storage
        qdrant_url = os.getenv("QDRANT_URL")
        if qdrant_url:
            storage = QdrantStorage(
                url=qdrant_url,
                api_key=os.getenv("QDRANT_API_KEY"),
                collection_name=collection_name,
                vector_size=768
            )
            print(f"✓ Connected to Qdrant Cloud: {qdrant_url}")
        else:
            storage = QdrantStorage(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6334")),
                api_key=os.getenv("QDRANT_API_KEY"),
                collection_name=collection_name,
                vector_size=768
            )
            print(f"✓ Connected to Qdrant Local: {os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6334')}")
        
        # Get collection info
        try:
            collection_info = storage.get_collection_info()
            points_count = collection_info.get("points_count", 0)
            vectors_count = collection_info.get("vectors_count", 0)
            
            print(f"\n📊 Collection Statistics:")
            print(f"  - Total Points: {points_count:,}")
            print(f"  - Vectors: {vectors_count:,}")
            
            # Get recent points (last 10)
            print(f"\n📝 Recent Entries (Last 10):")
            try:
                scroll_result = storage.client.scroll(
                    collection_name=collection_name,
                    limit=10,
                    with_payload=True,
                    with_vectors=False,
                    order_by="timestamp" if collection_name == "hygiaai_cases" else None
                )
                
                if scroll_result[0]:
                    for i, point in enumerate(scroll_result[0][:10], 1):
                        payload = point.payload or {}
                        point_id = point.id
                        
                        # Extract relevant info based on collection
                        if collection_name == "clinical_kb_collection":
                            title = payload.get("title", "N/A")
                            source = payload.get("source", "N/A")
                            domain = payload.get("domain", "N/A")
                            print(f"  {i}. ID: {point_id}")
                            print(f"     Title: {title[:60]}...")
                            print(f"     Source: {source} | Domain: {domain}")
                        elif collection_name == "patient_memory_collection":
                            patient_id = payload.get("patient_id", "N/A")
                            session_id = payload.get("session_id", "N/A")
                            diagnosis = payload.get("diagnosis", "N/A")
                            print(f"  {i}. ID: {point_id}")
                            print(f"     Patient ID: {patient_id} | Session: {session_id}")
                            print(f"     Diagnosis: {diagnosis}")
                        elif collection_name == "hygiaai_cases":
                            case_id = payload.get("case_id", "N/A")
                            patient_id = payload.get("patient_id", "N/A")
                            timestamp = payload.get("timestamp", "N/A")
                            print(f"  {i}. ID: {point_id}")
                            print(f"     Case ID: {case_id} | Patient ID: {patient_id}")
                            print(f"     Timestamp: {timestamp}")
                        print()
                else:
                    print("  No entries found")
                    
            except Exception as scroll_error:
                print(f"  ⚠️  Could not retrieve recent entries: {scroll_error}")
            
            return True
            
        except Exception as info_error:
            print(f"  ❌ Collection not found or error: {info_error}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error connecting to Qdrant: {e}")
        return False


def main():
    """Main function to check all collections"""
    print("="*80)
    print("  Qdrant Database Status Checker")
    print("="*80)
    print(f"\nTimestamp: {datetime.now(timezone.utc).isoformat()}")
    
    # Check all collections
    collections = [
        "clinical_kb_collection",
        "patient_memory_collection",
        "hygiaai_cases"
    ]
    
    results = {}
    for collection in collections:
        results[collection] = check_collection_status(collection)
    
    # Summary
    print(f"\n{'='*80}")
    print("  Summary")
    print(f"{'='*80}")
    for collection, status in results.items():
        status_icon = "✓" if status else "✗"
        print(f"  {status_icon} {collection}: {'Available' if status else 'Not Available'}")
    
    print("\n💡 Tips:")
    print("  - Run this script after uploading patient data or knowledge base files")
    print("  - Compare point counts over time to verify updates")
    print("  - Check recent entries to see latest additions")
    print("  - Use Qdrant Dashboard (if available) for visual inspection")


if __name__ == "__main__":
    main()

