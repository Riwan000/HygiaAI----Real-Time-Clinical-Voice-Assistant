"""
Real-Time Medical Transcription Module
Handles live audio transcription using Deepgram API
"""

from .deepgram_client import DeepgramClient, TranscriptionConfig
from .streaming_manager import StreamingManager, AdaptiveStreamingConfig, NetworkQuality
from .error_handler import (
    ErrorHandler,
    FallbackHandler,
    ErrorType,
    ErrorSeverity,
    TranscriptionError,
    RetryConfig
)

__all__ = [
    "DeepgramClient",
    "TranscriptionConfig",
    "StreamingManager",
    "AdaptiveStreamingConfig",
    "NetworkQuality",
    "ErrorHandler",
    "FallbackHandler",
    "ErrorType",
    "ErrorSeverity",
    "TranscriptionError",
    "RetryConfig",
]

