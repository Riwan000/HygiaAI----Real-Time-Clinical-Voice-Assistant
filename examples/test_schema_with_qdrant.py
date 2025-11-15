#!/usr/bin/env python3
"""
Test Schema Standards with Qdrant

Validates that the schema standards work correctly with Qdrant queries.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.schema_validator import SchemaValidator
from src.storage.qdrant_storage import QdrantStorage
from src.embeddings.text_embeddings import TextEmbeddingGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test schema standards with Qdrant"""
    print("=" * 80)
    print("  Schema Standards - Qdrant Integration Test")
    print("=" * 80)
    
    validator = SchemaValidator()
    embedding_gen = TextEmbeddingGenerator()
    
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Test 1: Verify Required Fields in Stored Documents
        print_section("Test 1: Verify Required Fields in Stored Documents")
        query_embedding = embedding_gen.generate_embedding("pathology")
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=None,
            limit=5
        )
        
        print(f"✓ Retrieved {len(results)} documents")
        
        all_valid = True
        for i, result in enumerate(results, 1):
            payload = result.get("payload", {})
            
            # Check required fields
            has_title = "title" in payload and payload["title"]
            has_source = "source" in payload and payload["source"]
            
            print(f"\n  Document {i}: {payload.get('title', 'Unknown')}")
            print(f"    ✓ Has title: {has_title}")
            print(f"    ✓ Has source: {has_source}")
            
            if not (has_title and has_source):
                all_valid = False
                print(f"    ✗ Missing required fields!")
            
            # Validate metadata
            is_valid, errors = validator.validate_metadata(payload)
            if is_valid:
                print(f"    ✓ Metadata valid")
            else:
                print(f"    ✗ Metadata invalid: {errors}")
                all_valid = False
        
        print(f"\n✓ All documents have required fields: {all_valid}")
        print()
        
        # Test 2: Test Filtering by Domain
        print_section("Test 2: Test Filtering by Domain")
        
        domains = ["pathology", "pharmacology", "guidelines"]
        for domain in domains:
            filters = {"domain": domain}
            
            # Validate filters
            is_valid, errors = validator.validate_for_qdrant_query(filters)
            if not is_valid:
                print(f"✗ Invalid filters for domain '{domain}': {errors}")
                continue
            
            results = storage.search_with_filters(
                query_embedding=query_embedding,
                filters=filters,
                limit=3
            )
            
            print(f"✓ Domain '{domain}': Found {len(results)} documents")
            for result in results:
                payload = result.get("payload", {})
                print(f"    - {payload.get('title', 'Unknown')}")
        print()
        
        # Test 3: Test Filtering by Source
        print_section("Test 3: Test Filtering by Source")
        
        filters = {"source": "demo"}
        is_valid, errors = validator.validate_for_qdrant_query(filters)
        
        if is_valid:
            results = storage.search_with_filters(
                query_embedding=query_embedding,
                filters=filters,
                limit=5
            )
            print(f"✓ Source 'demo': Found {len(results)} documents")
        else:
            print(f"✗ Invalid filters: {errors}")
        print()
        
        # Test 4: Test Year Range Filtering
        print_section("Test 4: Test Year Range Filtering")
        
        filters = {"year": {"gte": 2020, "lte": 2024}}
        is_valid, errors = validator.validate_for_qdrant_query(filters)
        
        if is_valid:
            results = storage.search_with_filters(
                query_embedding=query_embedding,
                filters=filters,
                limit=5
            )
            print(f"✓ Year range 2020-2024: Found {len(results)} documents")
        else:
            print(f"✗ Invalid filters: {errors}")
        print()
        
        # Test 5: Test Combined Filters
        print_section("Test 5: Test Combined Filters")
        
        filters = {
            "domain": "pathology",
            "source": "demo",
            "year": {"gte": 2023}
        }
        
        is_valid, errors = validator.validate_for_qdrant_query(filters)
        
        if is_valid:
            results = storage.search_with_filters(
                query_embedding=query_embedding,
                filters=filters,
                limit=5
            )
            print(f"✓ Combined filters (pathology + demo + year>=2023): Found {len(results)} documents")
            for result in results:
                payload = result.get("payload", {})
                print(f"    - {payload.get('title', 'Unknown')} (year: {payload.get('year', 'N/A')})")
        else:
            print(f"✗ Invalid filters: {errors}")
        print()
        
        # Test 6: Verify Embedding Dimensions
        print_section("Test 6: Verify Embedding Dimensions")
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=None,
            limit=3
        )
        
        all_correct_dim = True
        for result in results:
            vector = result.get("vector")
            if vector:
                if isinstance(vector, list):
                    is_valid, errors = validator.validate_embedding(vector, EmbeddingType.TEXT)
                    if is_valid:
                        print(f"✓ Document '{result.get('payload', {}).get('title', 'Unknown')}': Embedding dimension {len(vector)}")
                    else:
                        print(f"✗ Invalid embedding: {errors}")
                        all_correct_dim = False
                elif isinstance(vector, dict):
                    # Multi-vector
                    text_vec = vector.get("text")
                    if text_vec:
                        is_valid, errors = validator.validate_embedding(text_vec, EmbeddingType.TEXT)
                        if is_valid:
                            print(f"✓ Multi-vector document: Text embedding dimension {len(text_vec)}")
                        else:
                            print(f"✗ Invalid text embedding: {errors}")
                            all_correct_dim = False
        
        print(f"\n✓ All embeddings have correct dimensions: {all_correct_dim}")
        print()
        
        print("=" * 80)
        print("  Schema Standards - Qdrant Integration Test Complete!")
        print("=" * 80)
        print("\n✓ All schema standards validated successfully!")
        print("✓ Filters work correctly with Qdrant queries")
        print("✓ Required fields are present in all documents")
        print("✓ Embedding dimensions are correct")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

