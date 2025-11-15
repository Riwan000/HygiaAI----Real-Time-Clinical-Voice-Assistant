#!/usr/bin/env python3
"""
Test Knowledge Collector

Tests the open-access medical knowledge collector with a small sample.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.collector import (
    WebCrawler,
    CrawlerConfig,
    RobotsParser,
    DocumentParser,
    KnowledgeCollector,
    MedicalSource,
    SOURCE_CONFIGS
)
from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings.text_embeddings import TextEmbeddingGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test knowledge collector"""
    print("=" * 80)
    print("  Knowledge Collector Test")
    print("=" * 80)
    
    # Test 1: Robots Parser
    print_section("Test 1: Robots.txt Parser")
    robots_parser = RobotsParser(user_agent="HygiaAI-Collector/1.0")
    
    # Test URL (using a well-known site)
    test_url = "https://www.ncbi.nlm.nih.gov/books"
    can_fetch = robots_parser.can_fetch(test_url)
    print(f"✓ Can fetch {test_url}: {can_fetch}")
    
    crawl_delay = robots_parser.get_crawl_delay(test_url)
    print(f"✓ Crawl delay: {crawl_delay}s")
    
    # Test 2: Document Parser
    print_section("Test 2: Document Parser")
    doc_parser = DocumentParser()
    
    # Test HTML parsing
    test_html = """
    <html>
    <head>
        <title>Medical Textbook: Introduction to Pathology</title>
        <meta name="author" content="Dr. John Smith">
    </head>
    <body>
        <h1>Introduction to Pathology</h1>
        <p>This textbook covers the fundamentals of pathology, published in 2023.</p>
    </body>
    </html>
    """
    
    parsed = doc_parser.parse_html(test_html, "https://example.com/book.html")
    print(f"✓ Parsed HTML document:")
    print(f"  Title: {parsed.title}")
    print(f"  Author: {parsed.author}")
    print(f"  Year: {parsed.year}")
    print(f"  Content length: {len(parsed.content)} chars")
    
    # Test 3: Source Configuration
    print_section("Test 3: Source Configuration")
    source_config = SOURCE_CONFIGS[MedicalSource.NCBI_BOOKSHELF]
    print(f"✓ Source config for {source_config.source.value}:")
    print(f"  Base URL: {source_config.base_url}")
    print(f"  Allowed domains: {source_config.allowed_domains}")
    print(f"  Allowed file types: {source_config.allowed_file_types}")
    print(f"  Max pages: {source_config.max_pages}")
    
    # Test 4: Web Crawler (Limited Test)
    print_section("Test 4: Web Crawler (Limited Test)")
    crawler_config = CrawlerConfig(
        max_pages=5,  # Very limited for testing
        crawl_delay=2.0,
        respect_robots=True
    )
    
    crawler = WebCrawler(config=crawler_config)
    
    # Test with a simple, accessible URL (MedlinePlus is usually accessible)
    test_urls = [
        "https://medlineplus.gov/aboutmedlineplus.html"  # Simple about page
    ]
    
    print(f"Testing crawl with {len(test_urls)} test URLs...")
    print("(This may take a moment due to crawl delays)")
    
    for url in test_urls:
        try:
            result = crawler.crawl_url(url)
            if result.success:
                print(f"✓ Successfully crawled: {url}")
                print(f"  Title: {result.parsed_document.title[:60]}...")
                print(f"  File type: {result.parsed_document.file_type}")
            else:
                print(f"✗ Failed to crawl: {url}")
                print(f"  Error: {result.error}")
        except Exception as e:
            print(f"✗ Error crawling {url}: {e}")
    
    # Test 5: Knowledge Collector (Without Qdrant)
    print_section("Test 5: Knowledge Collector")
    collector = KnowledgeCollector(
        storage_directory="data/test_collected",
        ingestion_pipeline=None  # Skip Qdrant for this test
    )
    
    print("✓ Knowledge collector initialized")
    print(f"  Storage directory: {collector.storage_directory}")
    
    # Test 6: Integration with Knowledge Ingestion (If Qdrant Available)
    print_section("Test 6: Integration with Knowledge Ingestion")
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Initialize embedding generator
        embedding_gen = TextEmbeddingGenerator()
        
        # Create ingestion pipeline
        ingestion_pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=storage,
            text_embedding_generator=embedding_gen.generate_embedding,
            chunk_size=512,
            chunk_overlap=50
        )
        
        # Create collector with pipeline
        collector_with_qdrant = KnowledgeCollector(
            storage_directory="data/test_collected",
            ingestion_pipeline=ingestion_pipeline
        )
        
        print("✓ Knowledge collector with Qdrant integration initialized")
        print("  Ready to collect and store documents in Qdrant")
        
    except Exception as e:
        print(f"⚠ Qdrant not available: {e}")
        print("  Collector will work without Qdrant storage")
    
    print("\n" + "=" * 80)
    print("  All Tests Complete!")
    print("=" * 80)
    print("\nNote: Full crawling tests require network access and may take time.")
    print("For production use, configure sources and run with appropriate limits.")

if __name__ == "__main__":
    main()

