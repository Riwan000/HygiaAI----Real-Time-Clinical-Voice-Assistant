"""
Unit tests for Qdrant Storage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.storage.qdrant_storage import QdrantStorage, TranscriptStorage
from src.storage.schema import StorageMetadata, ModalityType
from src.storage.encryption import EncryptionManager, DeIdentificationManager


class TestQdrantStorage:
    """Test QdrantStorage class"""
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_initialization(self, mock_qdrant_client):
        """Test storage initialization"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        
        storage = QdrantStorage(host="localhost", port=6333)
        assert storage.host == "localhost"
        assert storage.port == 6333
        assert storage.collection_name == "hygiaai_transcripts"
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_store_transcript(self, mock_qdrant_client):
        """Test transcript storage"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        mock_client.upsert = Mock()
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        transcript_data = {
            "transcript": "Patient has fever and cough",
            "session_id": "test-session-1",
            "confidence": 0.95
        }
        embedding = [0.1] * 384
        
        point_id = storage.store_transcript(transcript_data, embedding)
        
        assert point_id is not None
        mock_client.upsert.assert_called_once()
    
    @patch('src.storage.qdrant_storage.QdrantClient')
    def test_search_similar(self, mock_qdrant_client):
        """Test similarity search"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.create_collection = Mock()
        
        # Mock search results
        mock_result = Mock()
        mock_result.id = "test-id-1"
        mock_result.score = 0.95
        mock_result.vector = [0.1] * 384
        mock_result.payload = {
            "transcript": "Patient has fever",
            "session_id": "test-session-1"
        }
        
        mock_client.search.return_value = [mock_result]
        
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        
        query_embedding = [0.1] * 384
        results = storage.search_similar(query_embedding, limit=5)
        
        assert len(results) == 1
        assert results[0]["id"] == "test-id-1"
        assert results[0]["score"] == 0.95


class TestEncryptionManager:
    """Test EncryptionManager class"""
    
    def test_initialization(self):
        """Test encryption manager initialization"""
        manager = EncryptionManager()
        assert manager.cipher is not None
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        manager = EncryptionManager()
        
        original = "Patient has fever"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original
    
    def test_encrypt_dict(self):
        """Test dictionary encryption"""
        manager = EncryptionManager()
        
        data = {
            "transcript": "Patient has fever",
            "patient_id": "P12345",
            "other_field": "not encrypted"
        }
        
        encrypted = manager.encrypt_dict(data, ["transcript", "patient_id"])
        
        assert encrypted["transcript"] != data["transcript"]
        assert encrypted["patient_id"] != data["patient_id"]
        assert encrypted["other_field"] == data["other_field"]


class TestDeIdentificationManager:
    """Test DeIdentificationManager class"""
    
    def test_initialization(self):
        """Test de-identification manager initialization"""
        manager = DeIdentificationManager()
        assert manager.patterns is not None
    
    def test_deidentify_text(self):
        """Test text de-identification"""
        manager = DeIdentificationManager()
        
        text = "Patient email: john@example.com, phone: 555-123-4567"
        deidentified = manager.deidentify_text(text)
        
        assert "[REDACTED]" in deidentified
        assert "john@example.com" not in deidentified
        assert "555-123-4567" not in deidentified
    
    def test_hash_patient_id(self):
        """Test patient ID hashing"""
        manager = DeIdentificationManager()
        
        patient_id = "P12345"
        hashed = manager.hash_patient_id(patient_id)
        
        assert hashed != patient_id
        assert len(hashed) == 16
        assert hashed.isalnum()

