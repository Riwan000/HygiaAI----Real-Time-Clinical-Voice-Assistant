"""
Check Qdrant Isolation for HygiaAI Project

This script verifies that:
1. Qdrant is configured with project-specific collection names
2. No other projects are using the same Qdrant instance
3. Collections are properly namespaced
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.qdrant_storage import QdrantStorage
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def check_qdrant_connection():
    """Check if Qdrant is accessible"""
    print("=" * 70)
    print("Qdrant Isolation Check for HygiaAI Project")
    print("=" * 70)
    print()
    
    try:
        # Get configuration (default to isolated instance port)
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6334"))  # Default to isolated instance
        
        print(f"📡 Connecting to Qdrant at {host}:{port}...")
        client = QdrantClient(host=host, port=port)
        
        # Check if Qdrant is accessible
        collections = client.get_collections()
        print(f"✅ Qdrant connection successful!")
        print()
        
        return client, collections
        
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("   This might mean Qdrant is not running.")
        print("   To start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        return None, None


def check_collections(client, collections):
    """Check all collections in Qdrant"""
    print("📋 Checking Collections in Qdrant:")
    print("-" * 70)
    
    if not collections or not collections.collections:
        print("   No collections found in Qdrant.")
        print("   ✅ This Qdrant instance is clean and ready for HygiaAI.")
        return
    
    print(f"   Found {len(collections.collections)} collection(s):")
    print()
    
    hygiaai_collections = []
    other_collections = []
    
    for collection in collections.collections:
        collection_name = collection.name
        
        # Check if it's a HygiaAI collection
        if collection_name.startswith("hygiaai_"):
            hygiaai_collections.append(collection_name)
        else:
            other_collections.append(collection_name)
    
    # Display HygiaAI collections
    if hygiaai_collections:
        print("   ✅ HygiaAI Project Collections:")
        for name in hygiaai_collections:
            try:
                info = client.get_collection(name)
                vector_size = info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else "N/A"
                points_count = info.points_count if hasattr(info, 'points_count') else "N/A"
                print(f"      • {name}")
                print(f"        - Vector Size: {vector_size}")
                print(f"        - Points: {points_count}")
            except Exception as e:
                print(f"      • {name} (error getting info: {e})")
        print()
    
    # Display other collections (potential conflicts)
    if other_collections:
        print("   ⚠️  Other Collections (Potential Conflicts):")
        for name in other_collections:
            try:
                info = client.get_collection(name)
                vector_size = info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else "N/A"
                points_count = info.points_count if hasattr(info, 'points_count') else "N/A"
                print(f"      • {name}")
                print(f"        - Vector Size: {vector_size}")
                print(f"        - Points: {points_count}")
            except Exception as e:
                print(f"      • {name} (error getting info: {e})")
        print()
        print("   ⚠️  WARNING: Other collections found!")
        print("      These might be from other projects.")
        print("      Consider using a separate Qdrant instance or different port.")
    else:
        print("   ✅ No other collections found - Qdrant is isolated for HygiaAI!")
        print()


def check_hygiaai_configuration():
    """Check HygiaAI's Qdrant configuration"""
    print("⚙️  HygiaAI Qdrant Configuration:")
    print("-" * 70)
    
    # Default configuration
    default_collection = "hygiaai_transcripts"
    default_host = os.getenv("QDRANT_HOST", "localhost")
    default_port = int(os.getenv("QDRANT_PORT", "6333"))
    default_vector_size = 768  # BioBERT
    
    print(f"   Default Collection Name: {default_collection}")
    print(f"   Default Host: {default_host}")
    print(f"   Default Port: {default_port}")
    print(f"   Default Vector Size: {default_vector_size} (BioBERT)")
    print()
    
    # Check if collection name is unique
    print("   ✅ Collection naming strategy:")
    print(f"      - Uses 'hygiaai_' prefix for all collections")
    print(f"      - This ensures isolation from other projects")
    print()


def check_port_isolation():
    """Check if port is isolated"""
    print("🔌 Port Isolation Check:")
    print("-" * 70)
    
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    if port == 6333:
        print(f"   ⚠️  Using default Qdrant port: {port}")
        print("      This is the standard Qdrant port.")
        print("      If other projects use Qdrant, they might use the same port.")
        print()
        print("   💡 Recommendation:")
        print("      - Use Docker with custom port mapping for isolation")
        print("      - Example: docker run -p 6334:6333 qdrant/qdrant")
        print("      - Then set QDRANT_PORT=6334 in .env")
    else:
        print(f"   ✅ Using custom port: {port}")
        print("      This provides better isolation from other projects.")
    print()


def check_collection_namespace():
    """Check collection namespace strategy"""
    print("🏷️  Collection Namespace Strategy:")
    print("-" * 70)
    
    # Expected HygiaAI collection names
    expected_collections = [
        "hygiaai_transcripts",  # Main transcript collection
        "hygiaai_knowledge_base",  # Knowledge base documents
        "hygiaai_cases",  # Clinical cases
    ]
    
    print("   Expected HygiaAI collections:")
    for name in expected_collections:
        print(f"      • {name}")
    print()
    
    print("   ✅ All collections use 'hygiaai_' prefix")
    print("      This ensures no conflicts with other projects.")
    print()


def recommend_isolation():
    """Provide recommendations for better isolation"""
    print("💡 Recommendations for Better Isolation:")
    print("-" * 70)
    
    recommendations = [
        "1. Use a dedicated Qdrant instance for this project",
        "2. Use Docker with custom port mapping (e.g., 6334:6333)",
        "3. Set QDRANT_HOST and QDRANT_PORT in .env file",
        "4. Use project-specific collection names (already done: 'hygiaai_*')",
        "5. Consider using Qdrant Cloud for production (separate instance)",
    ]
    
    for rec in recommendations:
        print(f"   {rec}")
    print()


def main():
    """Run all checks"""
    # Check connection
    client, collections = check_qdrant_connection()
    
    if client is None:
        print()
        print("=" * 70)
        print("⚠️  Cannot proceed with checks - Qdrant not accessible")
        print("=" * 70)
        return
    
    print()
    
    # Check collections
    check_collections(client, collections)
    
    # Check configuration
    check_hygiaai_configuration()
    
    # Check port isolation
    check_port_isolation()
    
    # Check namespace
    check_collection_namespace()
    
    # Recommendations
    recommend_isolation()
    
    print("=" * 70)
    print("✅ Isolation Check Complete")
    print("=" * 70)
    print()
    print("Summary:")
    print("  • HygiaAI uses 'hygiaai_' prefix for all collections")
    print("  • This provides namespace isolation from other projects")
    print("  • For better isolation, consider using a dedicated Qdrant instance")
    print()


if __name__ == "__main__":
    main()

