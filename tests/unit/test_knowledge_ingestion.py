"""
Unit tests for knowledge ingestion pipeline
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.storage.qdrant_storage import QdrantStorage
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
from src.storage.schema_validator import SchemaValidator


class TestKnowledgeIngestionPipeline:
    """Test KnowledgeIngestionPipeline"""
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock QdrantStorage"""
        storage = Mock(spec=QdrantStorage)
        storage.vector_size = 768
        storage.search_with_filters = Mock(return_value=[])
        storage.store_knowledge_base_document = Mock(return_value="test-point-id")
        return storage
    
    @pytest.fixture
    def mock_embedding_generator(self):
        """Create mock embedding generator"""
        def generator(text):
            return [0.1] * 768
        return generator
    
    @pytest.fixture
    def pipeline(self, mock_storage, mock_embedding_generator):
        """Create pipeline instance"""
        return KnowledgeIngestionPipeline(
            qdrant_storage=mock_storage,
            text_embedding_generator=mock_embedding_generator,
            chunk_size=512,
            chunk_overlap=50,
            validate_schema=True
        )
    
    def test_initialization(self, pipeline):
        """Test pipeline initialization"""
        assert pipeline is not None
        assert pipeline.chunk_size == 512
        assert pipeline.chunk_overlap == 50
        assert pipeline.validate_schema is True
        assert pipeline.validator is not None
    
    def test_chunk_text(self, pipeline):
        """Test text chunking"""
        text = "A" * 1000  # 1000 characters
        chunks = pipeline.chunk_text(text)
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("chunk_index" in chunk for chunk in chunks)
        assert chunks[0]["chunk_index"] == 0
    
    def test_chunk_text_with_overlap(self, pipeline):
        """Test chunking with overlap"""
        text = "A" * 1000
        chunks = pipeline.chunk_text(text, chunk_size=200, chunk_overlap=50)
        
        # Should have multiple chunks with overlap
        assert len(chunks) > 1
        # Verify overlap (chunk 1 should start before chunk 0 ends)
        if len(chunks) > 1:
            assert chunks[1]["start"] < chunks[0]["end"]
    
    def test_generate_document_hash(self, pipeline):
        """Test document hash generation"""
        doc1 = {"title": "Test", "text": "Content", "source": "test"}
        doc2 = {"title": "Test", "text": "Content", "source": "test"}
        doc3 = {"title": "Test", "text": "Different", "source": "test"}
        
        hash1 = pipeline.generate_document_hash(doc1)
        hash2 = pipeline.generate_document_hash(doc2)
        hash3 = pipeline.generate_document_hash(doc3)
        
        assert hash1 == hash2  # Same content
        assert hash1 != hash3  # Different content
        assert len(hash1) == 64  # SHA-256 hex digest
    
    def test_ingest_document_success(self, pipeline, mock_storage):
        """Test successful document ingestion"""
        document = {
            "title": "Test Document",
            "text": "This is a test document with some content.",
            "source": "test",
            "domain": "pathology"
        }
        
        point_ids = pipeline.ingest_document(document)
        
        assert len(point_ids) > 0
        assert mock_storage.store_knowledge_base_document.called
    
    def test_ingest_document_with_content_field(self, pipeline, mock_storage):
        """Test ingestion with 'content' field instead of 'text'"""
        document = {
            "title": "Test Document",
            "content": "This is test content.",
            "source": "test"
        }
        
        point_ids = pipeline.ingest_document(document)
        
        assert len(point_ids) > 0
        assert mock_storage.store_knowledge_base_document.called
    
    def test_ingest_document_idempotent(self, pipeline, mock_storage):
        """Test idempotent ingestion (skip duplicates)"""
        document = {
            "title": "Test Document",
            "text": "Test content",
            "source": "test"
        }
        
        # First ingestion - document doesn't exist
        mock_storage.search_with_filters.return_value = []
        point_ids1 = pipeline.ingest_document(document)
        
        # Second ingestion - document exists
        mock_storage.search_with_filters.return_value = [{"id": "existing-id"}]
        point_ids2 = pipeline.ingest_document(document)
        
        assert len(point_ids1) > 0
        assert len(point_ids2) == 1
        assert point_ids2[0] == "existing-id"
    
    def test_ingest_document_force_update(self, pipeline, mock_storage):
        """Test force update even if document exists"""
        document = {
            "title": "Test Document",
            "text": "Test content",
            "source": "test"
        }
        
        # Document exists but force_update=True
        mock_storage.search_with_filters.return_value = [{"id": "existing-id"}]
        point_ids = pipeline.ingest_document(document, force_update=True)
        
        # Should still ingest
        assert len(point_ids) > 0
        assert mock_storage.store_knowledge_base_document.called
    
    def test_ingest_document_with_metadata(self, pipeline, mock_storage):
        """Test ingestion with custom metadata"""
        document = {
            "title": "Test Document",
            "text": "Test content",
            "source": "test"
        }
        
        metadata = KnowledgeBaseMetadata(
            title="Custom Title",
            source="custom_source",
            domain="pharmacology",
            year=2023,
            embedding_type=EmbeddingType.TEXT,
            access_type=AccessType.OPEN
        )
        
        point_ids = pipeline.ingest_document(document, metadata=metadata)
        
        assert len(point_ids) > 0
        # Verify metadata was used
        call_args = mock_storage.store_knowledge_base_document.call_args
        assert call_args is not None
    
    def test_ingest_document_validation_error(self, pipeline):
        """Test ingestion with invalid metadata"""
        document = {
            "title": "",  # Empty title - invalid
            "text": "Test content",
            "source": "test"
        }
        
        with pytest.raises(ValueError, match="Invalid metadata"):
            pipeline.ingest_document(document)
    
    def test_ingest_document_no_text(self, pipeline, mock_storage):
        """Test ingestion with no text content"""
        document = {
            "title": "Test Document",
            "source": "test"
            # No text or content
        }
        
        with pytest.raises(ValueError, match="Invalid document"):
            pipeline.ingest_document(document)
    
    def test_ingest_batch(self, pipeline, mock_storage):
        """Test batch ingestion"""
        documents = [
            {"title": "Doc 1", "text": "Content 1", "source": "test"},
            {"title": "Doc 2", "text": "Content 2", "source": "test"},
            {"title": "Doc 3", "text": "Content 3", "source": "test"}
        ]
        
        mock_storage.search_with_filters.return_value = []
        stats = pipeline.ingest_batch(documents)
        
        assert stats["total"] == 3
        assert stats["ingested"] == 3
        assert stats["skipped"] == 0
        assert stats["errors"] == 0
        assert len(stats["point_ids"]) > 0
    
    def test_ingest_batch_with_errors(self, pipeline, mock_storage):
        """Test batch ingestion with some errors"""
        documents = [
            {"title": "Doc 1", "text": "Content 1", "source": "test"},
            {"title": "", "text": "Content 2", "source": "test"},  # Invalid
            {"title": "Doc 3", "text": "Content 3", "source": "test"}
        ]
        
        mock_storage.search_with_filters.return_value = []
        stats = pipeline.ingest_batch(documents)
        
        assert stats["total"] == 3
        assert stats["errors"] > 0
    
    def test_delta_ingest_new_documents(self, pipeline, mock_storage):
        """Test delta ingestion with new documents"""
        documents = [
            {"title": "Doc 1", "text": "Content 1", "source": "test"},
            {"title": "Doc 2", "text": "Content 2", "source": "test"}
        ]
        
        mock_storage.search_with_filters.return_value = []
        stats = pipeline.delta_ingest(documents)
        
        assert stats["new"] == 2
        assert stats["updated"] == 0
        assert stats["unchanged"] == 0
    
    def test_delta_ingest_updated_documents(self, pipeline, mock_storage):
        """Test delta ingestion with updated documents"""
        documents = [
            {"title": "Doc 1", "text": "Content 1", "source": "test", "updated_at": datetime.now(timezone.utc).isoformat()}
        ]
        
        # Document exists
        mock_storage.search_with_filters.return_value = [{"id": "existing-id"}]
        stats = pipeline.delta_ingest(documents)
        
        assert stats["updated"] == 1
        assert stats["new"] == 0
    
    def test_delta_ingest_unchanged_documents(self, pipeline, mock_storage):
        """Test delta ingestion with unchanged documents"""
        last_ingestion = datetime.now(timezone.utc)
        documents = [
            {
                "title": "Doc 1",
                "text": "Content 1",
                "source": "test",
                "updated_at": (last_ingestion - timedelta(days=1)).isoformat()  # Older
            }
        ]
        
        mock_storage.search_with_filters.return_value = []
        stats = pipeline.delta_ingest(documents, last_ingestion_time=last_ingestion)
        
        assert stats["unchanged"] == 1
        assert stats["new"] == 0
        assert stats["updated"] == 0
    
    def test_ingest_document_embedding_validation(self, pipeline, mock_storage):
        """Test embedding validation during ingestion"""
        # Mock embedding generator that returns wrong dimension
        def bad_generator(text):
            return [0.1] * 384  # Wrong dimension
        
        pipeline.text_embedding_generator = bad_generator
        
        document = {
            "title": "Test Document",
            "text": "Test content",
            "source": "test"
        }
        
        with pytest.raises(ValueError, match="Invalid embedding"):
            pipeline.ingest_document(document)
    
    def test_chunking_validation(self, pipeline):
        """Test chunking parameter validation"""
        # Test with valid chunking
        chunks = pipeline.chunk_text("Test text")
        assert len(chunks) > 0
        
        # Test with custom valid chunking
        chunks = pipeline.chunk_text("Test text", chunk_size=200, chunk_overlap=20)
        assert len(chunks) > 0

