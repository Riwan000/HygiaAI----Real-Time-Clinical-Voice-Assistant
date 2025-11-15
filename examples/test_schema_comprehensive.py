#!/usr/bin/env python3
"""
Comprehensive Schema Validation Test

Tests all aspects of the schema standard including edge cases and integration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.schema_validator import SchemaValidator, SchemaValidationError
from src.storage.schema import (
    KnowledgeBaseMetadata,
    KnowledgeBaseSchema,
    EmbeddingType,
    AccessType
)
from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings.text_embeddings import TextEmbeddingGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_metadata_validation_comprehensive():
    """Comprehensive metadata validation tests"""
    print_section("Comprehensive Metadata Validation")
    
    validator = SchemaValidator()
    
    test_cases = [
        {
            "name": "Valid complete metadata",
            "metadata": {
                "title": "Complete Document",
                "source": "test",
                "domain": "pathology",
                "year": 2023,
                "embedding_type": "text",
                "access_type": "open",
                "provenance_url": "https://example.com/doc.html",
                "version": "1.0",
                "author": "Dr. Test",
                "chunk_index": 0,
                "chunk_total": 5
            },
            "should_pass": True
        },
        {
            "name": "Minimal valid metadata (only required)",
            "metadata": {
                "title": "Minimal Doc",
                "source": "test"
            },
            "should_pass": True
        },
        {
            "name": "All valid domains",
            "metadata": {
                "title": "Test",
                "source": "test",
                "domain": "pathology"
            },
            "should_pass": True
        },
        {
            "name": "Invalid domain",
            "metadata": {
                "title": "Test",
                "source": "test",
                "domain": "invalid"
            },
            "should_pass": False
        },
        {
            "name": "Year too old",
            "metadata": {
                "title": "Test",
                "source": "test",
                "year": 1800
            },
            "should_pass": False
        },
        {
            "name": "Year too future",
            "metadata": {
                "title": "Test",
                "source": "test",
                "year": 2200
            },
            "should_pass": False
        },
        {
            "name": "Invalid URL",
            "metadata": {
                "title": "Test",
                "source": "test",
                "provenance_url": "not-a-url"
            },
            "should_pass": False
        },
        {
            "name": "Valid HTTP URL",
            "metadata": {
                "title": "Test",
                "source": "test",
                "provenance_url": "http://example.com/doc.html"
            },
            "should_pass": True
        },
        {
            "name": "Valid HTTPS URL",
            "metadata": {
                "title": "Test",
                "source": "test",
                "provenance_url": "https://example.com/doc.html"
            },
            "should_pass": True
        },
        {
            "name": "Chunk index equals total",
            "metadata": {
                "title": "Test",
                "source": "test",
                "chunk_index": 5,
                "chunk_total": 5
            },
            "should_pass": False
        },
        {
            "name": "Chunk index greater than total",
            "metadata": {
                "title": "Test",
                "source": "test",
                "chunk_index": 6,
                "chunk_total": 5
            },
            "should_pass": False
        },
        {
            "name": "Valid chunk indices",
            "metadata": {
                "title": "Test",
                "source": "test",
                "chunk_index": 0,
                "chunk_total": 5
            },
            "should_pass": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        is_valid, errors = validator.validate_metadata(test_case["metadata"])
        expected = test_case["should_pass"]
        
        if is_valid == expected:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        print(f"{status} {test_case['name']}: {'PASS' if is_valid == expected else 'FAIL'}")
        if is_valid != expected:
            print(f"    Expected: {expected}, Got: {is_valid}")
            if errors:
                print(f"    Errors: {errors}")
    
    print(f"\n✓ Passed: {passed}/{len(test_cases)}")
    print(f"✗ Failed: {failed}/{len(test_cases)}")
    return failed == 0

def test_document_validation_comprehensive():
    """Comprehensive document validation tests"""
    print_section("Comprehensive Document Validation")
    
    validator = SchemaValidator()
    
    test_cases = [
        {
            "name": "Valid document with text",
            "document": {
                "title": "Test Doc",
                "text": "This is test content."
            },
            "should_pass": True
        },
        {
            "name": "Valid document with content",
            "document": {
                "title": "Test Doc",
                "content": "This is test content."
            },
            "should_pass": True
        },
        {
            "name": "Document with both text and content",
            "document": {
                "title": "Test Doc",
                "text": "Text field",
                "content": "Content field"
            },
            "should_pass": True
        },
        {
            "name": "Document without text or content",
            "document": {
                "title": "Test Doc"
            },
            "should_pass": False
        },
        {
            "name": "Document with empty text",
            "document": {
                "title": "Test Doc",
                "text": "   "
            },
            "should_pass": False
        },
        {
            "name": "Document with non-string text",
            "document": {
                "title": "Test Doc",
                "text": 123
            },
            "should_pass": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        is_valid, errors = validator.validate_document(test_case["document"])
        expected = test_case["should_pass"]
        
        if is_valid == expected:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        print(f"{status} {test_case['name']}: {'PASS' if is_valid == expected else 'FAIL'}")
        if is_valid != expected:
            print(f"    Expected: {expected}, Got: {is_valid}")
            if errors:
                print(f"    Errors: {errors}")
    
    print(f"\n✓ Passed: {passed}/{len(test_cases)}")
    print(f"✗ Failed: {failed}/{len(test_cases)}")
    return failed == 0

def test_embedding_validation_comprehensive():
    """Comprehensive embedding validation tests"""
    print_section("Comprehensive Embedding Validation")
    
    validator = SchemaValidator()
    embedding_gen = TextEmbeddingGenerator()
    
    test_cases = [
        {
            "name": "Valid 768-dim text embedding",
            "embedding": embedding_gen.generate_embedding("Test text"),
            "embedding_type": EmbeddingType.TEXT,
            "should_pass": True
        },
        {
            "name": "Wrong dimension (384)",
            "embedding": [0.1] * 384,
            "embedding_type": EmbeddingType.TEXT,
            "should_pass": False
        },
        {
            "name": "Wrong dimension (1024)",
            "embedding": [0.1] * 1024,
            "embedding_type": EmbeddingType.TEXT,
            "should_pass": False
        },
        {
            "name": "Empty embedding",
            "embedding": [],
            "embedding_type": EmbeddingType.TEXT,
            "should_pass": False
        },
        {
            "name": "Non-list embedding",
            "embedding": "not-a-list",
            "embedding_type": EmbeddingType.TEXT,
            "should_pass": False
        },
        {
            "name": "Embedding with non-numeric values",
            "embedding": ["not", "numeric"] + [0.1] * 766,
            "embedding_type": EmbeddingType.TEXT,
            "should_pass": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        try:
            is_valid, errors = validator.validate_embedding(
                test_case["embedding"],
                test_case["embedding_type"]
            )
            expected = test_case["should_pass"]
            
            if is_valid == expected:
                passed += 1
                status = "✓"
            else:
                failed += 1
                status = "✗"
            
            print(f"{status} {test_case['name']}: {'PASS' if is_valid == expected else 'FAIL'}")
            if is_valid != expected:
                print(f"    Expected: {expected}, Got: {is_valid}")
                if errors:
                    print(f"    Errors: {errors}")
        except Exception as e:
            # For invalid inputs, exception is acceptable
            if not test_case["should_pass"]:
                passed += 1
                status = "✓"
                print(f"{status} {test_case['name']}: PASS (exception expected)")
            else:
                failed += 1
                status = "✗"
                print(f"{status} {test_case['name']}: FAIL (unexpected exception: {e})")
    
    print(f"\n✓ Passed: {passed}/{len(test_cases)}")
    print(f"✗ Failed: {failed}/{len(test_cases)}")
    return failed == 0

def test_chunking_validation_comprehensive():
    """Comprehensive chunking validation tests"""
    print_section("Comprehensive Chunking Validation")
    
    validator = SchemaValidator()
    
    test_cases = [
        {
            "name": "Valid standard chunking (512, 50)",
            "chunk_size": 512,
            "chunk_overlap": 50,
            "should_pass": True
        },
        {
            "name": "Valid minimum chunking (100, 10)",
            "chunk_size": 100,
            "chunk_overlap": 10,
            "should_pass": True
        },
        {
            "name": "Valid maximum chunking (2048, 200)",
            "chunk_size": 2048,
            "chunk_overlap": 200,
            "should_pass": True
        },
        {
            "name": "Chunk size too small",
            "chunk_size": 50,
            "chunk_overlap": 10,
            "should_pass": False
        },
        {
            "name": "Chunk size too large",
            "chunk_size": 3000,
            "chunk_overlap": 100,
            "should_pass": False
        },
        {
            "name": "Negative overlap",
            "chunk_size": 512,
            "chunk_overlap": -10,
            "should_pass": False
        },
        {
            "name": "Overlap equals size",
            "chunk_size": 512,
            "chunk_overlap": 512,
            "should_pass": False
        },
        {
            "name": "Overlap greater than size",
            "chunk_size": 512,
            "chunk_overlap": 600,
            "should_pass": False
        },
        {
            "name": "Zero overlap (valid)",
            "chunk_size": 512,
            "chunk_overlap": 0,
            "should_pass": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        is_valid, errors = validator.validate_chunking(
            test_case["chunk_size"],
            test_case["chunk_overlap"]
        )
        expected = test_case["should_pass"]
        
        if is_valid == expected:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        print(f"{status} {test_case['name']}: {'PASS' if is_valid == expected else 'FAIL'}")
        if is_valid != expected:
            print(f"    Expected: {expected}, Got: {is_valid}")
            if errors:
                print(f"    Errors: {errors}")
    
    print(f"\n✓ Passed: {passed}/{len(test_cases)}")
    print(f"✗ Failed: {failed}/{len(test_cases)}")
    return failed == 0

def test_filter_validation_comprehensive():
    """Comprehensive filter validation tests"""
    print_section("Comprehensive Filter Validation")
    
    validator = SchemaValidator()
    
    test_cases = [
        {
            "name": "Valid simple filter",
            "filters": {"domain": "pathology"},
            "should_pass": True
        },
        {
            "name": "Valid range filter",
            "filters": {"year": {"gte": 2020, "lte": 2023}},
            "should_pass": True
        },
        {
            "name": "Valid 'in' filter",
            "filters": {"domain": {"in": ["pathology", "pharmacology"]}},
            "should_pass": True
        },
        {
            "name": "Valid combined filters",
            "filters": {
                "domain": "pathology",
                "source": "demo",
                "year": {"gte": 2023}
            },
            "should_pass": True
        },
        {
            "name": "Invalid filter key",
            "filters": {"invalid_field": "value"},
            "should_pass": False
        },
        {
            "name": "Invalid 'in' filter (not a list)",
            "filters": {"domain": {"in": "not-a-list"}},
            "should_pass": False
        },
        {
            "name": "Valid ISO datetime string",
            "filters": {"created_at": {"gte": "2023-01-01T00:00:00Z"}},
            "should_pass": True
        },
        {
            "name": "Invalid range value (non-numeric string)",
            "filters": {"year": {"gte": "not-a-number"}},
            "should_pass": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        is_valid, errors = validator.validate_for_qdrant_query(test_case["filters"])
        expected = test_case["should_pass"]
        
        if is_valid == expected:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        print(f"{status} {test_case['name']}: {'PASS' if is_valid == expected else 'FAIL'}")
        if is_valid != expected:
            print(f"    Expected: {expected}, Got: {is_valid}")
            if errors:
                print(f"    Errors: {errors}")
    
    print(f"\n✓ Passed: {passed}/{len(test_cases)}")
    print(f"✗ Failed: {failed}/{len(test_cases)}")
    return failed == 0

def test_schema_integration():
    """Test complete schema integration with Qdrant"""
    print_section("Schema Integration with Qdrant")
    
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
        
        # Test 1: Validate all stored documents
        print("Test 1: Validate All Stored Documents")
        query_embedding = embedding_gen.generate_embedding("medical")
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=None,
            limit=20
        )
        
        print(f"  Retrieved {len(results)} documents for validation")
        
        all_valid = True
        validation_errors = []
        
        for result in results:
            payload = result.get("payload", {})
            is_valid, errors = validator.validate_metadata(payload)
            
            if not is_valid:
                all_valid = False
                validation_errors.append({
                    "title": payload.get("title", "Unknown"),
                    "errors": errors
                })
        
        if all_valid:
            print(f"  ✓ All {len(results)} documents have valid metadata")
        else:
            print(f"  ✗ {len(validation_errors)} documents have validation errors:")
            for error_info in validation_errors[:5]:  # Show first 5
                print(f"    - {error_info['title']}: {error_info['errors']}")
        print()
        
        # Test 2: Validate all embeddings
        print("Test 2: Validate All Embeddings")
        all_embeddings_valid = True
        
        for result in results:
            vector = result.get("vector")
            if vector:
                if isinstance(vector, list):
                    is_valid, errors = validator.validate_embedding(vector, EmbeddingType.TEXT)
                    if not is_valid:
                        all_embeddings_valid = False
                        print(f"  ✗ Invalid embedding in document: {result.get('payload', {}).get('title', 'Unknown')}")
                        print(f"    Errors: {errors}")
        
        if all_embeddings_valid:
            print(f"  ✓ All {len(results)} embeddings are valid (768 dimensions)")
        print()
        
        # Test 3: Test all filter types
        print("Test 3: Test All Filter Types")
        
        filter_tests = [
            ("Domain filter", {"domain": "pathology"}),
            ("Source filter", {"source": "demo"}),
            ("Year range filter", {"year": {"gte": 2023}}),
            ("Combined filters", {"domain": "pathology", "source": "demo"}),
            ("'In' filter", {"domain": {"in": ["pathology", "pharmacology"]}})
        ]
        
        for filter_name, filters in filter_tests:
            is_valid, errors = validator.validate_for_qdrant_query(filters)
            if is_valid:
                # Try actual query
                try:
                    query_results = storage.search_with_filters(
                        query_embedding=query_embedding,
                        filters=filters,
                        limit=5
                    )
                    print(f"  ✓ {filter_name}: Valid, found {len(query_results)} results")
                except Exception as e:
                    print(f"  ✗ {filter_name}: Valid but query failed: {e}")
            else:
                print(f"  ✗ {filter_name}: Invalid - {errors}")
        print()
        
        return all_valid and all_embeddings_valid
        
    except Exception as e:
        print(f"  ✗ Error connecting to Qdrant: {e}")
        return False

def main():
    """Run all comprehensive tests"""
    print("=" * 80)
    print("  Comprehensive Schema Validation Test Suite")
    print("=" * 80)
    
    results = []
    
    # Run all test suites
    results.append(("Metadata Validation", test_metadata_validation_comprehensive()))
    results.append(("Document Validation", test_document_validation_comprehensive()))
    results.append(("Embedding Validation", test_embedding_validation_comprehensive()))
    results.append(("Chunking Validation", test_chunking_validation_comprehensive()))
    results.append(("Filter Validation", test_filter_validation_comprehensive()))
    results.append(("Schema Integration", test_schema_integration()))
    
    # Summary
    print("=" * 80)
    print("  Test Summary")
    print("=" * 80)
    print()
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("=" * 80)
        print("  ✓ ALL TESTS PASSED!")
        print("=" * 80)
    else:
        print("=" * 80)
        print("  ✗ SOME TESTS FAILED")
        print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

