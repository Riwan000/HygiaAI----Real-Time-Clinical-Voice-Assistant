#!/usr/bin/env python3
"""
Test Outbreak Detection with Sample Data

Stores sample cases first, then tests all detection methods.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.qdrant_storage import QdrantStorage
from src.retrieval.case_retrieval import CaseRetriever
from src.embeddings.text_embeddings import TextEmbeddingGenerator
from src.outbreak import (
    OutbreakDetector,
    DetectionMethod,
    OutbreakDetectionOptions
)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test outbreak detection with sample data"""
    print("=" * 80)
    print("  Outbreak Detection Test with Sample Data")
    print("=" * 80)
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="clinical_cases",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        retriever = CaseRetriever(qdrant_storage=storage)
        
        # Initialize embedding generator
        embedding_generator = TextEmbeddingGenerator()
        
        # Store sample cases for testing
        print_section("Setting Up Test Data")
        
        base_time = datetime.now(timezone.utc)
        test_cases = [
            {
                "transcript": "Patient presents with high fever, persistent cough, and chest pain. Diagnosis: Pneumonia. Treatment: Amoxicillin.",
                "diagnosis": "Pneumonia",
                "outcome": "recovered",
                "timestamp": (base_time - timedelta(days=1)).isoformat(),
                "symptoms": ["fever", "cough", "chest pain"]
            },
            {
                "transcript": "Patient with fever, productive cough, and shortness of breath. Chest X-ray shows pneumonia. Treatment: Azithromycin.",
                "diagnosis": "Pneumonia",
                "outcome": "recovered",
                "timestamp": (base_time - timedelta(days=2)).isoformat(),
                "symptoms": ["fever", "cough", "shortness of breath"]
            },
            {
                "transcript": "Patient reports high fever and severe cough. Diagnosis: Community-acquired pneumonia. Treatment: Levofloxacin.",
                "diagnosis": "Pneumonia",
                "outcome": "improved",
                "timestamp": (base_time - timedelta(days=3)).isoformat(),
                "symptoms": ["fever", "cough"]
            },
            {
                "transcript": "Patient with fever, cough, and fatigue. Diagnosis: Bronchitis. Treatment: Antibiotics.",
                "diagnosis": "Bronchitis",
                "outcome": "recovered",
                "timestamp": (base_time - timedelta(days=4)).isoformat(),
                "symptoms": ["fever", "cough", "fatigue"]
            },
            {
                "transcript": "Patient presents with persistent cough and chest discomfort. Diagnosis: Bronchitis. Treatment: Expectorants.",
                "diagnosis": "Bronchitis",
                "outcome": "recovered",
                "timestamp": (base_time - timedelta(days=5)).isoformat(),
                "symptoms": ["cough", "chest discomfort"]
            },
            {
                "transcript": "Patient with headache, body aches, and fatigue. Diagnosis: Influenza. Treatment: Rest and fluids.",
                "diagnosis": "Influenza",
                "outcome": "recovered",
                "timestamp": (base_time - timedelta(days=6)).isoformat(),
                "symptoms": ["headache", "body aches", "fatigue"]
            },
            {
                "transcript": "Patient reports fever, chills, and muscle pain. Diagnosis: Flu. Treatment: Antiviral medication.",
                "diagnosis": "Influenza",
                "outcome": "improved",
                "timestamp": (base_time - timedelta(days=7)).isoformat(),
                "symptoms": ["fever", "chills", "muscle pain"]
            },
            {
                "transcript": "Patient with high fever, cough, and difficulty breathing. Diagnosis: Severe pneumonia. Treatment: Hospitalization.",
                "diagnosis": "Pneumonia",
                "outcome": "hospitalized",
                "timestamp": (base_time - timedelta(days=8)).isoformat(),
                "symptoms": ["fever", "cough", "difficulty breathing"]
            }
        ]
        
        print(f"Storing {len(test_cases)} test cases...")
        stored_ids = []
        
        for i, case in enumerate(test_cases):
            # Generate embedding
            embedding = embedding_generator.generate_embedding(case["transcript"])
            
            # Store case
            case_id = storage.store_transcript(
                transcript_data={
                    "transcript": case["transcript"],
                    "diagnosis": case["diagnosis"],
                    "outcome": case["outcome"],
                    "medical_entities": [
                        {"entity_type": "symptom", "text": symptom}
                        for symptom in case["symptoms"]
                    ]
                },
                embedding=embedding,
                metadata={
                    "session_id": f"test-session-{i+1:03d}",
                    "patient_id": f"test-patient-{i+1:03d}",
                    "timestamp": case["timestamp"],
                    "modality": "text"
                }
            )
            stored_ids.append(case_id)
        
        print(f"✓ Stored {len(stored_ids)} test cases")
        
        # Verify cases were stored by retrieving them
        print("\n  Verifying stored cases...")
        dummy_embedding = [0.0] * 768
        all_cases = storage.search_with_filters(
            query_embedding=dummy_embedding,
            filters=None,
            limit=100
        )
        print(f"  Found {len(all_cases)} total cases in collection")
        if all_cases:
            sample = all_cases[0]
            print(f"  Sample case payload keys: {list(sample.get('payload', {}).keys())}")
            print(f"  Sample timestamp: {sample.get('payload', {}).get('timestamp')}")
        
        # Initialize outbreak detector
        detector = OutbreakDetector(
            qdrant_storage=storage,
            case_retriever=retriever
        )
        
        # Test 1: DBSCAN Clustering
        print_section("Test 1: DBSCAN Clustering")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.DBSCAN,
            time_window_days=30,
            min_cluster_size=2,
            eps=0.5,
            min_samples=2,
            symptom_keywords=["fever", "cough", "pneumonia"]
        )
        
        result = detector.detect_outbreaks(options)
        print(f"✓ DBSCAN Detection Complete")
        print(f"  Total Cases Analyzed: {result.total_cases_analyzed}")
        print(f"  Clusters Detected: {len(result.clusters)}")
        print(f"  Alerts Generated: {len(result.alerts)}")
        print(f"  Anomaly Cases: {len(result.anomaly_cases)}")
        
        if result.clusters:
            print(f"\n  Clusters:")
            for cluster in result.clusters[:3]:
                print(f"    Cluster {cluster.cluster_id}:")
                print(f"      Size: {cluster.size}")
                print(f"      Symptoms: {', '.join(cluster.symptoms[:3])}")
                print(f"      Diagnoses: {', '.join(cluster.diagnoses[:3])}")
                print(f"      Density Score: {cluster.density_score:.3f}")
        
        if result.alerts:
            print(f"\n  Alerts:")
            for alert in result.alerts[:3]:
                print(f"    {alert.alert_id}:")
                print(f"      Level: {alert.level.value.upper()}")
                print(f"      Message: {alert.message}")
                print(f"      Confidence: {alert.confidence:.3f}")
                print(f"      Actions: {', '.join(alert.recommended_actions[:2])}")
        
        # Test 2: K-means Clustering
        print_section("Test 2: K-means Clustering")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.KMEANS,
            time_window_days=30,
            min_cluster_size=2,
            num_clusters=3,
            symptom_keywords=["fever", "cough"]
        )
        
        result = detector.detect_outbreaks(options)
        print(f"✓ K-means Detection Complete")
        print(f"  Total Cases Analyzed: {result.total_cases_analyzed}")
        print(f"  Clusters Detected: {len(result.clusters)}")
        print(f"  Alerts Generated: {len(result.alerts)}")
        
        if result.clusters:
            print(f"\n  Clusters:")
            for cluster in result.clusters:
                print(f"    Cluster {cluster.cluster_id}: {cluster.size} cases")
                if cluster.symptoms:
                    print(f"      Common Symptoms: {', '.join(cluster.symptoms[:3])}")
        
        # Test 3: Hierarchical Clustering
        print_section("Test 3: Hierarchical Clustering")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.HIERARCHICAL,
            time_window_days=30,
            min_cluster_size=2,
            num_clusters=3
        )
        
        result = detector.detect_outbreaks(options)
        print(f"✓ Hierarchical Detection Complete")
        print(f"  Total Cases Analyzed: {result.total_cases_analyzed}")
        print(f"  Clusters Detected: {len(result.clusters)}")
        print(f"  Alerts Generated: {len(result.alerts)}")
        
        # Test 4: Anomaly Detection
        print_section("Test 4: Anomaly Detection")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.ANOMALY_DETECTION,
            time_window_days=30,
            min_cluster_size=1,
            anomaly_threshold=0.9
        )
        
        result = detector.detect_outbreaks(options)
        print(f"✓ Anomaly Detection Complete")
        print(f"  Total Cases Analyzed: {result.total_cases_analyzed}")
        print(f"  Anomaly Cases: {len(result.anomaly_cases)}")
        print(f"  Clusters from Anomalies: {len(result.clusters)}")
        
        if result.anomaly_cases:
            print(f"\n  Sample Anomaly Cases: {result.anomaly_cases[:5]}")
        
        # Test 5: Surge-based (legacy method)
        print_section("Test 5: Surge-based Detection (Legacy)")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.SURGE_BASED,
            time_window_days=7,
            threshold=1.5,
            symptom_keywords=["fever", "cough", "pneumonia"]
        )
        
        result = detector.detect_outbreaks(options)
        print(f"✓ Surge-based Detection Complete")
        print(f"  Total Cases Analyzed: {result.total_cases_analyzed}")
        print(f"  Clusters Detected: {len(result.clusters)}")
        print(f"  Alerts Generated: {len(result.alerts)}")
        
        if result.clusters:
            print(f"\n  Detected Surges:")
            for cluster in result.clusters:
                print(f"    Symptom: {', '.join(cluster.symptoms)}")
                print(f"      Cluster Size: {cluster.size}")
                print(f"      Surge Ratio: {cluster.density_score:.2f}x")
        
        print("\n" + "=" * 80)
        print("  All Tests Complete!")
        print("=" * 80)
        print(f"\n✓ Test cases stored: {len(stored_ids)}")
        print(f"✓ All detection methods tested successfully")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

