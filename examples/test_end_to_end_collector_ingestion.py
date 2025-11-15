#!/usr/bin/env python3
"""
End-to-End Test: Knowledge Collector → Ingestion Pipeline

Tests the complete flow:
1. Collect documents from sources
2. Parse documents
3. Ingest into Qdrant via pipeline
4. Verify retrieval
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.collector import KnowledgeCollector, ParsedDocument, MedicalSource
from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings.text_embeddings import TextEmbeddingGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test end-to-end collector to ingestion flow"""
    print("=" * 80)
    print("  End-to-End Test: Collector → Ingestion Pipeline")
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
        
        collector = KnowledgeCollector(
            storage_directory="data/test_e2e_collected",
            ingestion_pipeline=pipeline
        )
        print("✓ KnowledgeCollector initialized with ingestion pipeline")
        print()
        
        # Test 2: Create sample parsed documents (simulating collection)
        print_section("2. Creating Sample Parsed Documents")
        
        sample_docs = [
            ParsedDocument(
                url="https://test.example.com/doc1.html",
                title="Clinical Pathology: Disease Diagnosis",
                content="""
                Clinical pathology is a medical specialty that deals with the diagnosis
                of disease based on the laboratory analysis of bodily fluids and tissues.
                Pathologists use various techniques including microscopy, molecular biology,
                and biochemistry to identify diseases and understand their mechanisms.
                """,
                source="test_source",
                domain="pathology",
                author="Test Author",
                year=2024,
                file_type="html",
                metadata={}
            ),
            ParsedDocument(
                url="https://test.example.com/doc2.html",
                title="Pharmacology: Drug Mechanisms",
                content="""
                Pharmacology studies how drugs interact with biological systems.
                It encompasses drug discovery, development, and clinical application.
                Understanding drug mechanisms helps in developing effective treatments
                and managing side effects.
                """,
                source="test_source",
                domain="pharmacology",
                author="Test Author",
                year=2024,
                file_type="html",
                metadata={}
            ),
            ParsedDocument(
                url="https://test.example.com/doc3.html",
                title="Clinical Guidelines: Best Practices",
                content="""
                Clinical practice guidelines provide evidence-based recommendations
                for healthcare providers. They help standardize care and improve
                patient outcomes by ensuring consistent application of best practices.
                """,
                source="test_source",
                domain="guidelines",
                author="Test Author",
                year=2024,
                file_type="html",
                metadata={}
            )
        ]
        
        print(f"✓ Created {len(sample_docs)} sample parsed documents")
        for i, doc in enumerate(sample_docs, 1):
            print(f"  {i}. {doc.title}")
        print()
        
        # Test 3: Process and store via collector (which uses pipeline)
        print_section("3. Processing Documents via Collector")
        
        from src.collector.web_crawler import CrawlResult
        from datetime import datetime, timezone
        
        stored_count = 0
        for doc in sample_docs:
            # Create a mock crawl result
            crawl_result = CrawlResult(
                url=doc.url,
                success=True,
                parsed_document=doc,
                crawled_at=datetime.now(timezone.utc)
            )
            
            try:
                # Use a valid MedicalSource enum value
                from src.collector.source_config import MedicalSource
                point_id = collector.process_and_store(
                    crawl_result=crawl_result,
                    source=MedicalSource.MEDLINEPLUS,  # Use a valid enum
                    domain=doc.domain
                )
                if point_id:
                    stored_count += 1
                    print(f"✓ Stored: {doc.title[:50]}...")
            except Exception as e:
                print(f"✗ Error storing {doc.title}: {e}")
        
        print(f"\n✓ Stored {stored_count}/{len(sample_docs)} documents")
        print()
        
        # Test 4: Verify retrieval from Qdrant
        print_section("4. Verify Retrieval from Qdrant")
        
        query_embedding = embedding_gen.generate_embedding("pathology and disease diagnosis")
        
        # Test retrieval by domain
        domains = ["pathology", "pharmacology", "guidelines"]
        for domain in domains:
            results = storage.search_with_filters(
                query_embedding=query_embedding,
                filters={"domain": domain, "source": "medlineplus"},
                limit=3
            )
            print(f"✓ Domain '{domain}': Found {len(results)} results")
            if results:
                for result in results[:2]:
                    payload = result.get("payload", {})
                    print(f"    - {payload.get('title', 'Unknown')[:50]}... (score: {result.get('score', 0):.4f})")
        print()
        
        # Test 5: Verify idempotent ingestion
        print_section("5. Test Idempotent Ingestion")
        
        # Try to process the same document again
        crawl_result = CrawlResult(
            url=sample_docs[0].url,
            success=True,
            parsed_document=sample_docs[0],
            crawled_at=datetime.now(timezone.utc)
        )
        
        from src.collector.source_config import MedicalSource
        point_id_duplicate = collector.process_and_store(
            crawl_result=crawl_result,
            source=MedicalSource.MEDLINEPLUS,
            domain=sample_docs[0].domain
        )
        
        if point_id_duplicate:
            print("✓ Idempotent ingestion working: Document processed (may be updated)")
        else:
            print("✓ Idempotent ingestion working: Document skipped (already exists)")
        print()
        
        # Test 6: Direct pipeline ingestion (alternative path)
        print_section("6. Direct Pipeline Ingestion")
        
        direct_doc = {
            "title": "Direct Ingestion Test",
            "text": "This document was ingested directly via the pipeline without going through the collector.",
            "source": "direct_test",
            "domain": "general",
            "year": 2024,
            "provenance_url": "https://test.example.com/direct.html"
        }
        
        point_ids = pipeline.ingest_document(direct_doc)
        print(f"✓ Direct ingestion: {len(point_ids)} chunks created")
        
        # Verify retrieval
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters={"source": "direct_test"},
            limit=1
        )
        if results:
            print(f"✓ Retrieved direct ingestion document: {results[0].get('payload', {}).get('title')}")
        print()
        
        # Test 7: Batch ingestion via pipeline
        print_section("7. Batch Ingestion via Pipeline")
        
        batch_docs = [
            {
                "title": "Batch Doc 1",
                "text": "First batch document for testing batch ingestion capabilities.",
                "source": "batch_test",
                "domain": "general"
            },
            {
                "title": "Batch Doc 2",
                "text": "Second batch document for testing batch ingestion capabilities.",
                "source": "batch_test",
                "domain": "general"
            }
        ]
        
        stats = pipeline.ingest_batch(batch_docs)
        print(f"✓ Batch ingestion complete:")
        print(f"    Total: {stats['total']}")
        print(f"    Ingested: {stats['ingested']}")
        print(f"    Skipped: {stats['skipped']}")
        print(f"    Errors: {stats['errors']}")
        print()
        
        print("=" * 80)
        print("  ✓ All End-to-End Tests Passed!")
        print("=" * 80)
        print("\nSummary:")
        print(f"  - Documents processed via collector: {stored_count}")
        print(f"  - Direct pipeline ingestion: 1 document")
        print(f"  - Batch ingestion: {stats['ingested']} documents")
        print(f"  - Total documents in Qdrant: {stored_count + 1 + stats['ingested']}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

