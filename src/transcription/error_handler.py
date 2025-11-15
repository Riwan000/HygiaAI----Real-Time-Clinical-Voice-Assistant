"""
Error Handling Module for Deepgram Transcription

Provides:
- Multi-level error handling framework
- Error detection and classification
- Retry logic with exponential backoff
- Fallback mechanisms
- Automated logging
"""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import traceback

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error type classification"""
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    API_ERROR = "api_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INVALID_INPUT_ERROR = "invalid_input_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"  # Recoverable, can retry
    MEDIUM = "medium"  # May need fallback
    HIGH = "high"  # Critical, may need manual intervention
    CRITICAL = "critical"  # System failure


@dataclass
class TranscriptionError:
    """Structured error information"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    original_exception: Optional[Exception] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        return {
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "retry_count": self.retry_count,
            "stack_trace": self.stack_trace,
        }


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    initial_delay: float = 1.0  # Seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff base
    jitter: bool = True  # Add random jitter to delays
    retryable_errors: list[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK_ERROR,
        ErrorType.TIMEOUT_ERROR,
        ErrorType.RATE_LIMIT_ERROR,
        ErrorType.API_ERROR,
    ])


class ErrorHandler:
    """
    Multi-level error handling framework for Deepgram transcription
    
    Features:
    - Error detection and classification
    - Automatic retry with exponential backoff
    - Fallback mechanisms
    - Comprehensive logging
    - Error recovery strategies
    """
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize error handler
        
        Args:
            retry_config: Retry configuration
        """
        self.retry_config = retry_config or RetryConfig()
        self.error_log: list[TranscriptionError] = []
        self.error_stats: Dict[str, int] = {}
        
    def classify_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> TranscriptionError:
        """
        Classify an exception into a TranscriptionError
        
        Args:
            exception: The exception to classify
            context: Additional context information
            
        Returns:
            TranscriptionError with classified error type and severity
        """
        error_type = ErrorType.UNKNOWN_ERROR
        severity = ErrorSeverity.MEDIUM
        message = str(exception)
        
        # Classify error type
        exception_type = type(exception).__name__
        exception_str = str(exception).lower()
        
        # Network errors
        if any(keyword in exception_str for keyword in ['connection', 'network', 'socket', 'timeout', 'unreachable']):
            error_type = ErrorType.NETWORK_ERROR
            severity = ErrorSeverity.MEDIUM
        # Authentication errors
        elif any(keyword in exception_str for keyword in ['auth', 'unauthorized', 'forbidden', '401', '403', 'api key', 'invalid key']):
            error_type = ErrorType.AUTHENTICATION_ERROR
            severity = ErrorSeverity.HIGH
        # Rate limit errors
        elif any(keyword in exception_str for keyword in ['rate limit', '429', 'too many requests', 'quota']):
            error_type = ErrorType.RATE_LIMIT_ERROR
            severity = ErrorSeverity.MEDIUM
        # Timeout errors
        elif any(keyword in exception_str for keyword in ['timeout', 'timed out', 'deadline']):
            error_type = ErrorType.TIMEOUT_ERROR
            severity = ErrorSeverity.MEDIUM
        # API errors
        elif any(keyword in exception_str for keyword in ['api', 'server error', '500', '502', '503', '504']):
            error_type = ErrorType.API_ERROR
            severity = ErrorSeverity.MEDIUM
        # Invalid input errors
        elif any(keyword in exception_str for keyword in ['invalid', 'bad request', '400', 'malformed']):
            error_type = ErrorType.INVALID_INPUT_ERROR
            severity = ErrorSeverity.LOW
        
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        error = TranscriptionError(
            error_type=error_type,
            severity=severity,
            message=message,
            original_exception=exception,
            context=context or {},
            stack_trace=stack_trace
        )
        
        # Log error
        self.log_error(error)
        
        return error
    
    def log_error(self, error: TranscriptionError):
        """
        Log error with appropriate level
        
        Args:
            error: TranscriptionError to log
        """
        self.error_log.append(error)
        
        # Update statistics
        error_key = f"{error.error_type.value}_{error.severity.value}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1
        
        # Log based on severity
        log_message = (
            f"[{error.error_type.value}] {error.message} "
            f"(Severity: {error.severity.value}, Retries: {error.retry_count})"
        )
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=error.original_exception)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message, exc_info=error.original_exception)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Log context if available
        if error.context:
            logger.debug(f"Error context: {error.context}")
    
    def is_retryable(self, error: TranscriptionError) -> bool:
        """
        Check if error is retryable
        
        Args:
            error: TranscriptionError to check
            
        Returns:
            True if error is retryable
        """
        if error.retry_count >= self.retry_config.max_retries:
            return False
        
        return error.error_type in self.retry_config.retryable_errors
    
    def calculate_retry_delay(self, retry_count: int) -> float:
        """
        Calculate retry delay with exponential backoff
        
        Args:
            retry_count: Current retry attempt number
            
        Returns:
            Delay in seconds
        """
        delay = self.retry_config.initial_delay * (
            self.retry_config.exponential_base ** retry_count
        )
        
        # Cap at max delay
        delay = min(delay, self.retry_config.max_delay)
        
        # Add jitter if enabled
        if self.retry_config.jitter:
            import random
            jitter = delay * 0.1 * random.random()  # 10% jitter
            delay += jitter
        
        return delay
    
    async def retry_with_backoff(
        self,
        func: Callable,
        *args,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic and exponential backoff
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            context: Additional context for error handling
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_error: Optional[TranscriptionError] = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                elif asyncio.iscoroutine(func):
                    result = await func
                else:
                    result = func(*args, **kwargs)
                
                # Success - log if retried
                if attempt > 0:
                    logger.info(f"Function succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                # Classify error
                error = self.classify_error(e, context)
                error.retry_count = attempt
                last_error = error
                
                # Check if retryable
                if not self.is_retryable(error):
                    logger.error(f"Error not retryable: {error.error_type.value}")
                    raise error.original_exception or e
                
                # Check if we've exhausted retries
                if attempt >= self.retry_config.max_retries:
                    logger.error(
                        f"Max retries ({self.retry_config.max_retries}) exceeded. "
                        f"Last error: {error.message}"
                    )
                    raise error.original_exception or e
                
                # Calculate delay and wait
                delay = self.calculate_retry_delay(attempt)
                logger.warning(
                    f"Retry {attempt + 1}/{self.retry_config.max_retries} after {delay:.2f}s. "
                    f"Error: {error.message}"
                )
                await asyncio.sleep(delay)
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error.original_exception or Exception(last_error.message)
        raise Exception("Unknown error in retry logic")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of errors
        
        Returns:
            Dictionary with error statistics
        """
        return {
            "total_errors": len(self.error_log),
            "error_stats": self.error_stats.copy(),
            "recent_errors": [
                error.to_dict()
                for error in self.error_log[-10:]  # Last 10 errors
            ],
        }
    
    def clear_error_log(self):
        """Clear error log and statistics"""
        self.error_log.clear()
        self.error_stats.clear()
        logger.info("Error log cleared")


class FallbackHandler:
    """
    Fallback mechanisms for transcription failures
    
    Provides:
    - Alternative transcription methods
    - Graceful degradation
    - Error recovery strategies
    """
    
    def __init__(self, error_handler: ErrorHandler):
        """
        Initialize fallback handler
        
        Args:
            error_handler: ErrorHandler instance
        """
        self.error_handler = error_handler
        self.fallback_enabled = True
    
    async def handle_transcription_failure(
        self,
        error: TranscriptionError,
        audio_data: Optional[bytes] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle transcription failure with fallback mechanisms
        
        Args:
            error: TranscriptionError that occurred
            audio_data: Optional audio data for fallback processing
            session_id: Optional session identifier
            
        Returns:
            Fallback result dictionary
        """
        logger.warning(f"Handling transcription failure: {error.error_type.value}")
        
        # Determine fallback strategy based on error type
        if error.error_type == ErrorType.AUTHENTICATION_ERROR:
            return self._handle_auth_failure(error, session_id)
        elif error.error_type == ErrorType.NETWORK_ERROR:
            return self._handle_network_failure(error, audio_data, session_id)
        elif error.error_type == ErrorType.RATE_LIMIT_ERROR:
            return self._handle_rate_limit_failure(error, session_id)
        else:
            return self._handle_generic_failure(error, session_id)
    
    def _handle_auth_failure(
        self,
        error: TranscriptionError,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle authentication failure"""
        return {
            "transcript": "",
            "is_final": True,
            "error": "Authentication failed. Please check API key.",
            "error_type": error.error_type.value,
            "fallback_used": False,
            "session_id": session_id,
        }
    
    def _handle_network_failure(
        self,
        error: TranscriptionError,
        audio_data: Optional[bytes] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle network failure"""
        # Could implement local fallback or queue for later processing
        return {
            "transcript": "",
            "is_final": True,
            "error": "Network error. Please check connection and try again.",
            "error_type": error.error_type.value,
            "fallback_used": False,
            "session_id": session_id,
            "suggestion": "Audio data can be queued for processing when connection is restored",
        }
    
    def _handle_rate_limit_failure(
        self,
        error: TranscriptionError,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle rate limit failure"""
        return {
            "transcript": "",
            "is_final": True,
            "error": "Rate limit exceeded. Please wait before retrying.",
            "error_type": error.error_type.value,
            "fallback_used": False,
            "session_id": session_id,
            "suggestion": "Implement request queuing or reduce request frequency",
        }
    
    def _handle_generic_failure(
        self,
        error: TranscriptionError,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle generic failure"""
        return {
            "transcript": "",
            "is_final": True,
            "error": f"Transcription failed: {error.message}",
            "error_type": error.error_type.value,
            "fallback_used": False,
            "session_id": session_id,
        }

