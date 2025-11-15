#!/usr/bin/env python3
"""
Detailed Test for Knowledge Collector

Tests the full pipeline: crawling, parsing, storing, and Qdrant integration.
"""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.collector import (
    WebCrawler,
    CrawlerConfig,
    RobotsParser,
    DocumentParser,
    ParsedDocument,
    KnowledgeCollector,
    MedicalSource,
    SOURCE_CONFIGS
)
from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings.text_embeddings import TextEmbeddingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_robots_parser_detailed():
    """Test robots parser in detail"""
    print_section("Test 1: Robots Parser - Detailed")
    
    parser = RobotsParser(user_agent="HygiaAI-Collector/1.0")
    
    # Test multiple domains
    test_urls = [
        "https://www.ncbi.nlm.nih.gov/books",
        "https://medlineplus.gov",
        "https://www.who.int/elena",
        "https://www.cdc.gov"
    ]
    
    for url in test_urls:
        can_fetch = parser.can_fetch(url)
        delay = parser.get_crawl_delay(url)
        print(f"✓ {url}")
        print(f"  Allowed: {can_fetch}")
        print(f"  Crawl delay: {delay}s")
    
    print()


def test_document_parser_detailed():
    """Test document parser with various formats"""
    print_section("Test 2: Document Parser - Detailed")
    
    parser = DocumentParser()
    
    # Test HTML with various metadata
    html_tests = [
        {
            "html": """
            <html>
            <head>
                <title>Pathology Textbook 2023</title>
                <meta name="author" content="Dr. Jane Smith, Dr. John Doe">
                <meta name="date" content="2023-01-15">
            </head>
            <body>
                <h1>Introduction to Pathology</h1>
                <p>This comprehensive textbook covers disease diagnosis and pathology.</p>
            </body>
            </html>
            """,
            "url": "https://example.com/pathology.html"
        },
        {
            "html": """
            <html>
            <head>
                <title>Pharmacology Guide</title>
                <meta property="og:title" content="Clinical Pharmacology">
            </head>
            <body>
                <h1>Drug Dosage Guidelines</h1>
                <p>Published in 2022, this guide covers medication protocols.</p>
            </body>
            </html>
            """,
            "url": "https://example.com/pharmacology.html"
        }
    ]
    
    for i, test in enumerate(html_tests, 1):
        parsed = parser.parse_html(test["html"], test["url"])
        print(f"✓ Test HTML {i}:")
        print(f"  Title: {parsed.title}")
        print(f"  Author: {parsed.author}")
        print(f"  Year: {parsed.year}")
        print(f"  Content length: {len(parsed.content)} chars")
        print(f"  Domain: {parsed.domain}")
        print()
    
    # Test year extraction
    print("✓ Year extraction tests:")
    year_tests = [
        ("Published in 2023", 2023),
        ("Copyright 2020-2024", 2024),  # Should get most recent
        ("No year here", None)
    ]
    
    for text, expected in year_tests:
        year = parser._extract_year(text, None)
        status = "✓" if (year == expected or (expected is None and year is None)) else "✗"
        print(f"  {status} '{text}' -> {year} (expected: {expected})")
    print()


def test_web_crawler_detailed():
    """Test web crawler with real URLs"""
    print_section("Test 3: Web Crawler - Detailed")
    
    config = CrawlerConfig(
        max_pages=10,  # Limited for testing
        crawl_delay=2.0,
        respect_robots=True,
        timeout=30
    )
    
    crawler = WebCrawler(config=config)
    
    # Test URLs from different sources
    test_urls = [
        "https://medlineplus.gov/aboutmedlineplus.html",
        "https://medlineplus.gov/healthtopics.html"
    ]
    
    print(f"Testing crawl with {len(test_urls)} URLs...")
    print("(This may take a moment due to crawl delays)\n")
    
    results = []
    for url in test_urls:
        try:
            result = crawler.crawl_url(url)
            results.append(result)
            
            if result.success:
                print(f"✓ Successfully crawled: {url}")
                print(f"  Title: {result.parsed_document.title[:80]}...")
                print(f"  File type: {result.parsed_document.file_type}")
                print(f"  Content length: {len(result.parsed_document.content)} chars")
                if result.parsed_document.author:
                    print(f"  Author: {result.parsed_document.author}")
                if result.parsed_document.year:
                    print(f"  Year: {result.parsed_document.year}")
            else:
                print(f"✗ Failed to crawl: {url}")
                print(f"  Error: {result.error}")
                if result.status_code:
                    print(f"  Status code: {result.status_code}")
        except Exception as e:
            print(f"✗ Exception crawling {url}: {e}")
        print()
    
    successful = [r for r in results if r.success]
    print(f"Summary: {len(successful)}/{len(results)} successful")
    print()


def test_knowledge_collector_with_storage():
    """Test knowledge collector with file storage"""
    print_section("Test 4: Knowledge Collector - Storage")
    
    collector = KnowledgeCollector(
        storage_directory="data/demo_collected",
        ingestion_pipeline=None  # Test storage only
    )
    
    print(f"✓ Collector initialized")
    print(f"  Storage directory: {collector.storage_directory}")
    
    # Create a sample parsed document
    from src.collector import ParsedDocument
    sample_doc = ParsedDocument(
        url="https://example.com/sample.html",
        title="Sample Medical Document",
        content="This is a sample medical document for testing. It contains information about disease diagnosis and treatment protocols.",
        source="example.com",
        domain="example.com",
        author="Dr. Test Author",
        year=2023,
        file_type="html"
    )
    
    # Save parsed document
    saved_path = collector._save_parsed_document(sample_doc)
    print(f"✓ Saved parsed document: {saved_path}")
    print(f"  File exists: {saved_path.exists()}")
    
    # Test domain inference
    domains = [
        ("Pathology Textbook", "This book covers disease diagnosis and pathology", "pathology"),
        ("Pharmacology Guide", "Drug dosage and medication information", "pharmacology"),
        ("Surgical Procedures", "Surgery and surgical techniques", "surgery"),
        ("General Medical Text", "General medical information", None)
    ]
    
    print("\n✓ Domain inference tests:")
    for title, content, expected_domain in domains:
        doc = ParsedDocument(
            url=f"https://example.com/{title.lower().replace(' ', '_')}.html",
            title=title,
            content=content,
            source="example.com",
            domain="example.com"
        )
        inferred = collector._infer_domain(doc)
        status = "✓" if inferred == expected_domain else "✗"
        print(f"  {status} '{title}' -> {inferred} (expected: {expected_domain})")
    print()


def test_qdrant_integration():
    """Test integration with Qdrant"""
    print_section("Test 5: Qdrant Integration")
    
    try:
        # Initialize Qdrant storage
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print("✓ Qdrant storage initialized")
        
        # Initialize embedding generator
        embedding_gen = TextEmbeddingGenerator()
        print("✓ Text embedding generator initialized")
        
        # Create ingestion pipeline
        ingestion_pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=storage,
            text_embedding_generator=embedding_gen.generate_embedding,
            chunk_size=512,
            chunk_overlap=50
        )
        print("✓ Knowledge ingestion pipeline initialized")
        
        # Create collector with pipeline
        collector = KnowledgeCollector(
            storage_directory="data/demo_collected",
            ingestion_pipeline=ingestion_pipeline
        )
        print("✓ Knowledge collector with Qdrant integration ready")
        
        # Create sample documents for ingestion
        sample_documents = [
            {
                "url": "https://example.com/pathology_intro.html",
                "title": "Introduction to Pathology",
                "content": """
                Pathology is the study of disease. It involves the examination of tissues, organs, 
                and bodily fluids to diagnose diseases. Pathologists use various techniques including 
                microscopy, molecular biology, and immunohistochemistry to identify abnormalities.
                
                Common pathological conditions include inflammation, infection, neoplasia, and 
                degenerative diseases. Understanding pathology is essential for accurate diagnosis 
                and effective treatment planning.
                """,
                "source": "example.com",
                "author": "Dr. Medical Author",
                "year": 2023,
                "file_type": "html",
                "provenance_url": "https://example.com/pathology_intro.html"
            },
            {
                "url": "https://example.com/pharmacology_basics.html",
                "title": "Pharmacology Basics",
                "content": """
                Pharmacology is the study of how drugs interact with biological systems. It covers 
                drug absorption, distribution, metabolism, and excretion (ADME). Understanding 
                pharmacokinetics and pharmacodynamics is crucial for safe and effective medication use.
                
                Drug interactions can occur at various levels including pharmacokinetic and 
                pharmacodynamic interactions. Healthcare providers must be aware of potential 
                interactions when prescribing multiple medications.
                """,
                "source": "example.com",
                "author": "Dr. Pharmacy Expert",
                "year": 2023,
                "file_type": "html",
                "provenance_url": "https://example.com/pharmacology_basics.html"
            },
            {
                "url": "https://example.com/clinical_guidelines.html",
                "title": "Clinical Practice Guidelines",
                "content": """
                Clinical practice guidelines are systematically developed statements to assist 
                practitioner and patient decisions about appropriate healthcare. They are based on 
                the best available evidence and expert consensus.
                
                Guidelines help standardize care, improve patient outcomes, and reduce variations 
                in practice. They should be regularly updated as new evidence emerges.
                """,
                "source": "example.com",
                "author": "Clinical Guidelines Committee",
                "year": 2023,
                "file_type": "html",
                "provenance_url": "https://example.com/clinical_guidelines.html"
            }
        ]
        
        print(f"\n✓ Ingesting {len(sample_documents)} sample documents into Qdrant...")
        
        ingested_count = 0
        for doc_data in sample_documents:
            try:
                from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
                
                metadata = KnowledgeBaseMetadata(
                    title=doc_data["title"],
                    source="demo",
                    domain=collector._infer_domain(
                        ParsedDocument(
                            url=doc_data["url"],
                            title=doc_data["title"],
                            content=doc_data["content"],
                            source=doc_data["source"],
                            domain=doc_data["source"]
                        )
                    ),
                    year=doc_data["year"],
                    embedding_type=EmbeddingType.TEXT,
                    access_type=AccessType.OPEN,
                    provenance_url=doc_data["provenance_url"],
                    author=doc_data["author"]
                )
                
                point_ids = ingestion_pipeline.ingest_document(
                    doc_data,
                    metadata=metadata
                )
                
                if point_ids:
                    ingested_count += 1
                    print(f"  ✓ Ingested: {doc_data['title']} ({len(point_ids)} chunks)")
            except Exception as e:
                print(f"  ✗ Error ingesting {doc_data['title']}: {e}")
        
        print(f"\n✓ Successfully ingested {ingested_count}/{len(sample_documents)} documents")
        
        # Verify storage
        collection_info = storage.get_collection_info()
        if collection_info:
            points_count = collection_info.get("points_count", 0)
            print(f"✓ Collection now has {points_count} points")
        
    except Exception as e:
        print(f"✗ Qdrant integration test failed: {e}")
        print("  (This is expected if Qdrant is not running)")
    print()


def main():
    """Run all detailed tests"""
    print("=" * 80)
    print("  Knowledge Collector - Detailed Testing")
    print("=" * 80)
    
    try:
        test_robots_parser_detailed()
        test_document_parser_detailed()
        test_web_crawler_detailed()
        test_knowledge_collector_with_storage()
        test_qdrant_integration()
        
        print("=" * 80)
        print("  All Detailed Tests Complete!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

