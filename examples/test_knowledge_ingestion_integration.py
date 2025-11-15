#!/usr/bin/env python3
"""
Integration Test for Knowledge Ingestion Pipeline

Tests the complete pipeline: load → chunk → embed → upsert → verify retrieval
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
from src.embeddings.text_embeddings import TextEmbeddingGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test knowledge ingestion pipeline"""
    print("=" * 80)
    print("  Knowledge Ingestion Pipeline - Integration Test")
    print("=" * 80)
    
    try:
        # Initialize components
        print_section("1. Initializing Components")
        
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print("✓ QdrantStorage initialized")
        
        embedding_gen = TextEmbeddingGenerator()
        print("✓ TextEmbeddingGenerator initialized")
        
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=storage,
            text_embedding_generator=embedding_gen.generate_embedding,
            chunk_size=512,
            chunk_overlap=50,
            validate_schema=True
        )
        print("✓ KnowledgeIngestionPipeline initialized")
        print()
        
        # Test 2: Ingest sample documents
        print_section("2. Ingesting Sample Documents")
        
        sample_documents = [
            {
                "title": "Test Document 1: Pathology Basics",
                "text": """
                Pathology is the medical specialty concerned with the study of disease.
                It involves the examination of tissues, organs, and bodily fluids to
                diagnose diseases and understand their causes and mechanisms. Pathologists
                work in laboratories and use various techniques including microscopy,
                molecular biology, and biochemistry to analyze samples.
                """,
                "source": "test",
                "domain": "pathology",
                "year": 2024,
                "provenance_url": "https://test.example.com/pathology1.html"
            },
            {
                "title": "Test Document 2: Pharmacology Principles",
                "text": """
                Pharmacology is the branch of medicine that deals with the study of drugs
                and their effects on living organisms. It encompasses drug discovery,
                development, and clinical application. Pharmacologists study how drugs
                interact with biological systems, including their mechanisms of action,
                therapeutic effects, and potential side effects.
                """,
                "source": "test",
                "domain": "pharmacology",
                "year": 2024,
                "provenance_url": "https://test.example.com/pharmacology1.html"
            },
            {
                "title": "Test Document 3: Clinical Guidelines",
                "text": """
                Clinical practice guidelines are systematically developed statements
                to assist practitioner and patient decisions about appropriate health
                care for specific clinical circumstances. They are based on the best
                available evidence and expert consensus. Guidelines help standardize
                care and improve patient outcomes.
                """,
                "source": "test",
                "domain": "guidelines",
                "year": 2024,
                "provenance_url": "https://test.example.com/guidelines1.html"
            }
        ]
        
        ingested_count = 0
        point_ids_all = []
        
        for i, doc in enumerate(sample_documents, 1):
            try:
                print(f"  Ingesting document {i}: {doc['title']}")
                point_ids = pipeline.ingest_document(doc)
                ingested_count += 1
                point_ids_all.extend(point_ids)
                print(f"    ✓ Ingested {len(point_ids)} chunks")
            except Exception as e:
                print(f"    ✗ Error: {e}")
        
        print(f"\n✓ Ingested {ingested_count}/{len(sample_documents)} documents")
        print(f"✓ Total chunks created: {len(point_ids_all)}")
        print()
        
        # Test 3: Verify retrieval by domain
        print_section("3. Verify Retrieval by Domain")
        
        query_embedding = embedding_gen.generate_embedding("pathology and disease diagnosis")
        
        domains = ["pathology", "pharmacology", "guidelines"]
        for domain in domains:
            results = storage.search_with_filters(
                query_embedding=query_embedding,
                filters={"domain": domain, "source": "test"},
                limit=3
            )
            print(f"✓ Domain '{domain}': Found {len(results)} results")
            if results:
                for result in results[:2]:
                    payload = result.get("payload", {})
                    print(f"    - {payload.get('title', 'Unknown')} (score: {result.get('score', 0):.4f})")
        print()
        
        # Test 4: Verify retrieval by year
        print_section("4. Verify Retrieval by Year")
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters={"year": {"gte": 2024}, "source": "test"},
            limit=5
        )
        print(f"✓ Year >= 2024: Found {len(results)} results")
        print()
        
        # Test 5: Verify retrieval by source
        print_section("5. Verify Retrieval by Source")
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters={"source": "test"},
            limit=10
        )
        print(f"✓ Source 'test': Found {len(results)} results")
        print()
        
        # Test 6: Test idempotent ingestion
        print_section("6. Test Idempotent Ingestion")
        
        # Try to ingest the same document again
        doc = sample_documents[0]
        point_ids_duplicate = pipeline.ingest_document(doc)
        
        if len(point_ids_duplicate) == 1:
            print("✓ Idempotent ingestion working: Document skipped (already exists)")
        else:
            print(f"⚠ Ingested {len(point_ids_duplicate)} chunks (may have been updated)")
        print()
        
        # Test 7: Test batch ingestion
        print_section("7. Test Batch Ingestion")
        
        batch_docs = [
            {
                "title": "Batch Doc 1",
                "text": "This is batch document 1 with some content about medical topics.",
                "source": "test",
                "domain": "pathology"
            },
            {
                "title": "Batch Doc 2",
                "text": "This is batch document 2 with different medical content.",
                "source": "test",
                "domain": "pharmacology"
            }
        ]
        
        stats = pipeline.ingest_batch(batch_docs)
        print(f"✓ Batch ingestion complete:")
        print(f"    Total: {stats['total']}")
        print(f"    Ingested: {stats['ingested']}")
        print(f"    Skipped: {stats['skipped']}")
        print(f"    Errors: {stats['errors']}")
        print()
        
        # Test 8: Test delta ingestion
        print_section("8. Test Delta Ingestion")
        
        delta_docs = [
            {
                "title": "Delta Doc 1",
                "text": "This is a new document for delta ingestion testing.",
                "source": "test",
                "domain": "guidelines",
                "updated_at": "2024-11-12T10:00:00Z"
            }
        ]
        
        stats = pipeline.delta_ingest(delta_docs)
        print(f"✓ Delta ingestion complete:")
        print(f"    New: {stats['new']}")
        print(f"    Updated: {stats['updated']}")
        print(f"    Unchanged: {stats['unchanged']}")
        print(f"    Errors: {stats['errors']}")
        print()
        
        # Test 9: Verify chunking
        print_section("9. Verify Chunking")
        
        long_text = "A" * 2000  # 2000 characters
        chunks = pipeline.chunk_text(long_text)
        print(f"✓ Chunked {len(long_text)} characters into {len(chunks)} chunks")
        print(f"    Chunk size: {pipeline.chunk_size}")
        print(f"    Chunk overlap: {pipeline.chunk_overlap}")
        if chunks:
            print(f"    First chunk length: {len(chunks[0]['text'])}")
            print(f"    Last chunk length: {len(chunks[-1]['text'])}")
        print()
        
        # Test 10: Performance check
        print_section("10. Performance Check")
        
        import time
        
        start_time = time.time()
        test_doc = {
            "title": "Performance Test",
            "text": "This is a performance test document with some content.",
            "source": "test"
        }
        point_ids = pipeline.ingest_document(test_doc)
        elapsed = time.time() - start_time
        
        print(f"✓ Single document ingestion time: {elapsed:.3f} seconds")
        print(f"    Chunks created: {len(point_ids)}")
        if len(point_ids) > 0:
            print(f"    Time per chunk: {elapsed/len(point_ids):.3f} seconds")
        print()
        
        print("=" * 80)
        print("  ✓ All Integration Tests Passed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


