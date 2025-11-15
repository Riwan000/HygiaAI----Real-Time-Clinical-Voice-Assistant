"""
Unit tests for Task 4: Qdrant Vector Store Integration

Tests:
- Multi-vector embeddings (text + image)
- Knowledge base document storage
- Enhanced filtering (range, "in", exact match)
- Hybrid search (semantic + keyword)
- Knowledge ingestion pipeline
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.storage.qdrant_storage import QdrantStorage
from src.storage.schema import (
    KnowledgeBaseMetadata,
    KnowledgeBaseSchema,
    EmbeddingType,
    AccessType,
    StorageMetadata,
    ModalityType,
)
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline


class TestMultiVectorEmbeddings:
    """Test multi-vector embedding storage"""
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_store_multimodal_embedding(self, mock_qdrant_client):
        """Test storing multi-vector embeddings (text + image)"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        mock_client.upsert = Mock()
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        # Test multi-vector storage
        text_embedding = [0.1] * 768
        image_embedding = [0.2] * 512
        data = {"transcript": "Patient has fever", "image_path": "xray.jpg"}
        
        point_id = storage.store_multimodal_embedding(
            data=data,
            text_embedding=text_embedding,
            image_embedding=image_embedding
        )
        
        assert point_id is not None
        mock_client.upsert.assert_called_once()
        
        # Verify named vectors were used
        call_args = mock_client.upsert.call_args
        point = call_args[1]["points"][0]
        assert isinstance(point.vector, dict)
        assert "text" in point.vector
        assert "image" in point.vector
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_store_single_vector_embedding(self, mock_qdrant_client):
        """Test storing single vector embedding (text only)"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        mock_client.upsert = Mock()
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        # Test single vector storage
        text_embedding = [0.1] * 768
        data = {"transcript": "Patient has fever"}
        
        point_id = storage.store_multimodal_embedding(
            data=data,
            text_embedding=text_embedding,
            image_embedding=None
        )
        
        assert point_id is not None
        mock_client.upsert.assert_called_once()
        
        # Verify single vector was used
        call_args = mock_client.upsert.call_args
        point = call_args[1]["points"][0]
        assert isinstance(point.vector, list)


class TestKnowledgeBaseDocuments:
    """Test knowledge base document storage"""
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_store_knowledge_base_document(self, mock_qdrant_client):
        """Test storing knowledge base document"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        mock_client.upsert = Mock()
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        # Test knowledge base document storage
        document_data = {
            "title": "Clinical Guidelines for Fever",
            "text": "Fever is a common symptom...",
            "source": "NCBI Bookshelf",
            "domain": "pathology",
            "year": 2024,
            "provenance_url": "https://example.com/guidelines",
            "version": "1.0"
        }
        
        text_embedding = [0.1] * 768
        image_embedding = [0.2] * 512
        
        point_id = storage.store_knowledge_base_document(
            document_data=document_data,
            text_embedding=text_embedding,
            image_embedding=image_embedding
        )
        
        assert point_id is not None
        mock_client.upsert.assert_called_once()
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_store_knowledge_base_document_with_metadata(self, mock_qdrant_client):
        """Test storing knowledge base document with explicit metadata"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        mock_client.upsert = Mock()
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        document_data = {
            "text": "Clinical guidelines for fever management..."
        }
        
        metadata = KnowledgeBaseMetadata(
            title="Fever Management Guidelines",
            source="PubMed OA",
            domain="pathology",
            year=2024,
            embedding_type=EmbeddingType.TEXT,
            access_type=AccessType.OPEN,
            provenance_url="https://example.com/guidelines",
            version="1.0"
        )
        
        text_embedding = [0.1] * 768
        
        point_id = storage.store_knowledge_base_document(
            document_data=document_data,
            text_embedding=text_embedding,
            image_embedding=None,
            metadata=metadata
        )
        
        assert point_id is not None
        mock_client.upsert.assert_called_once()


class TestEnhancedFiltering:
    """Test enhanced filtering capabilities"""
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_search_with_range_filters(self, mock_qdrant_client):
        """Test search with range filters (gte, lte, gt, lt)"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        
        # Mock search results
        mock_result = Mock()
        mock_result.id = "test-id-1"
        mock_result.score = 0.95
        mock_result.payload = {"age": 35, "year": 2024}
        mock_client.search.return_value = [mock_result]
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        query_embedding = [0.1] * 384
        filters = {
            "age": {"gte": 30, "lte": 50},
            "year": {"gte": 2020}
        }
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=filters,
            limit=5
        )
        
        assert len(results) == 1
        assert results[0]["id"] == "test-id-1"
        mock_client.search.assert_called_once()
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_search_with_in_filters(self, mock_qdrant_client):
        """Test search with 'in' filters for list values"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        
        # Mock search results
        mock_result = Mock()
        mock_result.id = "test-id-1"
        mock_result.score = 0.95
        mock_result.payload = {"domain": "pathology", "source": "NCBI Bookshelf"}
        mock_client.search.return_value = [mock_result]
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        query_embedding = [0.1] * 384
        filters = {
            "domain": {"in": ["pathology", "pharmacology"]},
            "source": "NCBI Bookshelf"
        }
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=filters,
            limit=5
        )
        
        assert len(results) == 1
        mock_client.search.assert_called_once()
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_search_with_exact_match_filters(self, mock_qdrant_client):
        """Test search with exact match filters"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        
        # Mock search results
        mock_result = Mock()
        mock_result.id = "test-id-1"
        mock_result.score = 0.95
        mock_result.payload = {"access_type": "open", "domain": "pathology"}
        mock_client.search.return_value = [mock_result]
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        query_embedding = [0.1] * 384
        filters = {
            "access_type": "open",
            "domain": "pathology"
        }
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=filters,
            limit=5
        )
        
        assert len(results) == 1
        mock_client.search.assert_called_once()
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_search_with_multi_vector(self, mock_qdrant_client):
        """Test search with multi-vector (specify vector name)"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        
        # Mock search results
        mock_result = Mock()
        mock_result.id = "test-id-1"
        mock_result.score = 0.95
        mock_result.payload = {}
        mock_client.search.return_value = [mock_result]
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        query_embedding = [0.1] * 384
        
        results = storage.search_with_filters(
            query_embedding=query_embedding,
            filters=None,
            limit=5,
            vector_name="text"  # Search in text vector
        )
        
        assert len(results) == 1
        mock_client.search.assert_called_once()
        
        # Verify vector name was used
        call_args = mock_client.search.call_args
        assert call_args[1]["query_vector"][0] == "text"


class TestHybridSearch:
    """Test hybrid search (semantic + keyword)"""
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_hybrid_search(self, mock_qdrant_client):
        """Test hybrid search combining semantic and keyword search"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        
        # Mock search results
        mock_result1 = Mock()
        mock_result1.id = "test-id-1"
        mock_result1.score = 0.95
        mock_result1.payload = {"text": "Patient has fever and cough"}
        
        mock_result2 = Mock()
        mock_result2.id = "test-id-2"
        mock_result2.score = 0.85
        mock_result2.payload = {"text": "Fever is a common symptom"}
        
        mock_client.search.return_value = [mock_result1, mock_result2]
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        query_text = "fever cough"
        query_embedding = [0.1] * 384
        
        results = storage.hybrid_search(
            query_text=query_text,
            query_embedding=query_embedding,
            limit=5
        )
        
        assert len(results) > 0
        # Verify combined scores are present
        assert "semantic_score" in results[0]
        assert "keyword_score" in results[0]
        assert "combined_score" in results[0]
        # Results should be sorted by combined_score
        assert results[0]["combined_score"] >= results[1]["combined_score"] if len(results) > 1 else True
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_hybrid_search_with_filters(self, mock_qdrant_client):
        """Test hybrid search with keyword filters"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        
        # Mock search results
        mock_result = Mock()
        mock_result.id = "test-id-1"
        mock_result.score = 0.95
        mock_result.payload = {"text": "Fever guidelines", "domain": "pathology"}
        mock_client.search.return_value = [mock_result]
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        query_text = "fever"
        query_embedding = [0.1] * 384
        keyword_filters = {"domain": "pathology"}
        
        results = storage.hybrid_search(
            query_text=query_text,
            query_embedding=query_embedding,
            keyword_filters=keyword_filters,
            limit=5
        )
        
        assert len(results) > 0
        mock_client.search.assert_called_once()


class TestKnowledgeIngestionPipeline:
    """Test knowledge ingestion pipeline"""
    
    def test_chunk_text(self):
        """Test text chunking"""
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=Mock(),
            chunk_size=100,
            chunk_overlap=20
        )
        
        text = "A" * 250  # 250 characters
        chunks = pipeline.chunk_text(text)
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("chunk_index" in chunk for chunk in chunks)
        assert all("start" in chunk for chunk in chunks)
        assert all("end" in chunk for chunk in chunks)
    
    def test_generate_document_hash(self):
        """Test document hash generation"""
        pipeline = KnowledgeIngestionPipeline(qdrant_storage=Mock())
        
        doc1 = {
            "title": "Test Document",
            "text": "Test content",
            "source": "Test Source"
        }
        
        doc2 = {
            "title": "Test Document",
            "text": "Test content",
            "source": "Test Source"
        }
        
        doc3 = {
            "title": "Different Document",
            "text": "Different content",
            "source": "Test Source"
        }
        
        hash1 = pipeline.generate_document_hash(doc1)
        hash2 = pipeline.generate_document_hash(doc2)
        hash3 = pipeline.generate_document_hash(doc3)
        
        # Same documents should have same hash
        assert hash1 == hash2
        # Different documents should have different hash
        assert hash1 != hash3
    
    @patch('src.storage.knowledge_ingestion.QdrantStorage')
    def test_ingest_document(self, mock_storage_class):
        """Test document ingestion"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        mock_storage.search_with_filters.return_value = []  # No existing document
        mock_storage.store_knowledge_base_document.return_value = "test-point-id"
        
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=mock_storage,
            text_embedding_generator=lambda x: [0.1] * 768,
            chunk_size=100,
            chunk_overlap=20
        )
        
        document = {
            "title": "Test Document",
            "text": "A" * 250,  # 250 characters (will be chunked)
            "source": "Test Source",
            "domain": "pathology",
            "year": 2024
        }
        
        point_ids = pipeline.ingest_document(document)
        
        assert len(point_ids) > 0
        assert all(isinstance(pid, str) for pid in point_ids)
        # Verify storage was called for each chunk
        assert mock_storage.store_knowledge_base_document.call_count == len(point_ids)
    
    @patch('src.storage.knowledge_ingestion.QdrantStorage')
    def test_ingest_document_idempotent(self, mock_storage_class):
        """Test idempotent document ingestion (skip if exists)"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        # Mock existing document
        existing_doc = Mock()
        existing_doc.id = "existing-id"
        mock_storage.search_with_filters.return_value = [{"id": "existing-id"}]
        
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=mock_storage,
            text_embedding_generator=lambda x: [0.1] * 768
        )
        
        document = {
            "title": "Test Document",
            "text": "Test content",
            "source": "Test Source"
        }
        
        point_ids = pipeline.ingest_document(document, force_update=False)
        
        # Should return existing ID without storing
        assert len(point_ids) == 1
        assert point_ids[0] == "existing-id"
        # Should not call store_knowledge_base_document
        mock_storage.store_knowledge_base_document.assert_not_called()
    
    @patch('src.storage.knowledge_ingestion.QdrantStorage')
    def test_ingest_batch(self, mock_storage_class):
        """Test batch document ingestion"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        mock_storage.search_with_filters.return_value = []
        mock_storage.store_knowledge_base_document.return_value = "test-point-id"
        
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=mock_storage,
            text_embedding_generator=lambda x: [0.1] * 768
        )
        
        documents = [
            {"title": "Doc 1", "text": "Content 1", "source": "Source 1"},
            {"title": "Doc 2", "text": "Content 2", "source": "Source 2"},
            {"title": "Doc 3", "text": "Content 3", "source": "Source 3"}
        ]
        
        stats = pipeline.ingest_batch(documents)
        
        assert stats["total"] == 3
        assert stats["ingested"] == 3
        assert stats["skipped"] == 0
        assert stats["errors"] == 0
        assert len(stats["point_ids"]) > 0
    
    @patch('src.storage.knowledge_ingestion.QdrantStorage')
    def test_delta_ingest(self, mock_storage_class):
        """Test delta ingestion (only new/updated documents)"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        mock_storage.store_knowledge_base_document.return_value = "test-point-id"
        
        pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=mock_storage,
            text_embedding_generator=lambda x: [0.1] * 768
        )
        
        # Generate hashes for documents
        doc1 = {"title": "Doc 1", "text": "Content 1", "source": "Source 1"}
        doc2 = {"title": "Doc 2", "text": "Content 2", "source": "Source 2"}
        hash1 = pipeline.generate_document_hash(doc1)
        hash2 = pipeline.generate_document_hash(doc2)
        
        # Mock: first doc exists, second is new
        def mock_search(query_embedding, filters=None, **kwargs):
            if filters and filters.get("doc_hash") == hash1:
                return [{"id": "existing-id"}]
            return []
        
        mock_storage.search_with_filters.side_effect = mock_search
        
        documents = [doc1, doc2]
        
        stats = pipeline.delta_ingest(documents)
        
        assert stats["total"] == 2
        # First doc exists (will be marked as updated since we force_update=True)
        assert stats["updated"] == 1
        # Second doc is new
        assert stats["new"] == 1
        assert stats["unchanged"] == 0  # No unchanged since we don't check updated_at
        assert stats["errors"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

