#!/usr/bin/env python3
"""Check patient_id structure in Qdrant"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from qdrant_client import QdrantClient

def main():
    client = QdrantClient(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6334")),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    
    # Check patient_memory_collection
    result = client.scroll(
        collection_name="patient_memory_collection",
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    print("Sample patient_id values:")
    for i, point in enumerate(result[0][:10], 1):
        payload = point.payload or {}
        pid1 = payload.get("patient_id")
        pid2 = payload.get("case_metadata", {}).get("patient_id") if isinstance(payload.get("case_metadata"), dict) else None
        print(f"{i}. Point ID: {point.id}")
        print(f"   Top-level patient_id: {pid1}")
        print(f"   case_metadata.patient_id: {pid2}")
        print()

if __name__ == "__main__":
    main()

