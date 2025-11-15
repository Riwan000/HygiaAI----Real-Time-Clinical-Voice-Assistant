#!/usr/bin/env python3
"""
Test Schema Validation

Tests the schema validator with real documents and validates against Qdrant.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.schema_validator import SchemaValidator
from src.storage.schema import (
    KnowledgeBaseMetadata,
    KnowledgeBaseSchema,
    EmbeddingType,
    AccessType
)
from src.storage.qdrant_storage import QdrantStorage
from src.embeddings.text_embeddings import TextEmbeddingGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test schema validation"""
    print("=" * 80)
    print("  Schema Validation Test")
    print("=" * 80)
    
    validator = SchemaValidator()
    
    # Test 1: Valid Metadata
    print_section("Test 1: Valid Metadata")
    valid_metadata = {
        "title": "Introduction to Pathology",
        "source": "demo",
        "domain": "pathology",
        "year": 2023,
        "embedding_type": "text",
        "access_type": "open",
        "provenance_url": "https://demo.hygiaai.com/pathology.html",
        "version": "1.0",
        "author": "Dr. Medical Education",
        "chunk_index": 0,
        "chunk_total": 3
    }
    
    is_valid, errors = validator.validate_metadata(valid_metadata)
    print(f"✓ Valid metadata: {is_valid}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    print()
    
    # Test 2: Invalid Metadata
    print_section("Test 2: Invalid Metadata")
    invalid_metadata = {
        "title": "",  # Empty title
        # Missing source
        "domain": "invalid_domain",
        "year": 1800,  # Invalid year
        "provenance_url": "not-a-url"
    }
    
    is_valid, errors = validator.validate_metadata(invalid_metadata)
    print(f"✗ Invalid metadata: {is_valid}")
    print(f"  Found {len(errors)} errors:")
    for error in errors:
        print(f"    - {error}")
    print()
    
    # Test 3: Valid Document
    print_section("Test 3: Valid Document")
    valid_document = {
        "title": "Test Document",
        "text": "This is a test document with medical content about pathology and disease diagnosis."
    }
    
    is_valid, errors = validator.validate_document(valid_document)
    print(f"✓ Valid document: {is_valid}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    print()
    
    # Test 4: Valid Embedding
    print_section("Test 4: Valid Embedding")
    embedding_gen = TextEmbeddingGenerator()
    test_text = "Pathology is the study of disease."
    embedding = embedding_gen.generate_embedding(test_text)
    
    is_valid, errors = validator.validate_embedding(embedding, EmbeddingType.TEXT)
    print(f"✓ Valid embedding: {is_valid}")
    print(f"  Dimension: {len(embedding)} (expected: 768)")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    print()
    
    # Test 5: Valid Chunking
    print_section("Test 5: Valid Chunking")
    is_valid, errors = validator.validate_chunking(512, 50)
    print(f"✓ Valid chunking (512, 50): {is_valid}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    print()
    
    # Test 6: Complete Schema Validation
    print_section("Test 6: Complete Schema Validation")
    metadata = KnowledgeBaseMetadata(
        title="Test Document",
        source="demo",
        domain="pathology",
        year=2023,
        embedding_type=EmbeddingType.TEXT,
        access_type=AccessType.OPEN,
        provenance_url="https://demo.hygiaai.com/test.html"
    )
    
    schema = KnowledgeBaseSchema(
        id="test-schema-id",
        text_embedding=embedding,
        metadata=metadata,
        payload={"text": test_text}
    )
    
    is_valid, errors = validator.validate_knowledge_base_schema(schema)
    print(f"✓ Complete schema validation: {is_valid}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    print()
    
    # Test 7: Qdrant Filter Validation
    print_section("Test 7: Qdrant Filter Validation")
    valid_filters = {
        "domain": "pathology",
        "year": {"gte": 2020, "lte": 2023},
        "source": "demo"
    }
    
    is_valid, errors = validator.validate_for_qdrant_query(valid_filters)
    print(f"✓ Valid filters: {is_valid}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    print()
    
    # Test 8: Integration Test - Validate Existing Documents
    print_section("Test 8: Validate Existing Documents in Qdrant")
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Get a sample document from Qdrant
        results = storage.search_with_filters(
            query_embedding=embedding,
            filters=None,
            limit=1
        )
        
        if results:
            result = results[0]
            payload = result.get("payload", {})
            
            print(f"✓ Retrieved document: {payload.get('title', 'Unknown')}")
            
            # Validate metadata
            is_valid, errors = validator.validate_metadata(payload)
            print(f"  Metadata valid: {is_valid}")
            if errors:
                print(f"  Errors: {errors}")
            
            # Validate embedding dimension
            vector = result.get("vector")
            if vector:
                if isinstance(vector, list):
                    is_valid, errors = validator.validate_embedding(vector, EmbeddingType.TEXT)
                    print(f"  Embedding valid: {is_valid}")
                    if errors:
                        print(f"  Errors: {errors}")
        else:
            print("  No documents found in collection")
            
    except Exception as e:
        print(f"  ⚠ Could not connect to Qdrant: {e}")
    print()
    
    print("=" * 80)
    print("  Schema Validation Test Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()

