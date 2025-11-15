"""
Unit tests for Error Handler
"""

import pytest
import asyncio
from src.transcription.error_handler import (
    ErrorHandler,
    FallbackHandler,
    ErrorType,
    ErrorSeverity,
    TranscriptionError,
    RetryConfig
)


class TestErrorHandler:
    """Test ErrorHandler class"""
    
    def test_initialization(self):
        """Test error handler initialization"""
        handler = ErrorHandler()
        assert handler.retry_config is not None
        assert len(handler.error_log) == 0
        assert len(handler.error_stats) == 0
    
    def test_classify_network_error(self):
        """Test network error classification"""
        handler = ErrorHandler()
        error = Exception("Connection timeout")
        classified = handler.classify_error(error)
        
        assert classified.error_type == ErrorType.NETWORK_ERROR
        assert classified.severity == ErrorSeverity.MEDIUM
    
    def test_classify_auth_error(self):
        """Test authentication error classification"""
        handler = ErrorHandler()
        error = Exception("Unauthorized: Invalid API key")
        classified = handler.classify_error(error)
        
        assert classified.error_type == ErrorType.AUTHENTICATION_ERROR
        assert classified.severity == ErrorSeverity.HIGH
    
    def test_classify_rate_limit_error(self):
        """Test rate limit error classification"""
        handler = ErrorHandler()
        error = Exception("Rate limit exceeded: 429")
        classified = handler.classify_error(error)
        
        assert classified.error_type == ErrorType.RATE_LIMIT_ERROR
        assert classified.severity == ErrorSeverity.MEDIUM
    
    def test_is_retryable(self):
        """Test retryable error check"""
        handler = ErrorHandler()
        
        # Retryable error
        error = TranscriptionError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            retry_count=0
        )
        assert handler.is_retryable(error) is True
        
        # Non-retryable error
        error = TranscriptionError(
            error_type=ErrorType.AUTHENTICATION_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Auth error",
            retry_count=0
        )
        assert handler.is_retryable(error) is False
        
        # Max retries exceeded
        error = TranscriptionError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            retry_count=3
        )
        assert handler.is_retryable(error) is False
    
    def test_calculate_retry_delay(self):
        """Test retry delay calculation"""
        handler = ErrorHandler()
        
        delay1 = handler.calculate_retry_delay(0)
        delay2 = handler.calculate_retry_delay(1)
        delay3 = handler.calculate_retry_delay(2)
        
        # Should increase exponentially
        assert delay2 > delay1
        assert delay3 > delay2
        assert delay3 <= handler.retry_config.max_delay
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self):
        """Test retry with successful execution"""
        handler = ErrorHandler()
        
        async def success_func():
            return "success"
        
        result = await handler.retry_with_backoff(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_failure(self):
        """Test retry with eventual failure"""
        handler = ErrorHandler(RetryConfig(max_retries=2))
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Network error")
        
        with pytest.raises(Exception):
            await handler.retry_with_backoff(failing_func)
        
        # Should have retried max_retries + 1 times
        assert call_count == handler.retry_config.max_retries + 1
    
    def test_get_error_summary(self):
        """Test error summary generation"""
        handler = ErrorHandler()
        
        # Add some errors
        error1 = Exception("Network error")
        error2 = Exception("Auth error")
        
        handler.classify_error(error1)
        handler.classify_error(error2)
        
        summary = handler.get_error_summary()
        assert summary["total_errors"] == 2
        assert "error_stats" in summary
        assert "recent_errors" in summary


class TestFallbackHandler:
    """Test FallbackHandler class"""
    
    def test_initialization(self):
        """Test fallback handler initialization"""
        error_handler = ErrorHandler()
        fallback = FallbackHandler(error_handler)
        
        assert fallback.error_handler == error_handler
        assert fallback.fallback_enabled is True
    
    @pytest.mark.asyncio
    async def test_handle_auth_failure(self):
        """Test authentication failure handling"""
        error_handler = ErrorHandler()
        fallback = FallbackHandler(error_handler)
        
        error = TranscriptionError(
            error_type=ErrorType.AUTHENTICATION_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Invalid API key"
        )
        
        result = await fallback.handle_transcription_failure(error, session_id="test")
        assert result["error_type"] == ErrorType.AUTHENTICATION_ERROR.value
        assert "Authentication failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_network_failure(self):
        """Test network failure handling"""
        error_handler = ErrorHandler()
        fallback = FallbackHandler(error_handler)
        
        error = TranscriptionError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Connection timeout"
        )
        
        result = await fallback.handle_transcription_failure(
            error,
            audio_data=b"test",
            session_id="test"
        )
        assert result["error_type"] == ErrorType.NETWORK_ERROR.value
        assert "Network error" in result["error"]

