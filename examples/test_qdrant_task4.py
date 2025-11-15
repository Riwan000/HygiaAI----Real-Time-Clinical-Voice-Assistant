"""
Example: Testing Task 4 Features

Demonstrates:
- Multi-vector embeddings (text + image)
- Knowledge base document storage
- Enhanced filtering (range, "in", exact match)
- Hybrid search (semantic + keyword)
- Knowledge ingestion pipeline
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage import (
    QdrantStorage,
    KnowledgeBaseMetadata,
    KnowledgeBaseSchema,
    EmbeddingType,
    AccessType,
    KnowledgeIngestionPipeline,
)
from src.embeddings import BioBERTEmbeddingGenerator, CLIPEmbeddingGenerator
from src.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")


def test_multi_vector_embeddings():
    """Test multi-vector embedding storage"""
    print("=" * 60)
    print("Test 1: Multi-Vector Embeddings (Text + Image)")
    print("=" * 60)
    print()
    
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Initialize embedding generators
        text_generator = BioBERTEmbeddingGenerator()
        image_generator = CLIPEmbeddingGenerator()
        
        # Generate embeddings
        text = "Patient has fever and cough. Blood pressure: 140/90 mmHg."
        text_embedding = text_generator.generate_embedding(text)
        
        print(f"Text: {text}")
        print(f"Text embedding dimension: {len(text_embedding)}")
        print()
        
        # Store multi-vector embedding
        data = {
            "transcript": text,
            "image_path": "xray.jpg"  # Placeholder
        }
        
        # Note: In real scenario, you would have an actual image
        # For this example, we'll use text-only embedding
        point_id = storage.store_multimodal_embedding(
            data=data,
            text_embedding=text_embedding,
            image_embedding=None  # Would be image_generator.generate_embedding("xray.jpg")
        )
        
        print(f"✓ Stored multi-vector embedding: {point_id}")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_knowledge_base_documents():
    """Test knowledge base document storage"""
    print("=" * 60)
    print("Test 2: Knowledge Base Document Storage")
    print("=" * 60)
    print()
    
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Initialize text embedding generator
        text_generator = BioBERTEmbeddingGenerator()
        
        # Create knowledge base document
        document_data = {
            "title": "Clinical Guidelines for Fever Management",
            "text": "Fever is a common symptom in clinical practice. Management includes...",
            "source": "NCBI Bookshelf",
            "domain": "pathology",
            "year": 2024,
            "provenance_url": "https://example.com/guidelines",
            "version": "1.0",
            "author": "Medical Guidelines Committee"
        }
        
        # Generate text embedding
        text_embedding = text_generator.generate_embedding(document_data["text"])
        
        print(f"Title: {document_data['title']}")
        print(f"Source: {document_data['source']}")
        print(f"Domain: {document_data['domain']}")
        print(f"Year: {document_data['year']}")
        print(f"Text embedding dimension: {len(text_embedding)}")
        print()
        
        # Store knowledge base document
        point_id = storage.store_knowledge_base_document(
            document_data=document_data,
            text_embedding=text_embedding,
            image_embedding=None
        )
        
        print(f"✓ Stored knowledge base document: {point_id}")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_enhanced_filtering():
    """Test enhanced filtering capabilities"""
    print("=" * 60)
    print("Test 3: Enhanced Filtering (Range, 'In', Exact Match)")
    print("=" * 60)
    print()
    
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Initialize text embedding generator
        text_generator = BioBERTEmbeddingGenerator()
        
        query_text = "fever management"
        query_embedding = text_generator.generate_embedding(query_text)
        
        print(f"Query: {query_text}")
        print()
        
        # Test range filters
        print("Testing range filters (age, year):")
        filters_range = {
            "age": {"gte": 30, "lte": 50},
            "year": {"gte": 2020}
        }
        print(f"  Filters: {filters_range}")
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=filters_range,
            limit=5
        )
        print(f"  Results: {len(results)} documents found")
        print()
        
        # Test "in" filters
        print("Testing 'in' filters (domain, source):")
        filters_in = {
            "domain": {"in": ["pathology", "pharmacology"]},
            "source": "NCBI Bookshelf"
        }
        print(f"  Filters: {filters_in}")
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=filters_in,
            limit=5
        )
        print(f"  Results: {len(results)} documents found")
        print()
        
        # Test exact match filters
        print("Testing exact match filters (access_type, domain):")
        filters_exact = {
            "access_type": "open",
            "domain": "pathology"
        }
        print(f"  Filters: {filters_exact}")
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=filters_exact,
            limit=5
        )
        print(f"  Results: {len(results)} documents found")
        print()
        
        print("✓ Enhanced filtering tests completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_hybrid_search():
    """Test hybrid search (semantic + keyword)"""
    print("=" * 60)
    print("Test 4: Hybrid Search (Semantic + Keyword)")
    print("=" * 60)
    print()
    
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Initialize text embedding generator
        text_generator = BioBERTEmbeddingGenerator()
        
        query_text = "fever cough treatment"
        query_embedding = text_generator.generate_embedding(query_text)
        
        print(f"Query: {query_text}")
        print()
        
        # Test hybrid search
        results = storage.hybrid_search(
            query_text=query_text,
            query_embedding=query_embedding,
            limit=5,
            semantic_weight=0.7,
            keyword_weight=0.3
        )
        
        print(f"Results: {len(results)} documents found")
        print()
        
        for i, result in enumerate(results[:3], 1):
            print(f"Result {i}:")
            print(f"  ID: {result['id']}")
            print(f"  Semantic Score: {result.get('semantic_score', 0):.3f}")
            print(f"  Keyword Score: {result.get('keyword_score', 0):.3f}")
            print(f"  Combined Score: {result.get('combined_score', 0):.3f}")
            print()
        
        print("✓ Hybrid search test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_knowledge_ingestion_pipeline():
    """Test knowledge ingestion pipeline"""
    print("=" * 60)
    print("Test 5: Knowledge Ingestion Pipeline")
    print("=" * 60)
    print()
    
    try:
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        # Initialize embedding generators
        text_generator = BioBERTEmbeddingGenerator()
        
        # Create ingestion pipeline
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=storage,
            text_embedding_generator=text_generator.generate_embedding,
            chunk_size=200,
            chunk_overlap=50
        )
        
        # Test document chunking
        print("Testing document chunking:")
        text = "Fever is a common symptom. " * 20  # Long text
        chunks = pipeline.chunk_text(text, chunk_size=100, chunk_overlap=20)
        print(f"  Text length: {len(text)} characters")
        print(f"  Number of chunks: {len(chunks)}")
        print(f"  First chunk: {chunks[0]['text'][:50]}...")
        print()
        
        # Test document ingestion
        print("Testing document ingestion:")
        document = {
            "title": "Fever Management Guidelines",
            "text": "Fever is a common symptom in clinical practice. Management includes monitoring temperature, administering antipyretics, and identifying underlying causes. " * 5,
            "source": "NCBI Bookshelf",
            "domain": "pathology",
            "year": 2024,
            "provenance_url": "https://example.com/guidelines",
            "version": "1.0"
        }
        
        point_ids = pipeline.ingest_document(document)
        print(f"  Document ingested: {len(point_ids)} chunks stored")
        print(f"  Point IDs: {point_ids[:3]}...")
        print()
        
        # Test batch ingestion
        print("Testing batch ingestion:")
        documents = [
            {
                "title": f"Document {i}",
                "text": f"Content for document {i}. " * 10,
                "source": "Test Source",
                "domain": "pathology",
                "year": 2024
            }
            for i in range(3)
        ]
        
        stats = pipeline.ingest_batch(documents)
        print(f"  Total: {stats['total']}")
        print(f"  Ingested: {stats['ingested']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Errors: {stats['errors']}")
        print()
        
        print("✓ Knowledge ingestion pipeline test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def main():
    """Run all Task 4 tests"""
    print()
    print("=" * 60)
    print("Task 4: Qdrant Vector Store Integration Test Suite")
    print("=" * 60)
    print()
    
    test_multi_vector_embeddings()
    test_knowledge_base_documents()
    test_enhanced_filtering()
    test_hybrid_search()
    test_knowledge_ingestion_pipeline()
    
    print("=" * 60)
    print("✅ All Task 4 tests completed!")
    print("=" * 60)
    print()
    print("Note: Some tests require Qdrant to be running.")
    print("To start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
    print()


if __name__ == "__main__":
    main()

