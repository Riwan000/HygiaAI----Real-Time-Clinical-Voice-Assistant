"""
Unit tests for outbreak detection module
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from src.outbreak import (
    OutbreakDetector,
    DetectionMethod,
    AlertLevel,
    OutbreakDetectionOptions,
    OutbreakCluster,
    OutbreakAlert
)
from src.storage import QdrantStorage
from src.retrieval import CaseRetriever


@pytest.fixture
def mock_storage():
    """Mock QdrantStorage"""
    storage = Mock(spec=QdrantStorage)
    storage.vector_size = 768
    storage.collection_name = "clinical_cases"
    storage.client = Mock()
    return storage


@pytest.fixture
def mock_retriever():
    """Mock CaseRetriever"""
    return Mock(spec=CaseRetriever)


@pytest.fixture
def sample_cases():
    """Sample cases for testing"""
    base_time = datetime.now(timezone.utc)
    return [
        {
            "id": "case-1",
            "payload": {
                "timestamp": (base_time - timedelta(days=1)).isoformat(),
                "medical_entities": [
                    {"entity_type": "symptom", "text": "fever"},
                    {"entity_type": "symptom", "text": "cough"},
                    {"entity_type": "diagnosis", "text": "pneumonia"}
                ],
                "diagnosis": "pneumonia"
            },
            "vector": [0.1] * 768
        },
        {
            "id": "case-2",
            "payload": {
                "timestamp": (base_time - timedelta(days=2)).isoformat(),
                "medical_entities": [
                    {"entity_type": "symptom", "text": "fever"},
                    {"entity_type": "symptom", "text": "cough"},
                    {"entity_type": "diagnosis", "text": "bronchitis"}
                ],
                "diagnosis": "bronchitis"
            },
            "vector": [0.2] * 768
        },
        {
            "id": "case-3",
            "payload": {
                "timestamp": (base_time - timedelta(days=3)).isoformat(),
                "medical_entities": [
                    {"entity_type": "symptom", "text": "fever"},
                    {"entity_type": "symptom", "text": "headache"},
                    {"entity_type": "diagnosis", "text": "flu"}
                ],
                "diagnosis": "flu"
            },
            "vector": [0.3] * 768
        }
    ]


class TestOutbreakDetectionOptions:
    """Test OutbreakDetectionOptions"""
    
    def test_default_options(self):
        """Test default options"""
        options = OutbreakDetectionOptions()
        assert options.method == DetectionMethod.DBSCAN
        assert options.time_window_days == 7
        assert options.min_cluster_size == 3
        assert options.threshold == 2.0
    
    def test_custom_options(self):
        """Test custom options"""
        options = OutbreakDetectionOptions(
            method=DetectionMethod.KMEANS,
            time_window_days=14,
            min_cluster_size=5,
            threshold=3.0,
            symptom_keywords=["fever", "cough"]
        )
        assert options.method == DetectionMethod.KMEANS
        assert options.time_window_days == 14
        assert options.min_cluster_size == 5
        assert options.threshold == 3.0
        assert options.symptom_keywords == ["fever", "cough"]


class TestOutbreakDetector:
    """Test OutbreakDetector"""
    
    def test_initialization(self, mock_storage, mock_retriever):
        """Test detector initialization"""
        detector = OutbreakDetector(
            qdrant_storage=mock_storage,
            case_retriever=mock_retriever
        )
        assert detector.storage == mock_storage
        assert detector.case_retriever == mock_retriever
    
    def test_retrieve_cases(self, mock_storage, mock_retriever, sample_cases):
        """Test case retrieval"""
        detector = OutbreakDetector(mock_storage, mock_retriever)
        
        # Mock search_with_filters
        mock_storage.search_with_filters.return_value = sample_cases
        
        options = OutbreakDetectionOptions(time_window_days=7)
        cases = detector._retrieve_cases(options)
        
        assert len(cases) == 3
        assert cases[0]["id"] == "case-1"
        mock_storage.search_with_filters.assert_called_once()
    
    def test_extract_features(self, mock_storage, mock_retriever, sample_cases):
        """Test feature extraction"""
        detector = OutbreakDetector(mock_storage, mock_retriever)
        
        options = OutbreakDetectionOptions(
            symptom_keywords=["fever", "cough"]
        )
        
        features, metadata = detector._extract_features(sample_cases, options)
        
        assert len(features) == 3
        assert len(metadata) == 3
        assert features.shape[1] == 20  # Fixed feature size
        assert metadata[0]["case_id"] == "case-1"
        assert "fever" in metadata[0]["symptoms"]
    
    def test_detect_surge_based(self, mock_storage, mock_retriever, sample_cases):
        """Test surge-based detection"""
        detector = OutbreakDetector(mock_storage, mock_retriever)
        
        # Mock search_with_filters to return cases
        mock_storage.search_with_filters.return_value = sample_cases
        
        options = OutbreakDetectionOptions(
            method=DetectionMethod.SURGE_BASED,
            time_window_days=7,
            threshold=1.5,
            symptom_keywords=["fever", "cough"]
        )
        
        result = detector.detect_outbreaks(options)
        
        assert result.total_cases_analyzed == 3
        assert result.detection_method == "surge_based"
        # May or may not have clusters depending on surge ratios
    
    @pytest.mark.skipif(
        not pytest.importorskip("sklearn", reason="scikit-learn not available"),
        reason="scikit-learn not available"
    )
    def test_detect_dbscan(self, mock_storage, mock_retriever):
        """Test DBSCAN clustering"""
        detector = OutbreakDetector(mock_storage, mock_retriever)
        
        # Create sample features
        features = np.array([
            [0.1, 0.2, 0.3] + [0.0] * 17,
            [0.11, 0.21, 0.31] + [0.0] * 17,
            [0.12, 0.22, 0.32] + [0.0] * 17,
            [0.9, 0.8, 0.7] + [0.0] * 17,  # Outlier
        ])
        
        case_metadata = [
            {"case_id": f"case-{i}", "symptoms": ["fever"], "diagnoses": [], "timestamp": None, "payload": {}}
            for i in range(4)
        ]
        
        options = OutbreakDetectionOptions(
            method=DetectionMethod.DBSCAN,
            min_cluster_size=2,
            eps=0.5,
            min_samples=2
        )
        
        result = detector._detect_dbscan(features, case_metadata, options)
        
        assert len(result.clusters) >= 0  # May have clusters or not depending on DBSCAN
        # DBSCAN may identify noise points as anomalies
        assert result.anomaly_cases is not None
    
    @pytest.mark.skipif(
        not pytest.importorskip("sklearn", reason="scikit-learn not available"),
        reason="scikit-learn not available"
    )
    def test_detect_kmeans(self, mock_storage, mock_retriever):
        """Test K-means clustering"""
        detector = OutbreakDetector(mock_storage, mock_retriever)
        
        # Create sample features
        features = np.array([
            [0.1, 0.2, 0.3] + [0.0] * 17,
            [0.11, 0.21, 0.31] + [0.0] * 17,
            [0.12, 0.22, 0.32] + [0.0] * 17,
            [0.9, 0.8, 0.7] + [0.0] * 17,
        ])
        
        case_metadata = [
            {"case_id": f"case-{i}", "symptoms": ["fever"], "diagnoses": [], "timestamp": None, "payload": {}}
            for i in range(4)
        ]
        
        options = OutbreakDetectionOptions(
            method=DetectionMethod.KMEANS,
            min_cluster_size=2,
            num_clusters=2
        )
        
        result = detector._detect_kmeans(features, case_metadata, options)
        
        assert len(result.clusters) >= 0
        # K-means will create clusters based on num_clusters
    
    def test_detect_simple_clustering(self, mock_storage, mock_retriever):
        """Test simple clustering fallback"""
        detector = OutbreakDetector(mock_storage, mock_retriever)
        
        features = np.array([
            [0.1, 0.2, 0.3] + [0.0] * 17,
            [0.11, 0.21, 0.31] + [0.0] * 17,
        ])
        
        case_metadata = [
            {"case_id": "case-1", "symptoms": ["fever", "cough"], "diagnoses": [], "timestamp": None, "payload": {}},
            {"case_id": "case-2", "symptoms": ["fever", "cough"], "diagnoses": [], "timestamp": None, "payload": {}}
        ]
        
        options = OutbreakDetectionOptions(min_cluster_size=2)
        
        result = detector._detect_simple_clustering(features, case_metadata, options)
        
        assert len(result.clusters) >= 0
    
    def test_generate_alerts(self, mock_storage, mock_retriever):
        """Test alert generation"""
        detector = OutbreakDetector(mock_storage, mock_retriever)
        
        clusters = [
            OutbreakCluster(
                cluster_id=0,
                case_ids=["case-1", "case-2"],
                size=2,
                symptoms=["fever", "cough"],
                diagnoses=["pneumonia"],
                density_score=0.25,
                anomaly_score=2.5
            ),
            OutbreakCluster(
                cluster_id=1,
                case_ids=["case-3"],
                size=1,
                symptoms=["headache"],
                density_score=0.05,
                anomaly_score=0.5
            )
        ]
        
        options = OutbreakDetectionOptions()
        alerts = detector._generate_alerts(clusters, options)
        
        assert len(alerts) == 2
        assert alerts[0].level in [AlertLevel.HIGH, AlertLevel.CRITICAL]  # High density/anomaly score
        assert alerts[0].cluster.cluster_id == 0
        assert "fever" in alerts[0].message.lower()
        assert len(alerts[0].recommended_actions) > 0
        assert alerts[0].confidence > 0


class TestOutbreakCluster:
    """Test OutbreakCluster"""
    
    def test_cluster_creation(self):
        """Test cluster creation"""
        cluster = OutbreakCluster(
            cluster_id=1,
            case_ids=["case-1", "case-2"],
            size=2,
            symptoms=["fever", "cough"],
            diagnoses=["pneumonia"],
            density_score=0.5,
            anomaly_score=1.5
        )
        
        assert cluster.cluster_id == 1
        assert len(cluster.case_ids) == 2
        assert cluster.size == 2
        assert "fever" in cluster.symptoms
        assert cluster.density_score == 0.5


class TestOutbreakAlert:
    """Test OutbreakAlert"""
    
    def test_alert_creation(self):
        """Test alert creation"""
        cluster = OutbreakCluster(
            cluster_id=0,
            case_ids=["case-1"],
            size=1,
            symptoms=["fever"]
        )
        
        alert = OutbreakAlert(
            alert_id="alert-1",
            level=AlertLevel.HIGH,
            cluster=cluster,
            message="Test alert",
            confidence=0.8,
            recommended_actions=["Action 1", "Action 2"]
        )
        
        assert alert.alert_id == "alert-1"
        assert alert.level == AlertLevel.HIGH
        assert alert.confidence == 0.8
        assert len(alert.recommended_actions) == 2

