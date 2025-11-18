#!/usr/bin/env python3
"""
Explore Qdrant Database
Shows collections, point counts, and sample data from Qdrant
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from datetime import datetime
import json

def get_qdrant_client():
    """Get Qdrant client based on environment configuration"""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if qdrant_url:
        # Cloud connection
        return QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
    else:
        # Local connection
        return QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            api_key=qdrant_api_key
        )

def format_timestamp(timestamp_str):
    """Format ISO timestamp string for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def explore_collection(client, collection_name):
    """Explore a specific collection"""
    try:
        collection_info = client.get_collection(collection_name)
        print(f"\n{'='*80}")
        print(f"Collection: {collection_name}")
        print(f"{'='*80}")
        print(f"Points Count: {collection_info.points_count}")
        print(f"Vector Size: {collection_info.config.params.vectors.size}")
        print(f"Distance: {collection_info.config.params.vectors.distance}")
        
        # Get sample points
        if collection_info.points_count > 0:
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=min(5, collection_info.points_count),
                with_payload=True,
                with_vectors=False
            )
            
            print(f"\nSample Points (showing up to 5):")
            print("-" * 80)
            
            for i, point in enumerate(scroll_result[0], 1):
                print(f"\nPoint {i} (ID: {point.id}):")
                payload = point.payload or {}
                
                # Show key fields
                if "transcript" in payload:
                    transcript = payload["transcript"]
                    preview = transcript[:200] + "..." if len(transcript) > 200 else transcript
                    print(f"  Transcript: {preview}")
                
                if "patient_id" in payload:
                    print(f"  Patient ID: {payload['patient_id']}")
                
                if "timestamp" in payload:
                    print(f"  Timestamp: {format_timestamp(payload['timestamp'])}")
                
                if "diagnosis" in payload:
                    print(f"  Diagnosis: {payload['diagnosis']}")
                
                if "region" in payload:
                    print(f"  Region: {payload['region']}")
                
                if "modality_type" in payload:
                    print(f"  Modality: {payload['modality_type']}")
                
                if "domain" in payload:
                    print(f"  Domain: {payload['domain']}")
                
                if "source" in payload:
                    print(f"  Source: {payload['source']}")
                
                if "case_metadata" in payload:
                    metadata = payload["case_metadata"]
                    print(f"  Case Metadata:")
                    if isinstance(metadata, dict):
                        for key, value in list(metadata.items())[:5]:
                            print(f"    {key}: {value}")
                
                # Show medical entities if present
                if "medical_entities" in payload:
                    entities = payload["medical_entities"]
                    if isinstance(entities, list) and len(entities) > 0:
                        print(f"  Medical Entities: {len(entities)} found")
                        for entity in entities[:3]:
                            if isinstance(entity, dict):
                                print(f"    - {entity.get('text', 'N/A')} ({entity.get('entity_type', 'N/A')})")
        else:
            print("\nNo points in this collection.")
            
    except Exception as e:
        print(f"Error exploring collection {collection_name}: {e}")

def main():
    """Main function"""
    print("Qdrant Database Explorer")
    print("=" * 80)
    
    try:
        client = get_qdrant_client()
        
        # List all collections
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        print(f"\nFound {len(collection_names)} collection(s):")
        for name in collection_names:
            print(f"  - {name}")
        
        if not collection_names:
            print("\nNo collections found in Qdrant.")
            return
        
        # Show summary
        print(f"\n{'='*80}")
        print("Collection Summary")
        print(f"{'='*80}")
        for name in collection_names:
            try:
                info = client.get_collection(name)
                print(f"{name:40s} {info.points_count:>10,} points")
            except Exception as e:
                print(f"{name:40s} Error: {e}")
        
        # Explore each collection
        for name in collection_names:
            explore_collection(client, name)
        
        print(f"\n{'='*80}")
        print("Exploration Complete")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        print("\nMake sure Qdrant is running and environment variables are set:")
        print("  - QDRANT_HOST (default: localhost)")
        print("  - QDRANT_PORT (default: 6334)")
        print("  - QDRANT_URL (for cloud)")
        print("  - QDRANT_API_KEY (optional)")
        sys.exit(1)

if __name__ == "__main__":
    main()

