"""
Unit tests for Temporal Trend Analysis Module

Tests:
- Trend data aggregation
- Symptom trend analysis
- Diagnosis trend analysis
- Outcome trend analysis
- Outbreak detection
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone

from src.visualization.temporal_trends import (
    TemporalTrendAnalyzer,
    TrendData,
    TrendDataPoint,
    TrendOptions,
    TrendGranularity
)
from src.storage import QdrantStorage
from src.retrieval import CaseRetriever


class TestTrendOptions:
    """Test TrendOptions dataclass"""
    
    def test_default_options(self):
        """Test default trend options"""
        options = TrendOptions()
        
        assert options.start_date is None
        assert options.end_date is None
        assert options.granularity == TrendGranularity.DAILY
        assert options.filters is None
        assert "symptoms" in options.metrics
        assert "diagnoses" in options.metrics
        assert "outcomes" in options.metrics
    
    def test_custom_options(self):
        """Test custom trend options"""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        options = TrendOptions(
            start_date=start_date,
            end_date=end_date,
            granularity=TrendGranularity.WEEKLY,
            filters={"age_group": "adult"},
            metrics=["symptoms", "diagnoses"]
        )
        
        assert options.start_date == start_date
        assert options.end_date == end_date
        assert options.granularity == TrendGranularity.WEEKLY
        assert options.filters == {"age_group": "adult"}
        assert len(options.metrics) == 2


class TestTemporalTrendAnalyzer:
    """Test TemporalTrendAnalyzer class"""
    
    @patch('src.visualization.temporal_trends.QdrantStorage')
    def test_initialization(self, mock_storage_class):
        """Test trend analyzer initialization"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        analyzer = TemporalTrendAnalyzer(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        assert analyzer.storage == mock_storage
        assert analyzer.case_retriever is None
    
    @patch('src.visualization.temporal_trends.QdrantStorage')
    def test_query_cases_in_range(self, mock_storage_class):
        """Test querying cases within time range"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        mock_storage.search_with_filters.return_value = [
            {
                "id": "case-1",
                "payload": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "symptoms": ["fever", "cough"]
                }
            }
        ]
        
        analyzer = TemporalTrendAnalyzer(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        options = TrendOptions(
            start_date=start_date,
            end_date=end_date,
            granularity=TrendGranularity.DAILY
        )
        
        cases = analyzer._query_cases_in_range(options)
        
        assert len(cases) == 1
        assert cases[0]["id"] == "case-1"
        mock_storage.search_with_filters.assert_called_once()
    
    @patch('src.visualization.temporal_trends.QdrantStorage')
    def test_round_to_period_daily(self, mock_storage_class):
        """Test rounding timestamp to daily period"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        analyzer = TemporalTrendAnalyzer(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        rounded = analyzer._round_to_period(timestamp, TrendGranularity.DAILY)
        
        assert rounded.hour == 0
        assert rounded.minute == 0
        assert rounded.second == 0
        assert rounded.day == 15
    
    @patch('src.visualization.temporal_trends.QdrantStorage')
    def test_round_to_period_weekly(self, mock_storage_class):
        """Test rounding timestamp to weekly period"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        analyzer = TemporalTrendAnalyzer(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        # Wednesday, Jan 15, 2024
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        rounded = analyzer._round_to_period(timestamp, TrendGranularity.WEEKLY)
        
        # Should round to Monday (Jan 13, 2024)
        assert rounded.weekday() == 0  # Monday
        assert rounded.hour == 0
    
    @patch('src.visualization.temporal_trends.QdrantStorage')
    def test_calculate_summary(self, mock_storage_class):
        """Test summary calculation"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        analyzer = TemporalTrendAnalyzer(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        data_points = [
            TrendDataPoint(
                timestamp=datetime.now(timezone.utc),
                value=10.0,
                count=5
            ),
            TrendDataPoint(
                timestamp=datetime.now(timezone.utc),
                value=20.0,
                count=10
            ),
            TrendDataPoint(
                timestamp=datetime.now(timezone.utc),
                value=15.0,
                count=7
            )
        ]
        
        summary = analyzer._calculate_summary(data_points)
        
        assert summary["total_points"] == 3
        assert summary["min_value"] == 10.0
        assert summary["max_value"] == 20.0
        assert summary["avg_value"] == 15.0
        assert summary["total_count"] == 22
        assert summary["avg_count"] == pytest.approx(7.33, rel=0.1)
    
    @patch('src.visualization.temporal_trends.QdrantStorage')
    def test_analyze_symptom_trends(self, mock_storage_class):
        """Test symptom trend analysis"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        mock_storage.search_with_filters.return_value = [
            {
                "id": "case-1",
                "payload": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "medical_entities": [
                        {"text": "fever", "entity_type": "symptom"},
                        {"text": "cough", "entity_type": "symptom"}
                    ]
                }
            }
        ]
        
        analyzer = TemporalTrendAnalyzer(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        options = TrendOptions(
            granularity=TrendGranularity.DAILY
        )
        
        trend_data = analyzer.analyze_symptom_trends(options)
        
        assert trend_data.metric_name == "symptom_trends"
        assert trend_data.granularity == "daily"
        assert len(trend_data.data_points) > 0
        assert "summary" in trend_data.to_dict()
    
    @patch('src.visualization.temporal_trends.QdrantStorage')
    def test_detect_outbreak_signals(self, mock_storage_class):
        """Test outbreak detection"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        # Mock recent cases with fever
        recent_cases = [
            {
                "id": f"case-{i}",
                "payload": {
                    "timestamp": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
                    "medical_entities": [
                        {"text": "fever", "entity_type": "symptom"}
                    ]
                }
            }
            for i in range(10)
        ]
        
        # Mock baseline cases (fewer)
        baseline_cases = [
            {
                "id": f"baseline-{i}",
                "payload": {
                    "timestamp": (datetime.now(timezone.utc) - timedelta(days=10+i)).isoformat(),
                    "medical_entities": [
                        {"text": "fever", "entity_type": "symptom"}
                    ]
                }
            }
            for i in range(2)
        ]
        
        def mock_search(filters=None, **kwargs):
            if filters and "timestamp" in filters:
                # Check if it's recent or baseline
                if "gte" in filters.get("timestamp", {}):
                    return recent_cases
                else:
                    return baseline_cases
            return []
        
        mock_storage.search_with_filters.side_effect = mock_search
        
        analyzer = TemporalTrendAnalyzer(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        signals = analyzer.detect_outbreak_signals(
            symptom_keywords=["fever"],
            time_window_days=7,
            threshold=2.0
        )
        
        assert "signals" in signals
        assert "alert_count" in signals
        assert signals["time_window_days"] == 7
        assert signals["threshold"] == 2.0


class TestTrendData:
    """Test TrendData dataclass"""
    
    def test_to_dict(self):
        """Test converting trend data to dictionary"""
        data_point = TrendDataPoint(
            timestamp=datetime.now(timezone.utc),
            value=10.0,
            count=5,
            metadata={"test": "value"}
        )
        
        trend_data = TrendData(
            metric_name="test_metric",
            granularity="daily",
            data_points=[data_point],
            summary={"total": 1},
            metadata={"test": "metadata"}
        )
        
        trend_dict = trend_data.to_dict()
        
        assert trend_dict["metric_name"] == "test_metric"
        assert trend_dict["granularity"] == "daily"
        assert len(trend_dict["data_points"]) == 1
        assert trend_dict["summary"]["total"] == 1
        assert trend_dict["metadata"]["test"] == "metadata"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

