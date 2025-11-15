"""
Example: Testing Error Handling Mechanisms

Demonstrates:
- Error classification
- Retry logic with exponential backoff
- Fallback mechanisms
- Error logging and statistics
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.transcription.error_handler import (
    ErrorHandler,
    FallbackHandler,
    ErrorType,
    ErrorSeverity,
    RetryConfig
)
from src.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")


async def simulate_network_error():
    """Simulate a network error"""
    raise ConnectionError("Connection timeout: Unable to reach server")


async def simulate_auth_error():
    """Simulate an authentication error"""
    raise Exception("Unauthorized: Invalid API key")


async def simulate_rate_limit_error():
    """Simulate a rate limit error"""
    raise Exception("Rate limit exceeded: 429 Too Many Requests")


async def simulate_successful_operation():
    """Simulate a successful operation"""
    return {"status": "success", "data": "transcription result"}


async def test_error_classification():
    """Test error classification"""
    print("=" * 60)
    print("Test 1: Error Classification")
    print("=" * 60)
    print()
    
    handler = ErrorHandler()
    
    # Test network error
    try:
        await simulate_network_error()
    except Exception as e:
        error = handler.classify_error(e)
        print(f"✓ Network Error Classified:")
        print(f"  Type: {error.error_type.value}")
        print(f"  Severity: {error.severity.value}")
        print(f"  Message: {error.message}")
        print()
    
    # Test auth error
    try:
        await simulate_auth_error()
    except Exception as e:
        error = handler.classify_error(e)
        print(f"✓ Authentication Error Classified:")
        print(f"  Type: {error.error_type.value}")
        print(f"  Severity: {error.severity.value}")
        print(f"  Message: {error.message}")
        print()
    
    # Test rate limit error
    try:
        await simulate_rate_limit_error()
    except Exception as e:
        error = handler.classify_error(e)
        print(f"✓ Rate Limit Error Classified:")
        print(f"  Type: {error.error_type.value}")
        print(f"  Severity: {error.severity.value}")
        print(f"  Message: {error.message}")
        print()


async def test_retry_logic():
    """Test retry logic with exponential backoff"""
    print("=" * 60)
    print("Test 2: Retry Logic with Exponential Backoff")
    print("=" * 60)
    print()
    
    retry_config = RetryConfig(
        max_retries=3,
        initial_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0
    )
    handler = ErrorHandler(retry_config)
    
    call_count = 0
    
    async def flaky_operation():
        """Operation that fails twice then succeeds"""
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Network error (attempt {call_count})")
        return {"status": "success", "attempt": call_count}
    
    print("Testing retry logic with flaky operation...")
    print("  (Operation will fail twice, then succeed on 3rd attempt)")
    print()
    
    try:
        result = await handler.retry_with_backoff(flaky_operation)
        print(f"✓ Operation succeeded after {call_count} attempts")
        print(f"  Result: {result}")
        print()
    except Exception as e:
        print(f"✗ Operation failed: {e}")
        print()
    
    # Test with operation that always fails
    print("Testing retry logic with always-failing operation...")
    print()
    
    call_count = 0
    
    async def always_failing_operation():
        """Operation that always fails"""
        nonlocal call_count
        call_count += 1
        raise ConnectionError(f"Persistent network error (attempt {call_count})")
    
    try:
        await handler.retry_with_backoff(always_failing_operation)
    except Exception as e:
        print(f"✓ Operation correctly failed after {call_count} attempts")
        print(f"  Final error: {e}")
        print()


async def test_fallback_mechanisms():
    """Test fallback mechanisms"""
    print("=" * 60)
    print("Test 3: Fallback Mechanisms")
    print("=" * 60)
    print()
    
    handler = ErrorHandler()
    fallback = FallbackHandler(handler)
    
    # Test auth failure fallback
    print("Testing authentication failure fallback...")
    auth_error = handler.classify_error(Exception("Unauthorized: Invalid API key"))
    result = await fallback.handle_transcription_failure(
        auth_error,
        session_id="test-session-1"
    )
    print(f"✓ Fallback result:")
    print(f"  Error Type: {result['error_type']}")
    print(f"  Error Message: {result['error']}")
    print(f"  Fallback Used: {result['fallback_used']}")
    print()
    
    # Test network failure fallback
    print("Testing network failure fallback...")
    network_error = handler.classify_error(Exception("Connection timeout"))
    result = await fallback.handle_transcription_failure(
        network_error,
        audio_data=b"test audio data",
        session_id="test-session-2"
    )
    print(f"✓ Fallback result:")
    print(f"  Error Type: {result['error_type']}")
    print(f"  Error Message: {result['error']}")
    print(f"  Suggestion: {result.get('suggestion', 'N/A')}")
    print()


async def test_error_statistics():
    """Test error statistics and logging"""
    print("=" * 60)
    print("Test 4: Error Statistics and Logging")
    print("=" * 60)
    print()
    
    handler = ErrorHandler()
    
    # Generate various errors
    errors = [
        Exception("Network error 1"),
        Exception("Network error 2"),
        Exception("Unauthorized: Invalid API key"),
        Exception("Rate limit exceeded: 429"),
        Exception("Connection timeout"),
    ]
    
    for error in errors:
        handler.classify_error(error)
    
    # Get error summary
    summary = handler.get_error_summary()
    
    print(f"✓ Error Statistics:")
    print(f"  Total Errors: {summary['total_errors']}")
    print(f"  Error Stats: {summary['error_stats']}")
    print(f"  Recent Errors: {len(summary['recent_errors'])}")
    print()
    
    print("Recent Errors:")
    for i, error in enumerate(summary['recent_errors'][:3], 1):
        print(f"  {i}. {error['error_type']} - {error['message'][:50]}...")
    print()


async def main():
    """Run all error handling tests"""
    print()
    print("=" * 60)
    print("Error Handling Mechanisms Test Suite")
    print("=" * 60)
    print()
    
    await test_error_classification()
    await test_retry_logic()
    await test_fallback_mechanisms()
    await test_error_statistics()
    
    print("=" * 60)
    print("✅ All error handling tests completed!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())

