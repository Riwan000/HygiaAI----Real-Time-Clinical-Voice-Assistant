"""
Streaming Manager for Real-Time Audio Transcription

Handles:
- Dynamic streaming settings based on network conditions
- Audio buffering mechanisms
- Network quality detection
- Adaptive configuration
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, AsyncIterator, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class NetworkQuality(Enum):
    """Network quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class StreamingMetrics:
    """Metrics for streaming performance"""
    latency: float = 0.0  # Average latency in seconds
    packet_loss: float = 0.0  # Packet loss percentage
    throughput: float = 0.0  # Throughput in bytes/second
    buffer_size: int = 0  # Current buffer size
    network_quality: NetworkQuality = NetworkQuality.GOOD
    last_update: float = field(default_factory=time.time)


@dataclass
class AdaptiveStreamingConfig:
    """Adaptive streaming configuration"""
    # Buffer settings
    min_buffer_size: int = 1024  # Minimum buffer size in bytes
    max_buffer_size: int = 8192  # Maximum buffer size in bytes
    initial_buffer_size: int = 4096  # Initial buffer size
    
    # Network adaptation
    latency_threshold_good: float = 0.1  # 100ms - good quality
    latency_threshold_fair: float = 0.3  # 300ms - fair quality
    latency_threshold_poor: float = 0.5  # 500ms - poor quality
    
    # Audio quality settings
    enable_adaptive_quality: bool = True
    quality_adjustment_interval: float = 2.0  # Adjust every 2 seconds
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 0.5  # Seconds between retries


class StreamingManager:
    """
    Manages real-time audio streaming with adaptive configuration
    
    Features:
    - Dynamic buffering based on network conditions
    - Network quality detection
    - Adaptive streaming settings
    - Seamless transcription experience
    """
    
    def __init__(self, config: Optional[AdaptiveStreamingConfig] = None):
        """
        Initialize streaming manager
        
        Args:
            config: Adaptive streaming configuration
        """
        self.config = config or AdaptiveStreamingConfig()
        self.metrics = StreamingMetrics()
        self.buffer = deque(maxlen=self.config.max_buffer_size)
        self.audio_chunks = deque()
        self.is_streaming = False
        self.last_quality_check = time.time()
        
    def update_metrics(
        self,
        latency: Optional[float] = None,
        packet_loss: Optional[float] = None,
        throughput: Optional[float] = None
    ):
        """
        Update streaming metrics
        
        Args:
            latency: Current latency in seconds
            packet_loss: Packet loss percentage
            throughput: Throughput in bytes/second
        """
        if latency is not None:
            # Exponential moving average for latency
            alpha = 0.3
            self.metrics.latency = (
                alpha * latency + (1 - alpha) * self.metrics.latency
            )
        
        if packet_loss is not None:
            self.metrics.packet_loss = packet_loss
        
        if throughput is not None:
            self.metrics.throughput = throughput
        
        # Update network quality based on latency
        if self.metrics.latency < self.config.latency_threshold_good:
            self.metrics.network_quality = NetworkQuality.EXCELLENT
        elif self.metrics.latency < self.config.latency_threshold_fair:
            self.metrics.network_quality = NetworkQuality.GOOD
        elif self.metrics.latency < self.config.latency_threshold_poor:
            self.metrics.network_quality = NetworkQuality.FAIR
        else:
            self.metrics.network_quality = NetworkQuality.POOR
        
        self.metrics.last_update = time.time()
        logger.debug(
            f"Metrics updated: latency={self.metrics.latency:.3f}s, "
            f"quality={self.metrics.network_quality.value}"
        )
    
    def get_adaptive_buffer_size(self) -> int:
        """
        Get adaptive buffer size based on network quality
        
        Returns:
            Recommended buffer size in bytes
        """
        if not self.config.enable_adaptive_quality:
            return self.config.initial_buffer_size
        
        # Adjust buffer size based on network quality
        quality_multipliers = {
            NetworkQuality.EXCELLENT: 0.5,  # Smaller buffer for low latency
            NetworkQuality.GOOD: 1.0,       # Standard buffer
            NetworkQuality.FAIR: 1.5,       # Larger buffer for stability
            NetworkQuality.POOR: 2.0,       # Maximum buffer for poor network
        }
        
        multiplier = quality_multipliers.get(
            self.metrics.network_quality,
            1.0
        )
        
        buffer_size = int(
            self.config.initial_buffer_size * multiplier
        )
        
        # Clamp to min/max
        buffer_size = max(
            self.config.min_buffer_size,
            min(buffer_size, self.config.max_buffer_size)
        )
        
        return buffer_size
    
    async def buffer_audio_chunk(self, chunk: bytes):
        """
        Buffer an audio chunk with adaptive buffering
        
        Args:
            chunk: Audio data chunk
        """
        self.audio_chunks.append({
            "data": chunk,
            "timestamp": time.time(),
        })
        
        # Maintain buffer size based on network quality
        target_buffer_size = self.get_adaptive_buffer_size()
        while len(self.audio_chunks) > target_buffer_size // len(chunk) if chunk else 0:
            self.audio_chunks.popleft()
    
    async def get_buffered_chunks(self) -> AsyncIterator[bytes]:
        """
        Get buffered audio chunks
        
        Yields:
            Audio data chunks
        """
        while self.audio_chunks or self.is_streaming:
            if self.audio_chunks:
                chunk_data = self.audio_chunks.popleft()
                yield chunk_data["data"]
            else:
                # Wait a bit if buffer is empty but streaming is active
                await asyncio.sleep(0.01)
    
    def should_adjust_quality(self) -> bool:
        """
        Check if quality should be adjusted
        
        Returns:
            True if quality adjustment is needed
        """
        elapsed = time.time() - self.last_quality_check
        return elapsed >= self.config.quality_adjustment_interval
    
    def get_adaptive_settings(self) -> Dict[str, Any]:
        """
        Get adaptive streaming settings based on current metrics
        
        Returns:
            Dictionary of adaptive settings
        """
        settings = {
            "buffer_size": self.get_adaptive_buffer_size(),
            "network_quality": self.metrics.network_quality.value,
            "latency": self.metrics.latency,
            "packet_loss": self.metrics.packet_loss,
        }
        
        # Adjust settings based on network quality
        if self.metrics.network_quality == NetworkQuality.POOR:
            # Reduce quality for poor network
            settings["enable_interim_results"] = False  # Reduce data transfer
            settings["chunk_size"] = 4096  # Larger chunks
        elif self.metrics.network_quality == NetworkQuality.EXCELLENT:
            # Increase quality for excellent network
            settings["enable_interim_results"] = True
            settings["chunk_size"] = 1024  # Smaller chunks for lower latency
        else:
            # Standard settings
            settings["enable_interim_results"] = True
            settings["chunk_size"] = 2048
        
        return settings
    
    def start_streaming(self):
        """Start streaming session"""
        self.is_streaming = True
        self.audio_chunks.clear()
        self.metrics = StreamingMetrics()
        logger.info("Streaming session started")
    
    def stop_streaming(self):
        """Stop streaming session"""
        self.is_streaming = False
        logger.info("Streaming session stopped")
    
    def get_metrics(self) -> StreamingMetrics:
        """Get current streaming metrics"""
        return self.metrics

