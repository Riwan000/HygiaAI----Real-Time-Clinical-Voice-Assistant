"""
Unit tests for re-scan scheduler
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import shutil

from src.collector.scheduler import (
    RescanScheduler,
    ScanMetrics,
    DeltaDetector,
    ScanStateManager,
    DocumentState
)
from src.collector import KnowledgeCollector, MedicalSource
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline


class TestDeltaDetector:
    """Test DeltaDetector"""
    
    def test_compute_document_hash(self):
        """Test document hash computation"""
        detector = DeltaDetector()
        
        doc1 = {"title": "Test", "text": "Content", "source": "test"}
        doc2 = {"title": "Test", "text": "Content", "source": "test"}
        doc3 = {"title": "Test", "text": "Different", "source": "test"}
        
        hash1 = detector.compute_document_hash(doc1)
        hash2 = detector.compute_document_hash(doc2)
        hash3 = detector.compute_document_hash(doc3)
        
        assert hash1 == hash2  # Same content
        assert hash1 != hash3  # Different content
        assert len(hash1) == 64  # SHA-256 hex digest
    
    def test_extract_etag(self):
        """Test ETag extraction"""
        detector = DeltaDetector()
        
        headers1 = {"ETag": '"abc123"'}
        headers2 = {"etag": "xyz789"}
        headers3 = {}
        
        etag1 = detector.extract_etag(headers1)
        etag2 = detector.extract_etag(headers2)
        etag3 = detector.extract_etag(headers3)
        
        assert etag1 == "abc123"
        assert etag2 == "xyz789"
        assert etag3 is None
    
    def test_has_changed_new_document(self):
        """Test change detection for new document"""
        detector = DeltaDetector()
        
        current_hash = "abc123"
        stored_state = None
        
        assert detector.has_changed(current_hash, None, stored_state) is True
    
    def test_has_changed_unchanged_document(self):
        """Test change detection for unchanged document"""
        detector = DeltaDetector()
        
        current_hash = "abc123"
        stored_state = DocumentState(
            url="http://test.com",
            hash="abc123",
            version="1.0"
        )
        
        assert detector.has_changed(current_hash, None, stored_state) is False
    
    def test_has_changed_updated_document(self):
        """Test change detection for updated document"""
        detector = DeltaDetector()
        
        current_hash = "xyz789"
        stored_state = DocumentState(
            url="http://test.com",
            hash="abc123",
            version="1.0"
        )
        
        assert detector.has_changed(current_hash, None, stored_state) is True
    
    def test_increment_version(self):
        """Test version increment"""
        detector = DeltaDetector()
        
        assert detector.increment_version("1.0") == "1.1"
        assert detector.increment_version("1.5") == "1.6"
        assert detector.increment_version("2.0") == "2.1"
        assert detector.increment_version("invalid") == "invalid.1"


class TestScanStateManager:
    """Test ScanStateManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """Create state manager with temp file"""
        state_file = temp_dir / "scan_state.json"
        return ScanStateManager(str(state_file))
    
    def test_initialization(self, state_manager):
        """Test state manager initialization"""
        assert state_manager is not None
        assert len(state_manager.document_states) == 0
        assert len(state_manager.last_scan_times) == 0
    
    def test_update_and_get_document_state(self, state_manager):
        """Test updating and getting document state"""
        url = "http://test.com/doc1"
        
        # Update state
        state_manager.update_document_state(
            url=url,
            hash="abc123",
            etag="etag1",
            version="1.0"
        )
        
        # Get state
        state = state_manager.get_document_state(url)
        assert state is not None
        assert state.url == url
        assert state.hash == "abc123"
        assert state.etag == "etag1"
        assert state.version == "1.0"
    
    def test_update_existing_document_state(self, state_manager):
        """Test updating existing document state"""
        url = "http://test.com/doc1"
        
        # Initial state
        state_manager.update_document_state(url=url, hash="abc123", version="1.0")
        
        # Update state
        state_manager.update_document_state(url=url, hash="xyz789", version="1.1")
        
        # Verify update
        state = state_manager.get_document_state(url)
        assert state.hash == "xyz789"
        assert state.version == "1.1"
    
    def test_save_and_load_state(self, state_manager, temp_dir):
        """Test saving and loading state"""
        url = "http://test.com/doc1"
        
        # Update state
        state_manager.update_document_state(url=url, hash="abc123", version="1.0")
        state_manager.update_last_scan_time("test_source", datetime.now(timezone.utc))
        
        # Save state
        state_manager.save_state()
        
        # Create new manager and load
        state_file = temp_dir / "scan_state.json"
        new_manager = ScanStateManager(str(state_file))
        
        # Verify loaded state
        state = new_manager.get_document_state(url)
        assert state is not None
        assert state.hash == "abc123"
        assert new_manager.get_last_scan_time("test_source") is not None
    
    def test_get_last_scan_time(self, state_manager):
        """Test getting last scan time"""
        source = "test_source"
        scan_time = datetime.now(timezone.utc)
        
        state_manager.update_last_scan_time(source, scan_time)
        
        retrieved = state_manager.get_last_scan_time(source)
        assert retrieved == scan_time


class TestScanMetrics:
    """Test ScanMetrics"""
    
    def test_scan_metrics_creation(self):
        """Test creating scan metrics"""
        metrics = ScanMetrics(
            source="test_source",
            scan_time=datetime.now(timezone.utc),
            total_documents=10,
            added=5,
            updated=3,
            ignored=2,
            errors=0
        )
        
        assert metrics.source == "test_source"
        assert metrics.total_documents == 10
        assert metrics.added == 5
        assert metrics.updated == 3
        assert metrics.ignored == 2
        assert metrics.errors == 0
    
    def test_scan_metrics_to_dict(self):
        """Test converting metrics to dictionary"""
        scan_time = datetime.now(timezone.utc)
        metrics = ScanMetrics(
            source="test_source",
            scan_time=scan_time,
            added=5,
            updated=3
        )
        
        data = metrics.to_dict()
        assert data["source"] == "test_source"
        assert data["added"] == 5
        assert data["updated"] == 3
        assert "scan_time" in data


class TestRescanScheduler:
    """Test RescanScheduler"""
    
    @pytest.fixture
    def mock_collector(self):
        """Create mock collector"""
        collector = Mock(spec=KnowledgeCollector)
        collector.collect_from_source = Mock(return_value=[])
        return collector
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create mock pipeline"""
        pipeline = Mock(spec=KnowledgeIngestionPipeline)
        pipeline.ingest_document = Mock(return_value=["point-id"])
        return pipeline
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def scheduler(self, mock_collector, mock_pipeline, temp_dir):
        """Create scheduler with mocks"""
        state_file = temp_dir / "scan_state.json"
        return RescanScheduler(
            collector=mock_collector,
            ingestion_pipeline=mock_pipeline,
            state_file=str(state_file)
        )
    
    def test_initialization(self, scheduler):
        """Test scheduler initialization"""
        assert scheduler is not None
        assert scheduler.collector is not None
        assert scheduler.ingestion_pipeline is not None
        assert scheduler.state_manager is not None
    
    def test_scan_source_dry_run(self, scheduler, mock_collector):
        """Test scanning source in dry-run mode"""
        from src.collector.web_crawler import CrawlResult
        from src.collector.document_parser import ParsedDocument
        
        # Mock crawl results
        parsed_doc = ParsedDocument(
            url="http://test.com/doc1",
            title="Test Doc",
            content="Test content",
            source="test",
            domain="general"
        )
        
        crawl_result = CrawlResult(
            url="http://test.com/doc1",
            success=True,
            parsed_document=parsed_doc
        )
        
        mock_collector.collect_from_source.return_value = [crawl_result]
        
        # Scan in dry-run mode
        metrics = scheduler.scan_source(MedicalSource.MEDLINEPLUS, dry_run=True)
        
        assert metrics is not None
        assert metrics.total_documents == 1
        # In dry-run, documents are counted but not ingested
        assert metrics.added > 0 or metrics.updated > 0 or metrics.ignored > 0
    
    def test_get_metrics(self, scheduler):
        """Test getting metrics"""
        # Add some metrics
        metrics1 = ScanMetrics(source="test1", scan_time=datetime.now(timezone.utc))
        metrics2 = ScanMetrics(source="test2", scan_time=datetime.now(timezone.utc))
        
        scheduler.scan_metrics = [metrics1, metrics2]
        
        # Get all metrics
        all_metrics = scheduler.get_metrics()
        assert len(all_metrics) == 2
        
        # Get filtered metrics
        filtered = scheduler.get_metrics(source="test1")
        assert len(filtered) == 1
        assert filtered[0].source == "test1"
    
    def test_get_last_scan_time(self, scheduler):
        """Test getting last scan time"""
        source = "test_source"
        scan_time = datetime.now(timezone.utc)
        
        scheduler.state_manager.update_last_scan_time(source, scan_time)
        
        retrieved = scheduler.get_last_scan_time(source)
        assert retrieved == scan_time

