"""
Initialize Qdrant Collections for HygiaAI

This script initializes all required collections in the isolated Qdrant instance
with the correct schema and configuration based on the codebase.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.qdrant_storage import QdrantStorage
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def initialize_collections():
    """Initialize all HygiaAI collections with proper configuration"""
    print("=" * 70)
    print("Initializing Qdrant Collections for HygiaAI")
    print("=" * 70)
    print()
    
    # Get configuration from environment or use defaults
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6334"))  # Isolated instance port
    
    print(f"📡 Connecting to Qdrant at {host}:{port}...")
    
    try:
        # Connect to Qdrant
        client = QdrantClient(host=host, port=port)
        
        # Test connection
        collections = client.get_collections()
        print(f"✅ Connected to Qdrant successfully!")
        print()
        
        # Define collections based on codebase configuration
        collections_to_create = [
            {
                "name": "hygiaai_transcripts",
                "vector_size": 768,  # BioBERT embedding size
                "description": "Main transcript storage collection"
            },
            {
                "name": "hygiaai_knowledge_base",
                "vector_size": 768,  # BioBERT for text, can support multi-vector
                "description": "Knowledge base documents collection"
            },
            {
                "name": "hygiaai_cases",
                "vector_size": 768,  # BioBERT for clinical cases
                "description": "Clinical cases collection"
            }
        ]
        
        existing_collections = [c.name for c in collections.collections]
        
        print("📋 Collection Initialization:")
        print("-" * 70)
        
        for collection_config in collections_to_create:
            collection_name = collection_config["name"]
            vector_size = collection_config["vector_size"]
            description = collection_config["description"]
            
            if collection_name in existing_collections:
                # Check existing collection configuration
                try:
                    info = client.get_collection(collection_name)
                    existing_size = info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else None
                    
                    if existing_size == vector_size:
                        print(f"✅ {collection_name}")
                        print(f"   {description}")
                        print(f"   Vector Size: {vector_size} (already configured)")
                        print()
                    else:
                        print(f"⚠️  {collection_name}")
                        print(f"   {description}")
                        print(f"   Existing Vector Size: {existing_size}")
                        print(f"   Expected Vector Size: {vector_size}")
                        print(f"   ⚠️  Size mismatch - collection needs to be recreated")
                        print()
                except Exception as e:
                    print(f"❌ {collection_name}")
                    print(f"   Error checking collection: {e}")
                    print()
            else:
                # Create new collection
                try:
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    print(f"✅ {collection_name}")
                    print(f"   {description}")
                    print(f"   Vector Size: {vector_size} (created)")
                    print()
                except Exception as e:
                    print(f"❌ {collection_name}")
                    print(f"   Error creating collection: {e}")
                    print()
        
        # Verify using QdrantStorage (which is what the app uses)
        print("🔍 Verifying Collections via QdrantStorage:")
        print("-" * 70)
        
        for collection_config in collections_to_create:
            collection_name = collection_config["name"]
            vector_size = collection_config["vector_size"]
            
            try:
                storage = QdrantStorage(
                    host=host,
                    port=port,
                    collection_name=collection_name,
                    vector_size=vector_size,
                    enable_encryption=False,  # For initialization
                    enable_deidentification=False  # For initialization
                )
                print(f"✅ {collection_name} - Verified via QdrantStorage")
            except Exception as e:
                print(f"❌ {collection_name} - Verification failed: {e}")
        
        print()
        print("=" * 70)
        print("✅ Collection Initialization Complete")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  • Host: {host}")
        print(f"  • Port: {port}")
        print(f"  • Collections initialized: {len(collections_to_create)}")
        print()
        print("Collections ready for use:")
        for collection_config in collections_to_create:
            print(f"  • {collection_config['name']} ({collection_config['vector_size']}D)")
        print()
        
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        print()
        print("Make sure:")
        print("  1. Docker Desktop is running")
        print("  2. Qdrant container is started:")
        print("     docker start hygiaai-qdrant")
        print("     OR")
        print("     .\\examples\\setup_isolated_qdrant.ps1")
        print()
        return False
    
    return True


if __name__ == "__main__":
    success = initialize_collections()
    sys.exit(0 if success else 1)

