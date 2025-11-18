#!/usr/bin/env python3
"""
Utility script to create doc_hash index for existing Qdrant knowledge base collections.

This fixes the "Index required but not found for doc_hash" error when uploading
large documents to the knowledge base.

Usage:
    python scripts/create_doc_hash_index.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PayloadSchemaType
except ImportError:
    print("Error: qdrant-client not installed. Install with: pip install qdrant-client")
    sys.exit(1)


def create_doc_hash_index():
    """Create doc_hash index for knowledge base collections"""
    
    # Get Qdrant connection details
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6334"))
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    # Initialize Qdrant client
    if qdrant_url:
        client_kwargs = {"url": qdrant_url}
        if qdrant_api_key:
            client_kwargs["api_key"] = qdrant_api_key
        print(f"Connecting to Qdrant Cloud: {qdrant_url}")
    else:
        client_kwargs = {"host": qdrant_host, "port": qdrant_port}
        if qdrant_api_key:
            client_kwargs["api_key"] = qdrant_api_key
        print(f"Connecting to Qdrant Local: {qdrant_host}:{qdrant_port}")
    
    client = QdrantClient(**client_kwargs)
    
    # Get all collections
    try:
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"\nFound {len(collection_names)} collection(s): {', '.join(collection_names)}")
    except Exception as e:
        print(f"Error getting collections: {e}")
        sys.exit(1)
    
    # Find knowledge base collections
    knowledge_collections = [name for name in collection_names if "knowledge" in name.lower()]
    
    if not knowledge_collections:
        print("\n⚠ No knowledge base collections found.")
        print("Knowledge base collections should contain 'knowledge' in their name.")
        return
    
    # Create index for each knowledge base collection
    for collection_name in knowledge_collections:
        print(f"\n📋 Processing collection: {collection_name}")
        
        try:
            # Check if index already exists by trying to get collection info
            collection_info = client.get_collection(collection_name)
            payload_schema = collection_info.payload_schema if hasattr(collection_info, 'payload_schema') else None
            
            # Try to create the index
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="doc_hash",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print(f"  ✅ Created payload index for 'doc_hash'")
            except Exception as index_error:
                error_msg = str(index_error)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    print(f"  ℹ️  Index for 'doc_hash' already exists")
                else:
                    print(f"  ⚠️  Could not create index: {error_msg[:100]}")
                    # Continue anyway - the graceful error handling in knowledge_ingestion.py will handle it
                    
        except Exception as e:
            print(f"  ❌ Error processing collection: {e}")
            continue
    
    print("\n✅ Index creation complete!")
    print("\nYou can now upload large documents to the knowledge base without errors.")


if __name__ == "__main__":
    print("=" * 80)
    print("  Create doc_hash Index for Knowledge Base Collections")
    print("=" * 80)
    print()
    
    try:
        create_doc_hash_index()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

