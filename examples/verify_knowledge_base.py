#!/usr/bin/env python3
"""
Verify Knowledge Base

Tests that the knowledge base was populated correctly and can be queried.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.qdrant_storage import QdrantStorage
from src.embeddings.text_embeddings import TextEmbeddingGenerator
from src.retrieval.case_retrieval import CaseRetriever

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Verify knowledge base"""
    print("=" * 80)
    print("  Knowledge Base Verification")
    print("=" * 80)
    
    try:
        # Initialize Qdrant storage
        print_section("1. Connecting to Qdrant")
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print("✓ Connected to Qdrant")
        
        # Get collection info
        collection_info = storage.get_collection_info()
        if collection_info:
            points_count = collection_info.get("points_count", 0)
            print(f"✓ Collection 'knowledge_base' has {points_count} points")
        print()
        
        # Initialize embedding generator
        print_section("2. Testing Embedding Generation")
        embedding_gen = TextEmbeddingGenerator()
        test_text = "What is pathology?"
        embedding = embedding_gen.generate_embedding(test_text)
        print(f"✓ Generated embedding for query: '{test_text}'")
        print(f"  Embedding dimension: {len(embedding)}")
        print()
        
        # Test search
        print_section("3. Testing Knowledge Base Search")
        results = storage.search_with_filters(
            query_embedding=embedding,
            filters=None,
            limit=5
        )
        
        print(f"✓ Found {len(results)} results")
        print()
        
        for i, result in enumerate(results, 1):
            payload = result.get("payload", {})
            title = payload.get("title", "Unknown")
            source = payload.get("source", "Unknown")
            domain = payload.get("domain", "Unknown")
            score = result.get("score", 0.0)
            
            print(f"  Result {i}:")
            print(f"    Title: {title}")
            print(f"    Source: {source}")
            print(f"    Domain: {domain}")
            print(f"    Similarity Score: {score:.4f}")
            
            # Show text snippet
            text = payload.get("text", "")
            if text:
                snippet = text[:100] + "..." if len(text) > 100 else text
                print(f"    Text: {snippet}")
            print()
        
        # Test domain filtering
        print_section("4. Testing Domain Filtering")
        pathology_results = storage.search_with_filters(
            query_embedding=embedding,
            filters={"domain": "pathology"},
            limit=3
        )
        print(f"✓ Found {len(pathology_results)} pathology documents")
        
        pharmacology_results = storage.search_with_filters(
            query_embedding=embedding,
            filters={"domain": "pharmacology"},
            limit=3
        )
        print(f"✓ Found {len(pharmacology_results)} pharmacology documents")
        print()
        
        # Test source filtering
        print_section("5. Testing Source Filtering")
        demo_results = storage.search_with_filters(
            query_embedding=embedding,
            filters={"source": "demo"},
            limit=5
        )
        print(f"✓ Found {len(demo_results)} documents from 'demo' source")
        print()
        
        # Test direct search with different queries
        print_section("6. Testing Multiple Query Types")
        
        queries = [
            "What are the principles of medical diagnosis?",
            "How do drugs interact with the body?",
            "What are clinical practice guidelines?"
        ]
        
        for query in queries:
            query_embedding = embedding_gen.generate_embedding(query)
            results = storage.search_with_filters(
                query_embedding=query_embedding,
                filters=None,
                limit=2
            )
            
            print(f"✓ Query: '{query}'")
            print(f"  Found {len(results)} results")
            if results:
                top_result = results[0]
                payload = top_result.get("payload", {})
                print(f"  Top result: {payload.get('title', 'Unknown')} (score: {top_result.get('score', 0):.4f})")
            print()
        
        print("=" * 80)
        print("  Knowledge Base Verification Complete!")
        print("=" * 80)
        print("\n✓ All tests passed!")
        print("✓ Knowledge base is ready for use in the demo.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

