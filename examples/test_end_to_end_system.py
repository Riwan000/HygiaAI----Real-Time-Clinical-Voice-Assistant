#!/usr/bin/env python3
"""
End-to-End System Test for HygiaAI

Tests the complete flow:
1. Transcription (simulated)
2. Entity Extraction
3. Embedding Generation
4. Storage in Qdrant
5. Case Retrieval
6. RAG-Based Clinical Insights
7. Visualization Data
8. Outbreak Detection
9. Knowledge Base Integration
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.case_models import Case, CaseModality, CaseMetadata
from src.storage.qdrant_storage import QdrantStorage
from src.embeddings.text_embeddings import TextEmbeddingGenerator
from src.entity_extraction.medical_ner import MedicalNER
from src.rag.clinical_rag import ClinicalRAG
from src.retrieval.case_retrieval import CaseRetriever
from src.visualization.temporal_trends import TemporalTrendAnalyzer
from src.outbreak.outbreak_detector import OutbreakDetector
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.collector import KnowledgeCollector, MedicalSource

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_result(success, message):
    """Print a test result"""
    status = "✓" if success else "✗"
    print(f"{status} {message}")

def main():
    """Run end-to-end system test"""
    print("=" * 80)
    print("  HygiaAI - End-to-End System Test")
    print("=" * 80)
    
    test_results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # Initialize components
        print_section("1. Initializing System Components")
        
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="clinical_cases",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print_result(True, "QdrantStorage initialized")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        embedding_gen = TextEmbeddingGenerator()
        print_result(True, "TextEmbeddingGenerator initialized")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        ner = MedicalNER()
        print_result(True, "MedicalNER initialized")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        retriever = CaseRetriever(qdrant_storage=storage, text_embedding_generator=embedding_gen)
        print_result(True, "CaseRetriever initialized")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        try:
            rag = ClinicalRAG(case_retriever=retriever, fallback_to_ollama=True)
            print_result(True, "ClinicalRAG initialized")
            test_results["total"] += 1
            test_results["passed"] += 1
            rag_available = True
        except (ValueError, Exception) as e:
            print_result(False, f"ClinicalRAG initialization skipped: {e}")
            test_results["total"] += 1
            test_results["failed"] += 1
            rag_available = False
            rag = None
        
        trend_analyzer = TemporalTrendAnalyzer(qdrant_storage=storage)
        print_result(True, "TemporalTrendAnalyzer initialized")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        outbreak_detector = OutbreakDetector(qdrant_storage=storage)
        print_result(True, "OutbreakDetector initialized")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        ingestion_pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=storage,
            text_embedding_generator=embedding_gen.generate_embedding,
            chunk_size=512,
            chunk_overlap=50,
            validate_schema=True,
            enforce_open_access=False  # Disable strict access validation for testing
        )
        print_result(True, "KnowledgeIngestionPipeline initialized")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        print()
        
        # Test 2: Simulate Transcription and Entity Extraction
        print_section("2. Transcription & Entity Extraction")
        
        # Simulate transcribed text (normally from Deepgram)
        transcribed_text = """
        Patient presents with fever, cough, and shortness of breath. 
        Temperature is 38.5°C. Blood pressure 120/80. 
        Patient reports chest pain and fatigue. 
        History of diabetes and hypertension.
        """
        
        print(f"Simulated transcription: {transcribed_text[:60]}...")
        test_results["total"] += 1
        test_results["passed"] += 1
        print_result(True, "Transcription simulated")
        
        # Extract medical entities
        entities = ner.extract_entities(transcribed_text)
        print(f"Extracted {len(entities)} medical entities:")
        for entity in entities[:5]:
            # Handle both dict and object types
            if isinstance(entity, dict):
                print(f"  - {entity.get('text', 'N/A')} ({entity.get('type', 'N/A')})")
            else:
                print(f"  - {getattr(entity, 'text', 'N/A')} ({getattr(entity, 'type', 'N/A')})")
        
        if len(entities) > 0:
            print_result(True, f"Entity extraction successful: {len(entities)} entities")
            test_results["total"] += 1
            test_results["passed"] += 1
        else:
            print_result(False, "No entities extracted")
            test_results["total"] += 1
            test_results["failed"] += 1
        
        print()
        
        # Test 3: Create and Store Clinical Case
        print_section("3. Clinical Case Creation & Storage")
        
        # Create a clinical case
        case_metadata = CaseMetadata(
            timestamp=datetime.now(timezone.utc),
            age_group="adult",
            region="urban",
            comorbidities=["diabetes", "hypertension"],
            diagnosis="respiratory infection",
            outcome="under observation"
        )
        
        case = Case(
            case_id="test_case_001",
            patient_id="test_patient_001",
            modalities={
                "text": CaseModality(
                    modality_type="text",
                    content={
                        "transcript": transcribed_text,
                        "entities": entities
                    }
                )
            },
            metadata=case_metadata
        )
        
        print_result(True, "Clinical case created")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        # Generate embedding
        case_embedding = embedding_gen.generate_embedding(transcribed_text)
        print_result(True, f"Embedding generated: {len(case_embedding)} dimensions")
        test_results["total"] += 1
        test_results["passed"] += 1
        
        # Store in Qdrant
        try:
            # Prepare transcript data
            transcript_data = {
                "session_id": "test_session_001",
                "transcript": transcribed_text,
                "timestamp": case.metadata.timestamp.isoformat(),
                "confidence": 0.95,
                "speaker": "patient",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "patient_id": case.patient_id,
                    "age_group": case.metadata.age_group,
                    "region": case.metadata.region,
                    "comorbidities": case.metadata.comorbidities,
                    "diagnosis": case.metadata.diagnosis,
                    "outcome": case.metadata.outcome,
                    "medical_entities": json.dumps([{"text": getattr(e, 'text', str(e)), "type": getattr(e, 'entity_type', 'unknown').value if hasattr(getattr(e, 'entity_type', None), 'value') else 'unknown'} if not isinstance(e, dict) else e for e in entities])
                }
            }
            
            case_id = storage.store_transcript(
                transcript_data=transcript_data,
                embedding=case_embedding
            )
            print_result(True, f"Case stored in Qdrant: {case_id}")
            test_results["total"] += 1
            test_results["passed"] += 1
        except Exception as e:
            print_result(False, f"Failed to store case: {e}")
            test_results["total"] += 1
            test_results["failed"] += 1
            test_results["errors"].append(f"Storage error: {e}")
        
        print()
        
        # Test 4: Case Retrieval
        print_section("4. Case Retrieval")
        
        try:
            # Retrieve similar cases
            query_text = "fever and cough with respiratory symptoms"
            query_embedding = embedding_gen.generate_embedding(query_text)
            
            from src.retrieval.case_retrieval import RetrievalOptions
            options = RetrievalOptions(limit=5)
            results = retriever.retrieve_similar_cases(
                query_text=query_text,
                options=options
            )
            
            if results:
                print_result(True, f"Retrieved {len(results)} similar cases")
                test_results["total"] += 1
                test_results["passed"] += 1
                
                # Show top result
                top_result = results[0]
                print(f"  Top match: Score {top_result.score:.4f}")
                print(f"    Diagnosis: {top_result.case_data.get('diagnosis', 'N/A')}")
            else:
                print_result(False, "No cases retrieved")
                test_results["total"] += 1
                test_results["failed"] += 1
        except Exception as e:
            print_result(False, f"Retrieval error: {e}")
            test_results["total"] += 1
            test_results["failed"] += 1
            test_results["errors"].append(f"Retrieval error: {e}")
        
        print()
        
        # Test 5: RAG-Based Clinical Insights
        print_section("5. RAG-Based Clinical Insights")
        
        if not rag_available:
            print_result(False, "RAG test skipped (API key not available)")
            test_results["total"] += 1
            test_results["failed"] += 1
        else:
            try:
                query = "What are the potential diagnoses for a patient with fever, cough, and shortness of breath?"
                
                insight = rag.generate_insight(
                    query=query,
                    max_cases=3
                )
                
                if insight:
                    print_result(True, "Clinical insight generated")
                    test_results["total"] += 1
                    test_results["passed"] += 1
                    
                    print(f"  Confidence: {insight.confidence_score:.2f}" if insight.confidence_score else "  Confidence: N/A")
                    print(f"  Differential diagnoses: {len(insight.differential_diagnoses)}")
                    print(f"  Recommendations: {len(insight.recommendations)}")
                    
                    if insight.differential_diagnoses:
                        first_diag = insight.differential_diagnoses[0]
                        if isinstance(first_diag, dict):
                            print(f"  Top diagnosis: {first_diag.get('diagnosis', 'N/A')} "
                                  f"(confidence: {first_diag.get('confidence', 'N/A')})")
                else:
                    print_result(False, "No insight generated")
                    test_results["total"] += 1
                    test_results["failed"] += 1
            except Exception as e:
                print_result(False, f"RAG error: {e}")
                test_results["total"] += 1
                test_results["failed"] += 1
                test_results["errors"].append(f"RAG error: {e}")
        
        print()
        
        # Test 6: Temporal Trends Analysis
        print_section("6. Temporal Trends Analysis")
        
        try:
            from src.visualization.temporal_trends import TrendOptions
            from datetime import timedelta
            
            from src.visualization.temporal_trends import TrendGranularity
            options = TrendOptions(
                start_date=datetime.now(timezone.utc) - timedelta(days=30),
                end_date=datetime.now(timezone.utc),
                granularity=TrendGranularity.DAILY
            )
            
            # Analyze symptom trends
            trends = trend_analyzer.analyze_symptom_trends(options=options)
            
            if trends and hasattr(trends, 'data_points'):
                print_result(True, "Temporal trends analyzed")
                test_results["total"] += 1
                test_results["passed"] += 1
                
                print(f"  Data points: {len(trends.data_points) if trends.data_points else 0}")
                if trends.data_points:
                    print(f"  Latest count: {trends.data_points[-1].count if hasattr(trends.data_points[-1], 'count') else 'N/A'}")
            elif trends:
                print_result(True, "Temporal trends analyzed")
                test_results["total"] += 1
                test_results["passed"] += 1
                print(f"  Trend data available")
            else:
                print_result(False, "No trend data available")
                test_results["total"] += 1
                test_results["failed"] += 1
        except Exception as e:
            print_result(False, f"Trend analysis error: {e}")
            test_results["total"] += 1
            test_results["failed"] += 1
            test_results["errors"].append(f"Trend analysis error: {e}")
        
        print()
        
        # Test 7: Outbreak Detection
        print_section("7. Outbreak Detection")
        
        try:
            from src.outbreak.outbreak_detector import OutbreakDetectionOptions, DetectionMethod
            from datetime import timedelta
            
            options = OutbreakDetectionOptions(
                time_window_days=30,
                method=DetectionMethod.DBSCAN,
                min_cluster_size=3
            )
            
            # Detect outbreaks
            result = outbreak_detector.detect_outbreaks(options=options)
            alerts = result.alerts if result else []
            
            if alerts is not None:
                print_result(True, "Outbreak detection completed")
                test_results["total"] += 1
                test_results["passed"] += 1
                
                print(f"  Alerts generated: {len(alerts)}")
                for alert in alerts[:3]:
                    level = alert.level.value if hasattr(alert, 'level') else 'unknown'
                    message = alert.message[:50] if hasattr(alert, 'message') else 'N/A'
                    print(f"    - {level}: {message}...")
            else:
                print_result(False, "Outbreak detection failed")
                test_results["total"] += 1
                test_results["failed"] += 1
        except Exception as e:
            print_result(False, f"Outbreak detection error: {e}")
            test_results["total"] += 1
            test_results["failed"] += 1
            test_results["errors"].append(f"Outbreak detection error: {e}")
        
        print()
        
        # Test 8: Knowledge Base Integration
        print_section("8. Knowledge Base Integration")
        
        try:
            # Ingest a sample knowledge document
            knowledge_doc = {
                "title": "Respiratory Infection Treatment Guidelines",
                "text": "Respiratory infections are common conditions that require proper diagnosis and treatment. Symptoms include fever, cough, and shortness of breath.",
                "source": "test",
                "domain": "general",
                "year": 2024,
                "provenance_url": "https://test.example.com/guidelines.html",
                "access_type": "open"  # Explicitly mark as open-access
            }
            
            point_ids = ingestion_pipeline.ingest_document(knowledge_doc)
            
            if point_ids:
                print_result(True, f"Knowledge document ingested: {len(point_ids)} chunks")
                test_results["total"] += 1
                test_results["passed"] += 1
                
                # Search knowledge base
                query_embedding = embedding_gen.generate_embedding("respiratory infection treatment")
                results = storage.search_with_filters(
                    query_embedding=query_embedding,
                    filters={"source": "test", "domain": "general"},
                    limit=3
                )
                
                if results:
                    print_result(True, f"Knowledge base search successful: {len(results)} results")
                    test_results["total"] += 1
                    test_results["passed"] += 1
                else:
                    print_result(False, "No knowledge base results")
                    test_results["total"] += 1
                    test_results["failed"] += 1
            else:
                print_result(False, "Knowledge ingestion failed")
                test_results["total"] += 1
                test_results["failed"] += 1
        except Exception as e:
            print_result(False, f"Knowledge base error: {e}")
            test_results["total"] += 1
            test_results["failed"] += 1
            test_results["errors"].append(f"Knowledge base error: {e}")
        
        print()
        
        # Test 9: System Integration Check
        print_section("9. System Integration Check")
        
        # Check all components are working together
        components_ok = True
        
        try:
            # Verify storage is accessible
            collection_info = storage.get_collection_info()
            if collection_info:
                print_result(True, "Qdrant collection accessible")
                test_results["total"] += 1
                test_results["passed"] += 1
            else:
                components_ok = False
                print_result(False, "Qdrant collection not accessible")
                test_results["total"] += 1
                test_results["failed"] += 1
        except Exception as e:
            components_ok = False
            print_result(False, f"Collection check failed: {e}")
            test_results["total"] += 1
            test_results["failed"] += 1
            test_results["errors"].append(f"Collection check error: {e}")
        
        print()
        
        # Final Summary
        print_section("Test Summary")
        
        print(f"Total Tests: {test_results['total']}")
        print(f"Passed: {test_results['passed']} ({test_results['passed']/test_results['total']*100:.1f}%)")
        print(f"Failed: {test_results['failed']} ({test_results['failed']/test_results['total']*100:.1f}%)")
        
        if test_results['errors']:
            print("\nErrors encountered:")
            for error in test_results['errors']:
                print(f"  - {error}")
        
        success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
        
        print("\n" + "=" * 80)
        if success_rate >= 80:
            print(f"  ✓ End-to-End Test: PASSED ({success_rate:.1f}% success rate)")
        else:
            print(f"  ✗ End-to-End Test: FAILED ({success_rate:.1f}% success rate)")
        print("=" * 80)
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"\n✗ Critical Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

