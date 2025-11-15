"""
Example: Testing Case Retrieval

Demonstrates:
- Semantic search for clinical cases
- Keyword-based search with filters
- Hybrid search (semantic + keyword)
- Retrieval by entity type, time range, demographics
- Multi-modal case retrieval
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.retrieval import CaseRetriever, RetrievalOptions, RetrievalMode
from src.storage import QdrantStorage
from src.embeddings import BioBERTEmbeddingGenerator, CLIPEmbeddingGenerator
from src.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")


def test_semantic_search():
    """Test semantic search for clinical cases"""
    print("=" * 60)
    print("Test 1: Semantic Search for Clinical Cases")
    print("=" * 60)
    print()
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        text_generator = BioBERTEmbeddingGenerator()
        retriever = CaseRetriever(
            qdrant_storage=storage,
            text_embedding_generator=text_generator
        )
        
        # Semantic search
        query_text = "Patient reports fever, cough, and chest pain"
        options = RetrievalOptions(
            mode=RetrievalMode.SEMANTIC,
            limit=5,
            score_threshold=0.7
        )
        
        print(f"Query: {query_text}")
        print(f"Mode: {options.mode.value}")
        print()
        
        results = retriever.retrieve_similar_cases(
            query_text=query_text,
            options=options
        )
        
        print(f"Found {len(results)} similar cases:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Case {i}:")
            print(f"  ID: {result.case_id}")
            print(f"  Score: {result.score:.3f}")
            if result.metadata:
                print(f"  Age Group: {result.metadata.age_group}")
                print(f"  Region: {result.metadata.region}")
                print(f"  Diagnosis: {result.metadata.diagnosis}")
                print(f"  Outcome: {result.metadata.outcome}")
            if result.modalities.get("text"):
                transcript = result.modalities["text"].get("transcript", "")
                print(f"  Transcript: {transcript[:100]}...")
            print()
        
        print("✓ Semantic search test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_keyword_search():
    """Test keyword-based search with filters"""
    print("=" * 60)
    print("Test 2: Keyword-Based Search with Filters")
    print("=" * 60)
    print()
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        retriever = CaseRetriever(qdrant_storage=storage)
        
        # Keyword search with filters
        options = RetrievalOptions(
            mode=RetrievalMode.KEYWORD,
            limit=5,
            age_group="adult",
            age_range={"gte": 30, "lte": 50},
            region="rural_clinic_001",
            comorbidities=["diabetes", "hypertension"],
            diagnosis="pneumonia"
        )
        
        print("Filters:")
        print(f"  Age Group: {options.age_group}")
        print(f"  Age Range: {options.age_range}")
        print(f"  Region: {options.region}")
        print(f"  Comorbidities: {options.comorbidities}")
        print(f"  Diagnosis: {options.diagnosis}")
        print()
        
        results = retriever.retrieve_similar_cases(
            query_text="",
            options=options
        )
        
        print(f"Found {len(results)} matching cases:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Case {i}:")
            print(f"  ID: {result.case_id}")
            print(f"  Score: {result.score:.3f}")
            if result.metadata:
                print(f"  Age Group: {result.metadata.age_group}")
                print(f"  Region: {result.metadata.region}")
                print(f"  Comorbidities: {result.metadata.comorbidities}")
                print(f"  Diagnosis: {result.metadata.diagnosis}")
            print()
        
        print("✓ Keyword search test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_hybrid_search():
    """Test hybrid search (semantic + keyword)"""
    print("=" * 60)
    print("Test 3: Hybrid Search (Semantic + Keyword)")
    print("=" * 60)
    print()
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        text_generator = BioBERTEmbeddingGenerator()
        retriever = CaseRetriever(
            qdrant_storage=storage,
            text_embedding_generator=text_generator
        )
        
        # Hybrid search
        query_text = "fever cough chest pain"
        options = RetrievalOptions(
            mode=RetrievalMode.HYBRID,
            limit=5,
            semantic_weight=0.7,
            keyword_weight=0.3,
            age_group="adult",
            diagnosis="pneumonia"
        )
        
        print(f"Query: {query_text}")
        print(f"Mode: {options.mode.value}")
        print(f"Semantic Weight: {options.semantic_weight}")
        print(f"Keyword Weight: {options.keyword_weight}")
        print()
        
        results = retriever.retrieve_similar_cases(
            query_text=query_text,
            options=options
        )
        
        print(f"Found {len(results)} similar cases:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Case {i}:")
            print(f"  ID: {result.case_id}")
            print(f"  Combined Score: {result.combined_score:.3f}")
            print(f"  Semantic Score: {result.semantic_score:.3f}")
            print(f"  Keyword Score: {result.keyword_score:.3f}")
            if result.metadata:
                print(f"  Diagnosis: {result.metadata.diagnosis}")
                print(f"  Outcome: {result.metadata.outcome}")
            print()
        
        print("✓ Hybrid search test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_retrieve_by_entity_type():
    """Test retrieval by entity type"""
    print("=" * 60)
    print("Test 4: Retrieve by Entity Type")
    print("=" * 60)
    print()
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        retriever = CaseRetriever(qdrant_storage=storage)
        
        # Retrieve by entity type
        print("Retrieving cases with symptom: 'fever'")
        print()
        
        results = retriever.retrieve_by_entity_type(
            entity_type="symptom",
            entity_value="fever",
            options=RetrievalOptions(limit=5)
        )
        
        print(f"Found {len(results)} cases with symptom 'fever':")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Case {i}:")
            print(f"  ID: {result.case_id}")
            print(f"  Score: {result.score:.3f}")
            if result.modalities.get("text"):
                entities = result.modalities["text"].get("entities", [])
                print(f"  Entities: {len(entities)} found")
            print()
        
        print("✓ Entity type retrieval test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_retrieve_by_time_range():
    """Test retrieval by time range"""
    print("=" * 60)
    print("Test 5: Retrieve by Time Range")
    print("=" * 60)
    print()
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        text_generator = BioBERTEmbeddingGenerator()
        retriever = CaseRetriever(
            qdrant_storage=storage,
            text_embedding_generator=text_generator
        )
        
        # Retrieve by time range (last 6 months)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=180)
        
        print(f"Time Range: {start_time.date()} to {end_time.date()}")
        print()
        
        results = retriever.retrieve_by_time_range(
            start_time=start_time,
            end_time=end_time,
            query_text="pneumonia",
            options=RetrievalOptions(limit=5)
        )
        
        print(f"Found {len(results)} cases in the last 6 months:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Case {i}:")
            print(f"  ID: {result.case_id}")
            print(f"  Score: {result.score:.3f}")
            if result.metadata:
                print(f"  Timestamp: {result.metadata.timestamp}")
                print(f"  Diagnosis: {result.metadata.diagnosis}")
            print()
        
        print("✓ Time range retrieval test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def test_retrieve_by_demographics():
    """Test retrieval by demographics"""
    print("=" * 60)
    print("Test 6: Retrieve by Demographics")
    print("=" * 60)
    print()
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        text_generator = BioBERTEmbeddingGenerator()
        retriever = CaseRetriever(
            qdrant_storage=storage,
            text_embedding_generator=text_generator
        )
        
        # Retrieve by demographics
        print("Demographic Filters:")
        print("  Age Group: adult")
        print("  Age Range: 30-50")
        print("  Region: rural_clinic_001")
        print("  Comorbidities: diabetes, hypertension")
        print()
        
        results = retriever.retrieve_by_demographics(
            age_group="adult",
            age_range={"gte": 30, "lte": 50},
            region="rural_clinic_001",
            comorbidities=["diabetes", "hypertension"],
            query_text="fever cough",
            options=RetrievalOptions(limit=5)
        )
        
        print(f"Found {len(results)} matching cases:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Case {i}:")
            print(f"  ID: {result.case_id}")
            print(f"  Score: {result.score:.3f}")
            if result.metadata:
                print(f"  Age Group: {result.metadata.age_group}")
                print(f"  Region: {result.metadata.region}")
                print(f"  Comorbidities: {result.metadata.comorbidities}")
                print(f"  Diagnosis: {result.metadata.diagnosis}")
            print()
        
        print("✓ Demographics retrieval test completed")
        print()
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("  This is expected if Qdrant is not running.")
        print()


def main():
    """Run all case retrieval tests"""
    print()
    print("=" * 60)
    print("Case Retrieval Test Suite")
    print("=" * 60)
    print()
    
    test_semantic_search()
    test_keyword_search()
    test_hybrid_search()
    test_retrieve_by_entity_type()
    test_retrieve_by_time_range()
    test_retrieve_by_demographics()
    
    print("=" * 60)
    print("✅ All case retrieval tests completed!")
    print("=" * 60)
    print()
    print("Note: Some tests require Qdrant to be running.")
    print("To start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
    print()


if __name__ == "__main__":
    main()

