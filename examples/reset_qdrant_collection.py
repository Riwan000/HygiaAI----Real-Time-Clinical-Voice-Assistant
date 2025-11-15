#!/usr/bin/env python3
"""
Reset Qdrant Collection

This script deletes and recreates the Qdrant collection with the correct vector size.
Use this if you need to change the vector dimension (e.g., from 384 to 768).
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.qdrant_storage import QdrantStorage

def reset_collection(collection_name: str = "clinical_cases", vector_size: int = 768):
    """Delete and recreate the Qdrant collection"""
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name=collection_name,
            vector_size=vector_size
        )
        
        # Delete existing collection
        try:
            storage.client.delete_collection(collection_name)
            print(f"✓ Deleted existing collection: {collection_name}")
        except Exception as e:
            print(f"⚠ Could not delete collection (may not exist): {e}")
        
        # Recreate collection
        storage._ensure_collection()
        print(f"✓ Created collection: {collection_name} with vector_size={vector_size}")
        
        # Verify
        info = storage.get_collection_info()
        print(f"\nCollection Info:")
        print(f"  Name: {info.get('name')}")
        print(f"  Vector Size: {info.get('vector_size')}")
        print(f"  Points Count: {info.get('points_count', 0)}")
        print(f"  Status: {info.get('status')}")
        
    except Exception as e:
        print(f"✗ Error resetting collection: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset Qdrant collection")
    parser.add_argument("--collection", default="clinical_cases", help="Collection name")
    parser.add_argument("--vector-size", type=int, default=768, help="Vector size")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Qdrant Collection Reset")
    print("=" * 80)
    print(f"\nCollection: {args.collection}")
    print(f"Vector Size: {args.vector_size}")
    print("\n⚠ WARNING: This will delete all existing data in the collection!")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() in ["yes", "y"]:
        success = reset_collection(args.collection, args.vector_size)
        if success:
            print("\n✓ Collection reset successfully!")
        else:
            print("\n✗ Failed to reset collection")
            sys.exit(1)
    else:
        print("\nCancelled.")
        sys.exit(0)

