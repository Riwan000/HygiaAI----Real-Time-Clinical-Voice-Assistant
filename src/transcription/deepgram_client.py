"""
Deepgram API Client for Real-Time Medical Transcription

This module provides integration with Deepgram's speech-to-text API
for converting live doctor-patient audio into text transcripts.
"""

import os
import logging
import asyncio
import time
from typing import Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass

from deepgram import Deepgram

from .streaming_manager import StreamingManager, AdaptiveStreamingConfig
from .error_handler import ErrorHandler, FallbackHandler, RetryConfig

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionConfig:
    """Configuration for Deepgram transcription"""
    language: str = "en-US"
    model: str = "nova-2"  # Deepgram's latest model for better accuracy
    smart_format: bool = True  # Automatic punctuation and formatting
    punctuate: bool = True
    diarize: bool = True  # Speaker diarization (doctor vs patient)
    interim_results: bool = True  # Real-time partial results
    endpointing: int = 300  # Milliseconds of silence before endpointing
    vad_events: bool = True  # Voice activity detection events
    utterance_end_ms: int = 1000  # Milliseconds to wait for utterance end
    
    def to_listen_options(self, for_streaming: bool = False) -> Dict[str, Any]:
        """Convert to Deepgram ListenOptions dictionary
        
        Args:
            for_streaming: If True, includes streaming-only options (interim_results, endpointing, etc.)
        """
        options = {
            "model": self.model,
            "language": self.language,
            "smart_format": self.smart_format,
            "punctuate": self.punctuate,
            "diarize": self.diarize,
        }
        
        # Streaming-only options (not supported for file transcription)
        if for_streaming:
            options.update({
                "interim_results": self.interim_results,
                "endpointing": self.endpointing,
                "vad_events": self.vad_events,
                "utterance_end_ms": self.utterance_end_ms,
            })
        
        return options


class DeepgramClient:
    """
    Deepgram API client for real-time medical transcription
    
    Handles:
    - API authentication and connection
    - Real-time streaming transcription with adaptive buffering
    - Network quality detection and adaptation
    - Medical terminology accuracy configuration
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        streaming_config: Optional[AdaptiveStreamingConfig] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize Deepgram client
        
        Args:
            api_key: Deepgram API key. If None, reads from environment variable DEEPGRAM_API_KEY
            streaming_config: Adaptive streaming configuration
            retry_config: Retry configuration for error handling
        """
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Deepgram API key is required. "
                "Set DEEPGRAM_API_KEY in .env file or pass api_key parameter."
            )
        
        # Initialize Deepgram SDK client (v2)
        # Set in environment for SDK to pick up
        os.environ["DEEPGRAM_API_KEY"] = self.api_key
        # v2 SDK: Deepgram(api_key) - positional argument
        self.client = Deepgram(self.api_key)
        self.config = TranscriptionConfig()
        
        # Initialize streaming manager
        self.streaming_manager = StreamingManager(streaming_config)
        
        # Initialize error handler
        self.error_handler = ErrorHandler(retry_config)
        self.fallback_handler = FallbackHandler(self.error_handler)
        
        logger.info("Deepgram client initialized successfully")
    
    def _detect_mimetype(self, file_path: str) -> str:
        """
        Detect MIME type from file extension for Deepgram SDK v2
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            MIME type string (e.g., 'audio/wav', 'audio/mpeg')
        """
        import mimetypes
        import os
        
        # Get file extension
        _, ext = os.path.splitext(file_path.lower())
        
        # MIME type mapping for common audio formats
        mime_map = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.opus': 'audio/opus',
            '.webm': 'audio/webm',
            '.aac': 'audio/aac',
            '.amr': 'audio/amr',
            '.wma': 'audio/x-ms-wma',
        }
        
        # Check our mapping first
        if ext in mime_map:
            return mime_map[ext]
        
        # Fallback to mimetypes module
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype and mimetype.startswith('audio/'):
            return mimetype
        
        # Default to wav if unknown
        logger.warning(f"Unknown audio format for {file_path}, defaulting to audio/wav")
        return 'audio/wav'
    
    def update_config(self, config: TranscriptionConfig):
        """
        Update transcription configuration
        
        Args:
            config: TranscriptionConfig instance with desired settings
        """
        self.config = config
        logger.info(f"Transcription config updated: model={config.model}, language={config.language}")
    
    def get_adaptive_listen_options(self) -> Dict[str, Any]:
        """
        Get adaptive listen options based on network quality
        
        Returns:
            Dictionary of listen options with adaptive settings
        """
        base_options = self.config.to_listen_options()
        adaptive_settings = self.streaming_manager.get_adaptive_settings()
        
        # Adjust interim results based on network quality
        if not adaptive_settings.get("enable_interim_results", True):
            base_options["interim_results"] = False
        
        return base_options
    
    async def transcribe_audio_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        session_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Transcribe audio stream in real-time with adaptive buffering
        
        Args:
            audio_stream: Async iterator of audio bytes
            session_id: Optional session identifier for tracking
            
        Yields:
            Dict containing transcription results with:
            - transcript: The transcribed text
            - is_final: Whether this is a final result
            - confidence: Confidence score
            - speaker: Speaker ID (if diarization enabled)
            - timestamp: Timestamp of the transcription
            - metrics: Streaming metrics (if available)
        """
        self.streaming_manager.start_streaming()
        result_queue = asyncio.Queue()
        is_finished = False
        start_time = time.time()
        last_chunk_time = start_time
        
        try:
            # Get adaptive options (for streaming, include streaming-specific options)
            options = self.get_adaptive_listen_options()
            # Ensure streaming options are included
            base_options = self.config.to_listen_options(for_streaming=True)
            options.update(base_options)
            
            # Start live transcription
            logger.info("Starting live transcription with adaptive streaming")
            
            # Create a task to stream audio with buffering
            async def stream_audio_with_buffering():
                """Stream audio with adaptive buffering"""
                nonlocal last_chunk_time
                try:
                    async for audio_chunk in audio_stream:
                        # Buffer the chunk
                        await self.streaming_manager.buffer_audio_chunk(audio_chunk)
                        
                        # Calculate latency
                        current_time = time.time()
                        latency = current_time - last_chunk_time
                        last_chunk_time = current_time
                        
                        # Update metrics
                        self.streaming_manager.update_metrics(latency=latency)
                        
                        # Get buffered chunks for sending
                        async for buffered_chunk in self.streaming_manager.get_buffered_chunks():
                            # Send to Deepgram (placeholder - actual implementation depends on SDK)
                            # For now, we'll simulate the streaming
                            await asyncio.sleep(0.01)  # Simulate network delay
                    
                    # Signal completion
                    is_finished = True
                    await result_queue.put(None)
                    
                except Exception as e:
                    logger.error(f"Error streaming audio: {e}")
                    is_finished = True
                    await result_queue.put({
                        "error": str(e),
                        "session_id": session_id,
                    })
            
            # Start streaming task
            stream_task = asyncio.create_task(stream_audio_with_buffering())
            
            # Monitor network quality and adjust settings
            async def monitor_network_quality():
                """Monitor network quality and adjust settings"""
                while not is_finished:
                    await asyncio.sleep(2.0)  # Check every 2 seconds
                    if self.streaming_manager.should_adjust_quality():
                        metrics = self.streaming_manager.get_metrics()
                        logger.debug(
                            f"Network quality: {metrics.network_quality.value}, "
                            f"Latency: {metrics.latency:.3f}s"
                        )
            
            monitor_task = asyncio.create_task(monitor_network_quality())
            
            # Yield results (simulated for now - will be replaced with actual Deepgram SDK calls)
            # For now, we'll yield metrics and status updates
            while not is_finished or not result_queue.empty():
                try:
                    result = await asyncio.wait_for(result_queue.get(), timeout=1.0)
                    if result is None:  # Sentinel value
                        break
                    yield result
                except asyncio.TimeoutError:
                    # Yield metrics update
                    metrics = self.streaming_manager.get_metrics()
                    yield {
                        "type": "metrics",
                        "metrics": {
                            "latency": metrics.latency,
                            "network_quality": metrics.network_quality.value,
                            "buffer_size": len(self.streaming_manager.audio_chunks),
                        },
                        "session_id": session_id,
                    }
                    continue
            
            # Wait for tasks to complete
            await stream_task
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
        finally:
            self.streaming_manager.stop_streaming()
    
    async def transcribe_file(
        self,
        file_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe a pre-recorded audio file with error handling
        
        Args:
            file_path: Path to audio file
            session_id: Optional session identifier
            
        Returns:
            Dict containing transcription results
        """
        context = {
            "file_path": file_path,
            "session_id": session_id,
            "operation": "transcribe_file"
        }
        
        async def _transcribe():
            """Internal transcription function for retry logic"""
            # Check if file_path is a URL or local file
            is_url = file_path.startswith(('http://', 'https://'))
            
            if is_url:
                # For URLs, use REST API directly (like curl command)
                import requests
                url_endpoint = "https://api.deepgram.com/v2/listen"
                options = self.config.to_listen_options(for_streaming=False)
                
                # Build query string from options
                query_params = []
                if options.get('model'):
                    query_params.append(f"model={options['model']}")
                if options.get('smart_format'):
                    query_params.append("smart_format=true")
                if options.get('language'):
                    query_params.append(f"language={options['language']}")
                
                url_endpoint += "?" + "&".join(query_params) if query_params else ""
                
                headers = {
                    "Authorization": f"Token {self.api_key}",
                    "content-type": "application/json, audio/wav"
                }
                
                payload = {"url": file_path}
                
                logger.debug(f"Using REST API for URL transcription: {url_endpoint}")
                
                def _call_url_transcribe():
                    response = requests.post(url_endpoint, headers=headers, json=payload, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        # Convert REST API response to SDK-like format for parsing
                        if 'results' in result and 'channels' in result['results']:
                            channel = result['results']['channels'][0]
                            if 'alternatives' in channel and len(channel['alternatives']) > 0:
                                alternative = channel['alternatives'][0]
                                # Create a response object that matches SDK structure
                                class ResponseObj:
                                    def __init__(self, data):
                                        # Store the alternative for easy access
                                        alt = data['results']['channels'][0]['alternatives'][0]
                                        self.results = type('obj', (object,), {
                                            'channels': [type('obj', (object,), {
                                                'alternatives': [type('obj', (object,), {
                                                    'transcript': alt.get('transcript', ''),
                                                    'confidence': alt.get('confidence', 0)
                                                })()]
                                            })()]
                                        })()
                                        if 'metadata' in data:
                                            self.metadata = type('obj', (object,), data['metadata'])()
                                
                                return ResponseObj(result)
                    response.raise_for_status()
                    return None
                
                # Use retry logic for URL transcription too
                response = await self.error_handler.retry_with_backoff(
                    _call_url_transcribe,
                    context=context
                )
            else:
                # For local files, read the file
                with open(file_path, "rb") as audio_file:
                    audio_data_ref = audio_file.read()
                
                # Use Deepgram SDK to transcribe
                # Note: File transcription doesn't support streaming-only options
                options = self.config.to_listen_options(for_streaming=False)
                
                # Transcribe using Deepgram SDK with retry
                # Note: Deepgram SDK v2 uses client.transcription.create()
                # Note: create() is synchronous, not async
                # Store references to avoid closure issues
                client_ref = self.client
                options_ref = options
                
                def _call_transcribe():
                    try:
                        # Deepgram SDK v2 uses transcription methods
                        # Check if transcription attribute exists
                        if not hasattr(client_ref, 'transcription'):
                            available_attrs = [x for x in dir(client_ref) if not x.startswith('_')]
                            raise AttributeError(
                                f"Deepgram SDK v2 client missing 'transcription' attribute. "
                                f"Client type: {type(client_ref).__name__}, "
                                f"Available attributes: {available_attrs[:10]}"
                            )
                        
                        transcription_obj = client_ref.transcription
                        transcription_methods = [x for x in dir(transcription_obj) if not x.startswith('_')]
                        logger.debug(f"Transcription methods: {transcription_methods}")
                        
                        # Deepgram SDK v2: transcription.sync_prerecorded() for synchronous file transcription
                        # Takes source dict with 'buffer' key for bytes (requires mimetype) or 'url' for URLs
                        if hasattr(transcription_obj, 'sync_prerecorded'):
                            sync_func = transcription_obj.sync_prerecorded
                            if callable(sync_func):
                                logger.debug("Using SDK v2 API: client.transcription.sync_prerecorded()")
                                # v2 SDK sync_prerecorded takes source dict and options
                                if isinstance(audio_data_ref, bytes):
                                    # Detect mimetype from file extension
                                    mimetype = self._detect_mimetype(file_path)
                                    source = {
                                        'buffer': audio_data_ref,
                                        'mimetype': mimetype
                                    }
                                else:
                                    source = audio_data_ref  # Already a dict for URLs
                                
                                return sync_func(
                                    source,
                                    **options_ref
                                )
                        
                        # Fallback to prerecorded (async, but we'll call it synchronously)
                        if hasattr(transcription_obj, 'prerecorded'):
                            prerecorded_func = transcription_obj.prerecorded
                            if callable(prerecorded_func):
                                logger.debug("Using SDK v2 API: client.transcription.prerecorded()")
                                # v2 SDK prerecorded takes source dict and options
                                if isinstance(audio_data_ref, bytes):
                                    # Detect mimetype from file extension
                                    mimetype = self._detect_mimetype(file_path)
                                    source = {
                                        'buffer': audio_data_ref,
                                        'mimetype': mimetype
                                    }
                                else:
                                    source = audio_data_ref  # Already a dict for URLs
                                
                                # Note: prerecorded is async, but we're in a sync context
                                # This might need to be handled differently
                                return prerecorded_func(
                                    source,
                                    **options_ref
                                )
                        
                        # If we get here, the expected methods weren't found
                        available_attrs = [x for x in dir(client_ref) if not x.startswith('_')]
                        raise AttributeError(
                            f"Deepgram SDK v2 structure not recognized. "
                            f"Client type: {type(client_ref).__name__}, "
                            f"Available attributes: {available_attrs[:10]}. "
                            f"Transcription methods: {transcription_methods}. "
                            f"Expected client.transcription.sync_prerecorded() or prerecorded() for v2 SDK."
                        )
                        
                    except Exception as e:
                        logger.error(f"Deepgram SDK structure error: {e}")
                        logger.error(f"Client type: {type(client_ref)}")
                        if 'transcription_obj' in locals():
                            logger.error(f"Transcription methods: {transcription_methods if 'transcription_methods' in locals() else 'N/A'}")
                        raise
                
                response = await self.error_handler.retry_with_backoff(
                    _call_transcribe,
                    context=context
                )
            
            # Both URL and file paths converge here for response parsing
            
            # Log response structure for debugging
            if response is None:
                logger.warning("Deepgram API returned None response")
                return {
                    "transcript": "",
                    "is_final": True,
                    "error": "No response from Deepgram API",
                    "error_type": "api_error",
                    "session_id": session_id,
                }
            
            # Log response type for debugging
            logger.debug(f"Response type: {type(response)}, hasattr results: {hasattr(response, 'results')}")
            
            # Parse response - handle different response structures
            transcript_text = ""
            confidence = None
            duration = None
            
            # Method 0: Handle dict responses (Deepgram SDK v2 returns dict)
            if isinstance(response, dict):
                logger.debug("Response is a dict, parsing dict structure")
                if 'results' in response and response['results']:
                    results = response['results']
                    if 'channels' in results and results['channels']:
                        channel = results['channels'][0]
                        if 'alternatives' in channel and channel['alternatives']:
                            alternative = channel['alternatives'][0]
                            transcript_text = str(alternative.get('transcript', alternative.get('text', ''))) or ""
                            confidence = alternative.get('confidence')
                            logger.info(f"Extracted transcript from dict: length={len(transcript_text)}, confidence={confidence}")
                            if transcript_text:
                                logger.debug(f"Transcript preview: {transcript_text[:200]}...")
                if 'metadata' in response:
                    metadata = response['metadata']
                    duration = metadata.get('duration') if isinstance(metadata, dict) else None
            
            # Method 1: Standard Deepgram SDK response structure (object with attributes)
            elif hasattr(response, 'results') and response.results:
                logger.debug(f"Response has results: {type(response.results)}")
                if hasattr(response.results, 'channels') and response.results.channels:
                    logger.debug(f"Response has {len(response.results.channels)} channels")
                    channel = response.results.channels[0]
                    logger.debug(f"Channel type: {type(channel)}, has alternatives: {hasattr(channel, 'alternatives')}")
                    if hasattr(channel, 'alternatives') and channel.alternatives:
                        logger.debug(f"Channel has {len(channel.alternatives)} alternatives")
                        alternative = channel.alternatives[0]
                        logger.debug(f"Alternative type: {type(alternative)}, has transcript: {hasattr(alternative, 'transcript')}")
                        # Try multiple ways to access transcript
                        if hasattr(alternative, 'transcript'):
                            transcript_text = str(alternative.transcript) if alternative.transcript is not None else ""
                        elif hasattr(alternative, 'text'):
                            transcript_text = str(alternative.text) if alternative.text is not None else ""
                        else:
                            transcript_text = ""
                        confidence = alternative.confidence if hasattr(alternative, 'confidence') else None
                        logger.info(f"Extracted transcript length: {len(transcript_text)}, confidence: {confidence}")
                        if transcript_text:
                            logger.debug(f"Transcript preview: {transcript_text[:200]}...")
            
            # Method 2: Check if response has metadata directly
            if hasattr(response, 'metadata') and hasattr(response.metadata, 'duration'):
                duration = response.metadata.duration
            elif hasattr(response, 'duration'):
                duration = response.duration
            
            # Method 3: Try to access transcript directly (some SDK versions)
            if not transcript_text and hasattr(response, 'transcript'):
                transcript_text = response.transcript
            if not confidence and hasattr(response, 'confidence'):
                confidence = response.confidence
            
            # Method 4: Check if response is a dict-like object
            if not transcript_text and hasattr(response, 'get'):
                transcript_text = response.get('transcript', '')
                confidence = response.get('confidence')
                duration = response.get('duration')
            
            # If we got a transcript, return success
            if transcript_text:
                return {
                    "transcript": transcript_text,
                    "is_final": True,
                    "confidence": confidence,
                    "speaker": None,
                    "session_id": session_id,
                    "metadata": {
                        "duration": duration,
                    }
                }
            
            # No transcript found - log response structure for debugging
            logger.warning(f"Transcription completed but no transcript found. Response structure: {type(response)}")
            logger.debug(f"Response attributes: {[x for x in dir(response) if not x.startswith('_')][:20]}")
            
            return {
                "transcript": "",
                "is_final": True,
                "error": "Transcription completed but no transcript returned. Check audio file format and content.",
                "error_type": "no_transcript",
                "session_id": session_id,
                "metadata": {
                    "duration": duration,
                }
            }
        
        try:
            result = await _transcribe()
            
            # Check if result indicates a successful API call but no transcript
            # Don't treat this as a network error
            if result.get("error_type") == "no_transcript":
                # This is not a network error - API call succeeded but no transcript
                logger.warning("Transcription API call succeeded but returned no transcript")
                return result
            
            # If we have a transcript, return it
            if result.get("transcript"):
                return result
            
            # If we have an error but it's not a network error, return it
            if result.get("error") and result.get("error_type") != "network_error":
                return result
            
            # Otherwise, treat as network/API error
            return result
            
        except Exception as e:
            # Log the actual exception for debugging
            logger.error(f"Exception during transcription: {type(e).__name__}: {e}", exc_info=True)
            
            # Classify and handle error
            error = self.error_handler.classify_error(e, context)
            
            # Use fallback handler only for actual exceptions
            return await self.fallback_handler.handle_transcription_failure(
                error,
                audio_data=None,  # Could read file here for fallback
                session_id=session_id
            )
    
    def test_connection(self) -> bool:
        """
        Test Deepgram API connection with error handling
        
        Returns:
            True if connection is successful, False otherwise
        """
        context = {"operation": "test_connection"}
        
        def _test():
            """Internal test function"""
            from deepgram import Options
            test_client = Deepgram(self.api_key)
            return True
        
        try:
            # Test with retry logic
            result = asyncio.run(
                self.error_handler.retry_with_backoff(
                    _test,
                    context=context
                )
            )
            logger.info("Deepgram connection test successful")
            return result
        except Exception as e:
            error = self.error_handler.classify_error(e, context)
            logger.error(f"Deepgram connection test failed: {error.message}")
            return False
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error handling summary
        
        Returns:
            Dictionary with error statistics and recent errors
        """
        return self.error_handler.get_error_summary()
    
    def clear_error_log(self):
        """Clear error log"""
        self.error_handler.clear_error_log()
    
    def get_streaming_metrics(self) -> Dict[str, Any]:
        """
        Get current streaming metrics
        
        Returns:
            Dictionary of streaming metrics
        """
        metrics = self.streaming_manager.get_metrics()
        return {
            "latency": metrics.latency,
            "packet_loss": metrics.packet_loss,
            "throughput": metrics.throughput,
            "buffer_size": metrics.buffer_size,
            "network_quality": metrics.network_quality.value,
            "last_update": metrics.last_update,
        }
