"""
Unit tests for Streaming Manager
"""

import pytest
import asyncio
from src.transcription.streaming_manager import (
    StreamingManager,
    AdaptiveStreamingConfig,
    NetworkQuality
)


class TestAdaptiveStreamingConfig:
    """Test AdaptiveStreamingConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = AdaptiveStreamingConfig()
        assert config.min_buffer_size == 1024
        assert config.max_buffer_size == 8192
        assert config.initial_buffer_size == 4096
        assert config.enable_adaptive_quality is True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = AdaptiveStreamingConfig(
            min_buffer_size=2048,
            max_buffer_size=16384,
            enable_adaptive_quality=False
        )
        assert config.min_buffer_size == 2048
        assert config.max_buffer_size == 16384
        assert config.enable_adaptive_quality is False


class TestStreamingManager:
    """Test StreamingManager"""
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = StreamingManager()
        assert manager.config is not None
        assert manager.metrics is not None
        assert manager.is_streaming is False
    
    def test_update_metrics(self):
        """Test metrics update"""
        manager = StreamingManager()
        manager.update_metrics(latency=0.05, packet_loss=0.0, throughput=1000.0)
        
        # Latency uses EMA, so it won't be exactly 0.05 on first update
        assert manager.metrics.latency > 0  # Should be positive
        assert manager.metrics.packet_loss == 0.0
        assert manager.metrics.throughput == 1000.0
        assert manager.metrics.network_quality == NetworkQuality.EXCELLENT
    
    def test_network_quality_detection(self):
        """Test network quality detection based on latency"""
        manager = StreamingManager()
        
        # Excellent quality - update multiple times to overcome EMA smoothing
        for _ in range(10):
            manager.update_metrics(latency=0.05)
        assert manager.metrics.network_quality == NetworkQuality.EXCELLENT
        
        # Good quality
        for _ in range(10):
            manager.update_metrics(latency=0.15)
        assert manager.metrics.network_quality == NetworkQuality.GOOD
        
        # Fair quality
        for _ in range(10):
            manager.update_metrics(latency=0.35)
        assert manager.metrics.network_quality == NetworkQuality.FAIR
        
        # Poor quality
        for _ in range(10):
            manager.update_metrics(latency=0.6)
        assert manager.metrics.network_quality == NetworkQuality.POOR
    
    def test_get_adaptive_buffer_size(self):
        """Test adaptive buffer size calculation"""
        manager = StreamingManager()
        
        # Excellent quality - smaller buffer
        for _ in range(10):
            manager.update_metrics(latency=0.05)
        buffer_size = manager.get_adaptive_buffer_size()
        assert buffer_size <= manager.config.initial_buffer_size
        
        # Poor quality - larger buffer
        for _ in range(10):
            manager.update_metrics(latency=0.6)
        buffer_size = manager.get_adaptive_buffer_size()
        assert buffer_size >= manager.config.initial_buffer_size
    
    @pytest.mark.asyncio
    async def test_buffer_audio_chunk(self):
        """Test audio chunk buffering"""
        manager = StreamingManager()
        chunk = b"test audio data"
        
        await manager.buffer_audio_chunk(chunk)
        assert len(manager.audio_chunks) > 0
    
    def test_start_stop_streaming(self):
        """Test streaming session management"""
        manager = StreamingManager()
        
        assert manager.is_streaming is False
        manager.start_streaming()
        assert manager.is_streaming is True
        
        manager.stop_streaming()
        assert manager.is_streaming is False
    
    def test_get_adaptive_settings(self):
        """Test adaptive settings generation"""
        manager = StreamingManager()
        
        # Excellent quality - update multiple times to overcome EMA
        for _ in range(10):
            manager.update_metrics(latency=0.05)
        settings = manager.get_adaptive_settings()
        assert settings["network_quality"] == NetworkQuality.EXCELLENT.value
        assert settings["enable_interim_results"] is True
        assert settings["chunk_size"] == 1024
        
        # Poor quality - update multiple times to overcome EMA
        for _ in range(10):
            manager.update_metrics(latency=0.6)
        settings = manager.get_adaptive_settings()
        assert settings["network_quality"] == NetworkQuality.POOR.value
        assert settings["enable_interim_results"] is False
        assert settings["chunk_size"] == 4096

