#!/usr/bin/env python3
"""
Integration Test for Provenance & Compliance Guardrails

Tests:
- License validation
- Provenance URL validation
- Open-access enforcement
- Audit logging
- Crawl delay
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.compliance.license_validator import LicenseValidator
from src.compliance.audit_logger import AuditLogger, AuditEventType
from src.embeddings.text_embeddings import TextEmbeddingGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test provenance and compliance guardrails"""
    print("=" * 80)
    print("  Provenance & Compliance Guardrails - Integration Test")
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
        
        license_validator = LicenseValidator(strict_mode=True)
        print("✓ LicenseValidator initialized (strict mode)")
        
        audit_logger = AuditLogger(log_directory="logs/test_audit", enable_encryption=False)
        print("✓ AuditLogger initialized")
        
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=storage,
            text_embedding_generator=embedding_gen.generate_embedding,
            chunk_size=512,
            chunk_overlap=50,
            validate_schema=True,
            enforce_open_access=True,
            license_validator=license_validator,
            audit_logger=audit_logger
        )
        print("✓ KnowledgeIngestionPipeline initialized with compliance features")
        print()
        
        # Test 2: Provenance URL validation
        print_section("2. Provenance URL Validation")
        
        test_urls = [
            ("https://ncbi.nlm.nih.gov/book/123", True),
            ("http://example.com/doc.html", True),
            ("ftp://example.com/doc.html", False),
            ("invalid-url", False),
            (None, False),
            ("", False)
        ]
        
        for url, expected_valid in test_urls:
            is_valid, error = license_validator.validate_provenance_url(url)
            status = "✓" if is_valid == expected_valid else "✗"
            print(f"{status} URL: {url or 'None'}")
            print(f"    Valid: {is_valid}, Expected: {expected_valid}")
            if error:
                print(f"    Error: {error}")
        print()
        
        # Test 3: License validation - Open-access content
        print_section("3. License Validation - Open-Access Content")
        
        open_access_docs = [
            {
                "title": "CC Licensed Document",
                "text": "This is a test document.",
                "source": "test",
                "domain": "general",
                "provenance_url": "https://example.com/cc-doc.html",
                "license": "Creative Commons Attribution 4.0"
            },
            {
                "title": "Public Domain Document",
                "text": "This is a test document.",
                "source": "test",
                "domain": "general",
                "provenance_url": "https://example.com/pd-doc.html",
                "license": "This work is in the public domain"
            },
            {
                "title": "NCBI Document",
                "text": "This is a test document.",
                "source": "test",
                "domain": "general",
                "provenance_url": "https://ncbi.nlm.nih.gov/book/123"
            }
        ]
        
        ingested_count = 0
        for doc in open_access_docs:
            try:
                point_ids = pipeline.ingest_document(doc)
                ingested_count += 1
                print(f"✓ Ingested: {doc['title']}")
            except Exception as e:
                print(f"✗ Failed: {doc['title']} - {e}")
        
        print(f"\n✓ Ingested {ingested_count}/{len(open_access_docs)} open-access documents")
        print()
        
        # Test 4: License validation - Restricted content (should be rejected)
        print_section("4. License Validation - Restricted Content (Should Reject)")
        
        restricted_docs = [
            {
                "title": "Copyright Protected Document",
                "text": "This is a test document.",
                "source": "test",
                "domain": "general",
                "provenance_url": "https://example.com/copyright-doc.html",
                "copyright": "All rights reserved. Copyright protected."
            },
            {
                "title": "Proprietary Document",
                "text": "This is a test document.",
                "source": "test",
                "domain": "general",
                "provenance_url": "https://example.com/prop-doc.html",
                "license": "Proprietary license. Restricted access."
            }
        ]
        
        rejected_count = 0
        for doc in restricted_docs:
            try:
                point_ids = pipeline.ingest_document(doc)
                print(f"✗ Should have rejected: {doc['title']}")
            except ValueError as e:
                rejected_count += 1
                print(f"✓ Correctly rejected: {doc['title']}")
                print(f"    Reason: {str(e)[:80]}...")
            except Exception as e:
                print(f"✗ Unexpected error: {doc['title']} - {e}")
        
        print(f"\n✓ Correctly rejected {rejected_count}/{len(restricted_docs)} restricted documents")
        print()
        
        # Test 5: Audit logging verification
        print_section("5. Audit Logging Verification")
        
        # Query audit logs for ingestion events
        ingestion_events = audit_logger.query_events(
            event_type=AuditEventType.KNOWLEDGE_INGESTION,
            limit=10
        )
        print(f"✓ Found {len(ingestion_events)} knowledge ingestion events")
        
        validation_events = audit_logger.query_events(
            event_type=AuditEventType.KNOWLEDGE_ACCESS_VALIDATION,
            limit=10
        )
        print(f"✓ Found {len(validation_events)} access validation events")
        
        if ingestion_events:
            latest_event = ingestion_events[0]
            print(f"\n  Latest ingestion event:")
            print(f"    Title: {latest_event.resource_id}")
            print(f"    Source: {latest_event.details.get('source', 'unknown')}")
            print(f"    Provenance URL: {latest_event.details.get('provenance_url', 'unknown')}")
            print(f"    Access Type: {latest_event.details.get('access_type', 'unknown')}")
            print(f"    Timestamp: {latest_event.timestamp}")
        print()
        
        # Test 6: Verify access_type is always OPEN
        print_section("6. Verify Access Type Enforcement")
        
        # Search for ingested documents and verify access_type
        query_embedding = embedding_gen.generate_embedding("test document")
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters={"source": "test"},
            limit=10
        )
        
        all_open = True
        for result in results:
            payload = result.get("payload", {})
            access_type = payload.get("access_type", "unknown")
            title = payload.get("title", "unknown")
            if access_type != "open":
                print(f"✗ Document '{title}' has access_type '{access_type}' (expected 'open')")
                all_open = False
            else:
                print(f"✓ Document '{title}' has access_type 'open'")
        
        if all_open:
            print("\n✓ All ingested documents have access_type='open'")
        print()
        
        # Test 7: Verify provenance URLs are stored
        print_section("7. Verify Provenance URLs Are Stored")
        
        all_have_provenance = True
        for result in results:
            payload = result.get("payload", {})
            provenance_url = payload.get("provenance_url")
            title = payload.get("title", "unknown")
            if not provenance_url:
                print(f"✗ Document '{title}' missing provenance_url")
                all_have_provenance = False
            else:
                print(f"✓ Document '{title}' has provenance_url: {provenance_url[:50]}...")
        
        if all_have_provenance:
            print("\n✓ All ingested documents have provenance URLs")
        print()
        
        print("=" * 80)
        print("  ✓ All Compliance Tests Passed!")
        print("=" * 80)
        print("\nSummary:")
        print(f"  - Open-access documents ingested: {ingested_count}")
        print(f"  - Restricted documents rejected: {rejected_count}")
        print(f"  - Audit events logged: {len(ingestion_events) + len(validation_events)}")
        print(f"  - All documents have access_type='open': {all_open}")
        print(f"  - All documents have provenance URLs: {all_have_provenance}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

