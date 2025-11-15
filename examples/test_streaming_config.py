"""
Example: Testing Real-Time Streaming Configuration

Demonstrates:
- Adaptive streaming settings
- Network quality detection
- Buffering mechanisms
- Dynamic configuration adjustment
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.transcription.streaming_manager import (
    StreamingManager,
    AdaptiveStreamingConfig,
    NetworkQuality
)
from src.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")


async def simulate_audio_stream():
    """Simulate an audio stream for testing"""
    for i in range(10):
        # Simulate audio chunk
        chunk = b"audio_chunk_" + str(i).encode()
        yield chunk
        await asyncio.sleep(0.1)  # Simulate 100ms between chunks


async def test_streaming_configuration():
    """Test streaming configuration with different network conditions"""
    print("=" * 60)
    print("Testing Real-Time Streaming Configuration")
    print("=" * 60)
    print()
    
    # Initialize streaming manager
    config = AdaptiveStreamingConfig(
        min_buffer_size=1024,
        max_buffer_size=8192,
        initial_buffer_size=4096,
        enable_adaptive_quality=True
    )
    manager = StreamingManager(config)
    
    print("✓ Streaming Manager initialized")
    print(f"  Initial buffer size: {config.initial_buffer_size} bytes")
    print()
    
    # Test 1: Excellent network quality
    print("Test 1: Excellent Network Quality")
    print("-" * 60)
    manager.update_metrics(latency=0.05, packet_loss=0.0, throughput=5000.0)
    metrics = manager.get_metrics()
    settings = manager.get_adaptive_settings()
    
    print(f"  Latency: {metrics.latency:.3f}s")
    print(f"  Network Quality: {metrics.network_quality.value}")
    print(f"  Adaptive Buffer Size: {settings['buffer_size']} bytes")
    print(f"  Chunk Size: {settings['chunk_size']} bytes")
    print(f"  Interim Results: {settings['enable_interim_results']}")
    print()
    
    # Test 2: Poor network quality
    print("Test 2: Poor Network Quality")
    print("-" * 60)
    manager.update_metrics(latency=0.6, packet_loss=0.1, throughput=500.0)
    metrics = manager.get_metrics()
    settings = manager.get_adaptive_settings()
    
    print(f"  Latency: {metrics.latency:.3f}s")
    print(f"  Network Quality: {metrics.network_quality.value}")
    print(f"  Adaptive Buffer Size: {settings['buffer_size']} bytes")
    print(f"  Chunk Size: {settings['chunk_size']} bytes")
    print(f"  Interim Results: {settings['enable_interim_results']}")
    print()
    
    # Test 3: Buffering simulation
    print("Test 3: Audio Buffering Simulation")
    print("-" * 60)
    manager.start_streaming()
    
    async for chunk in simulate_audio_stream():
        await manager.buffer_audio_chunk(chunk)
        buffer_size = len(manager.audio_chunks)
        print(f"  Buffered chunk, buffer size: {buffer_size}")
    
    manager.stop_streaming()
    print("  ✓ Streaming session completed")
    print()
    
    # Test 4: Network quality transitions
    print("Test 4: Network Quality Transitions")
    print("-" * 60)
    latencies = [0.05, 0.15, 0.35, 0.6, 0.35, 0.15, 0.05]
    for latency in latencies:
        manager.update_metrics(latency=latency)
        metrics = manager.get_metrics()
        settings = manager.get_adaptive_settings()
        print(
            f"  Latency: {latency:.2f}s -> "
            f"Quality: {metrics.network_quality.value}, "
            f"Buffer: {settings['buffer_size']} bytes"
        )
    print()
    
    print("=" * 60)
    print("✅ All streaming configuration tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_streaming_configuration())

