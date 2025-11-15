#!/usr/bin/env python3
"""
Test Outbreak Detection

Tests the advanced outbreak detection system with various clustering algorithms.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.qdrant_storage import QdrantStorage
from src.retrieval.case_retrieval import CaseRetriever
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
    """Test outbreak detection"""
    print("=" * 80)
    print("  Outbreak Detection Test")
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
        
        # Initialize outbreak detector
        detector = OutbreakDetector(
            qdrant_storage=storage,
            case_retriever=retriever
        )
        
        # Test 1: DBSCAN Clustering
        print_section("Test 1: DBSCAN Clustering")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.DBSCAN,
            time_window_days=365,  # Use wider window to catch demo cases
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
                print(f"      Density Score: {cluster.density_score:.3f}")
        
        if result.alerts:
            print(f"\n  Alerts:")
            for alert in result.alerts[:3]:
                print(f"    {alert.alert_id}:")
                print(f"      Level: {alert.level.value}")
                print(f"      Message: {alert.message}")
                print(f"      Confidence: {alert.confidence:.3f}")
                print(f"      Actions: {', '.join(alert.recommended_actions[:2])}")
        
        # Test 2: K-means Clustering
        print_section("Test 2: K-means Clustering")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.KMEANS,
            time_window_days=365,  # Use wider window
            min_cluster_size=2,
            num_clusters=5,
            symptom_keywords=["fever", "cough"]
        )
        
        result = detector.detect_outbreaks(options)
        print(f"✓ K-means Detection Complete")
        print(f"  Total Cases Analyzed: {result.total_cases_analyzed}")
        print(f"  Clusters Detected: {len(result.clusters)}")
        print(f"  Alerts Generated: {len(result.alerts)}")
        
        # Test 3: Anomaly Detection
        print_section("Test 3: Anomaly Detection")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.ANOMALY_DETECTION,
            time_window_days=365,  # Use wider window
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
        
        # Test 4: Surge-based (legacy method)
        print_section("Test 4: Surge-based Detection (Legacy)")
        options = OutbreakDetectionOptions(
            method=DetectionMethod.SURGE_BASED,
            time_window_days=7,
            threshold=2.0,
            symptom_keywords=["fever", "cough", "pneumonia"]
        )
        
        result = detector.detect_outbreaks(options)
        print(f"✓ Surge-based Detection Complete")
        print(f"  Total Cases Analyzed: {result.total_cases_analyzed}")
        print(f"  Clusters Detected: {len(result.clusters)}")
        print(f"  Alerts Generated: {len(result.alerts)}")
        
        print("\n" + "=" * 80)
        print("  All Tests Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

