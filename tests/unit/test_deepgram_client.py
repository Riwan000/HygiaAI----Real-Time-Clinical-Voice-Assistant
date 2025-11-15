"""
Unit tests for Deepgram client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.transcription.deepgram_client import DeepgramClient, TranscriptionConfig


class TestTranscriptionConfig:
    """Test TranscriptionConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = TranscriptionConfig()
        assert config.language == "en-US"
        assert config.model == "nova-2"
        assert config.smart_format is True
        assert config.punctuate is True
        assert config.diarize is True
        assert config.interim_results is True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = TranscriptionConfig(
            language="en-GB",
            model="base",
            smart_format=False,
            diarize=False
        )
        assert config.language == "en-GB"
        assert config.model == "base"
        assert config.smart_format is False
        assert config.diarize is False


class TestDeepgramClient:
    """Test DeepgramClient class"""
    
    @patch('src.transcription.deepgram_client.DeepgramClient')
    def test_initialization_with_api_key(self, mock_deepgram):
        """Test client initialization with API key"""
        api_key = "test-api-key"
        client = DeepgramClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.config is not None
    
    @patch('src.transcription.deepgram_client.DeepgramClient')
    def test_initialization_without_api_key(self, mock_deepgram):
        """Test client initialization without API key (uses config)"""
        with patch('src.transcription.deepgram_client.DEEPGRAM_API_KEY', 'config-key'):
            client = DeepgramClient()
            assert client.api_key == 'config-key'
    
    @patch('src.transcription.deepgram_client.DeepgramClient')
    def test_initialization_missing_api_key(self, mock_deepgram):
        """Test client initialization fails when API key is missing"""
        with patch('src.transcription.deepgram_client.DEEPGRAM_API_KEY', None):
            with pytest.raises(ValueError, match="Deepgram API key is required"):
                DeepgramClient()
    
    @patch('src.transcription.deepgram_client.DeepgramClient')
    def test_update_config(self, mock_deepgram):
        """Test configuration update"""
        client = DeepgramClient(api_key="test-key")
        new_config = TranscriptionConfig(model="base", language="en-GB")
        client.update_config(new_config)
        assert client.config.model == "base"
        assert client.config.language == "en-GB"
    
    @patch('src.transcription.deepgram_client.DeepgramClient')
    def test_test_connection_success(self, mock_deepgram):
        """Test successful connection"""
        client = DeepgramClient(api_key="test-key")
        # Mock the connection methods
        mock_connection = MagicMock()
        client.get_live_connection = MagicMock(return_value=mock_connection)
        mock_connection.finish = MagicMock()
        
        result = client.test_connection()
        assert result is True

