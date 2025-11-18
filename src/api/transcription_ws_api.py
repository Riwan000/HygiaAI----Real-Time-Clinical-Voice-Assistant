"""
WebSocket proxy for Deepgram transcription
Bypasses browser restrictions by proxying WebSocket through backend
"""
import os
import json
import logging
import asyncio
import tempfile
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.routing import APIRouter
import websockets
from websockets.exceptions import ConnectionClosed
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/transcription", tags=["Transcription"])

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


@router.websocket("/ws")
async def transcription_websocket(websocket: WebSocket):
    """
    WebSocket proxy endpoint for Deepgram transcription
    
    Proxies audio data between browser and Deepgram WebSocket API.
    This bypasses browser restrictions and firewall issues.
    """
    await websocket.accept()
    
    if not DEEPGRAM_API_KEY:
        await websocket.close(code=1008, reason="Deepgram API key not configured")
        return
    
    deepgram_ws = None
    
    try:
        # Get configuration from client
        config = await websocket.receive_json()
        
        # Build Deepgram WebSocket URL
        params = {
            "model": config.get("model", "nova-2"),
            "language": config.get("language", "en-US"),
            "smart_format": str(config.get("smart_format", True)).lower(),
            "punctuate": str(config.get("punctuate", True)).lower(),
            "interim_results": str(config.get("interim_results", True)).lower(),
        }
        
        # Add optional parameters
        if config.get("diarize"):
            params["diarize"] = "true"
        if config.get("endpointing"):
            params["endpointing"] = str(config["endpointing"])
        if config.get("vad_events"):
            params["vad_events"] = "true"
        
        # Build query string with token parameter
        # Deepgram supports API key as query parameter: ?token={API_KEY}
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        deepgram_url = f"{DEEPGRAM_WS_URL}?{query_string}&token={DEEPGRAM_API_KEY}"
        
        logger.info(f"Connecting to Deepgram: {deepgram_url[:80]}...")
        
        # Connect to Deepgram WebSocket
        # Note: Using token in query string (Deepgram supports both header and query param)
        deepgram_ws = await websockets.connect(
            deepgram_url,
            ping_interval=20,
            ping_timeout=10,
        )
        
        logger.info("Connected to Deepgram WebSocket")
        await websocket.send_json({"type": "connected", "message": "Connected to Deepgram"})
        
        # Create tasks for bidirectional message forwarding
        async def forward_to_deepgram():
            """Forward audio data from browser to Deepgram"""
            try:
                while True:
                    # Receive data from browser
                    try:
                        data = await websocket.receive()
                        
                        if data.get("type") == "websocket.receive":
                            if "bytes" in data:
                                # Audio binary data - forward to Deepgram
                                audio_bytes = data["bytes"]
                                await deepgram_ws.send(audio_bytes)
                            elif "text" in data:
                                # JSON configuration (already sent) or control messages
                                try:
                                    msg = json.loads(data["text"])
                                    if msg.get("type") == "close":
                                        break
                                except json.JSONDecodeError:
                                    pass
                    except WebSocketDisconnect:
                        break
            except Exception as e:
                logger.error(f"Error forwarding to Deepgram: {e}")
        
        async def forward_from_deepgram():
            """Forward transcription results from Deepgram to browser"""
            try:
                async for message in deepgram_ws:
                    if isinstance(message, str):
                        # JSON response
                        try:
                            data = json.loads(message)
                            await websocket.send_json(data)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON from Deepgram: {message[:100]}")
                    else:
                        # Binary data (shouldn't happen with Deepgram)
                        await websocket.send_bytes(message)
            except ConnectionClosed:
                logger.info("Deepgram connection closed")
            except Exception as e:
                logger.error(f"Error forwarding from Deepgram: {e}")
        
        # Run both forwarding tasks concurrently
        await asyncio.gather(
            forward_to_deepgram(),
            forward_from_deepgram(),
            return_exceptions=True
        )
        
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        # Clean up
        if deepgram_ws:
            try:
                await deepgram_ws.close()
            except:
                pass
        try:
            await websocket.close()
        except:
            pass


@router.get("/health")
async def transcription_health():
    """Health check for transcription service"""
    return {
        "status": "healthy",
        "deepgram_configured": bool(DEEPGRAM_API_KEY),
        "websocket_proxy": True
    }


class TranscriptionResponse(BaseModel):
    """Response model for file transcription"""
    success: bool
    transcript: str
    words: List[Dict[str, Any]] = []
    confidence: float = 0.0
    duration: float = 0.0
    language: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None


@router.post("/file", response_model=TranscriptionResponse)
async def transcribe_audio_file(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form("en-US"),
    model: Optional[str] = Form("nova-2"),
    smart_format: Optional[bool] = Form(True),
    punctuate: Optional[bool] = Form(True),
    diarize: Optional[bool] = Form(True)
):
    """
    Transcribe an uploaded audio file using Deepgram
    
    Supports: WAV, MP3, MPEG, WEBM, M4A, FLAC, OGG, OPUS, and other audio formats
    """
    if not DEEPGRAM_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Deepgram API key not configured"
        )
    
    # Validate file type
    allowed_extensions = ['.wav', '.mp3', '.mpeg', '.webm', '.m4a', '.flac', '.ogg', '.opus', '.mp4', '.avi']
    file_ext = Path(audio_file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    temp_file = None
    try:
        # Save uploaded file temporarily
        file_content = await audio_file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(file_content)
            temp_file = tmp.name
        
        logger.info(f"Transcribing audio file: {audio_file.filename} ({len(file_content)} bytes)")
        
        # Detect mimetype from file extension
        mimetype_map = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.mpeg': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.opus': 'audio/opus',
            '.webm': 'audio/webm',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
        }
        detected_mimetype = mimetype_map.get(file_ext, audio_file.content_type or 'audio/wav')
        
        # Use Deepgram SDK for file transcription
        try:
            # Try Deepgram SDK v5 first
            try:
                from deepgram import DeepgramClient, PrerecordedOptions, FileSource
                
                deepgram = DeepgramClient(DEEPGRAM_API_KEY)
                
                # Prepare options
                options = PrerecordedOptions(
                    model=model or "nova-2",
                    language=language or "en-US",
                    smart_format=smart_format,
                    punctuate=punctuate,
                    diarize=diarize
                )
                
                # Read file as bytes
                with open(temp_file, "rb") as audio_file_handle:
                    audio_data = audio_file_handle.read()
                    # Include mimetype when using bytes
                    payload: FileSource = {
                        "buffer": audio_data,
                        "mimetype": detected_mimetype
                    }
                    
                    # Transcribe using Deepgram SDK v5
                    response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
            except (ImportError, AttributeError):
                # Fallback to Deepgram SDK v2
                from deepgram import Deepgram
                
                deepgram = Deepgram(DEEPGRAM_API_KEY)
                
                # Read file as bytes
                with open(temp_file, "rb") as audio_file_handle:
                    audio_data = audio_file_handle.read()
                    
                    # Prepare options dict for v2 SDK
                    options_dict = {
                        "model": model or "nova-2",
                        "language": language or "en-US",
                        "smart_format": smart_format,
                        "punctuate": punctuate,
                        "diarize": diarize
                    }
                    
                    # Include mimetype when using bytes (required for SDK v2)
                    source_dict = {
                        "buffer": audio_data,
                        "mimetype": detected_mimetype
                    }
                    
                    # Transcribe using Deepgram SDK v2
                    response = deepgram.transcription.sync_prerecorded(
                        source_dict,
                        options_dict
                    )
                
                # Extract transcript (works for both SDK v2 and v5)
                transcript = ""
                words = []
                confidence = 0.0
                duration = 0.0
                
                # Handle both SDK v2 and v5 response formats
                results = getattr(response, 'results', None) or (response.get('results') if isinstance(response, dict) else None)
                
                if results:
                    channels = getattr(results, 'channels', None) or (results.get('channels', []) if isinstance(results, dict) else [])
                    if channels:
                        channel = channels[0] if isinstance(channels, list) else channels
                        
                        # Get alternatives
                        alternatives = getattr(channel, 'alternatives', None) or (channel.get('alternatives', []) if isinstance(channel, dict) else [])
                        if alternatives:
                            alternative = alternatives[0] if isinstance(alternatives, list) else alternatives
                            
                            # Extract transcript and confidence
                            if isinstance(alternative, dict):
                                transcript = alternative.get('transcript', '')
                                confidence = alternative.get('confidence', 0.0)
                                word_list = alternative.get('words', [])
                            else:
                                transcript = getattr(alternative, 'transcript', '') or ''
                                confidence = getattr(alternative, 'confidence', 0.0) or 0.0
                                word_list = getattr(alternative, 'words', None) or []
                            
                            # Extract words with timestamps
                            if word_list:
                                words = [
                                    {
                                        "word": w.get('word', '') if isinstance(w, dict) else getattr(w, 'word', ''),
                                        "start": w.get('start', 0) if isinstance(w, dict) else getattr(w, 'start', 0),
                                        "end": w.get('end', 0) if isinstance(w, dict) else getattr(w, 'end', 0),
                                        "confidence": w.get('confidence', 0) if isinstance(w, dict) else getattr(w, 'confidence', 0),
                                        "speaker": w.get('speaker') if isinstance(w, dict) else getattr(w, 'speaker', None)
                                    }
                                    for w in word_list
                                ]
                
                # Get duration from metadata
                metadata = getattr(response, 'metadata', None) or (response.get('metadata', {}) if isinstance(response, dict) else {})
                if metadata:
                    if isinstance(metadata, dict):
                        duration = metadata.get('duration', 0.0)
                    else:
                        duration = getattr(metadata, 'duration', 0.0) or 0.0
                
                logger.info(f"Transcription complete: {len(transcript)} characters, {len(words)} words")
                
                return TranscriptionResponse(
                    success=True,
                    transcript=transcript,
                    words=words,
                    confidence=confidence,
                    duration=duration,
                    language=language or "en-US",
                    model=model or "nova-2"
                )
                
        except (ImportError, AttributeError, ValueError, TypeError) as sdk_error:
            # Fallback: Use Deepgram REST API directly
            logger.warning(f"Deepgram SDK error ({type(sdk_error).__name__}): {sdk_error}, using REST API fallback")
            import httpx
            
            with open(temp_file, "rb") as audio:
                files = {
                    "audio": (audio_file.filename, audio, detected_mimetype)
                }
                
                params = {
                    "model": model or "nova-2",
                    "language": language or "en-US",
                    "smart_format": "true" if smart_format else "false",
                    "punctuate": "true" if punctuate else "false",
                    "diarize": "true" if diarize else "false"
                }
                
                headers = {
                    "Authorization": f"Token {DEEPGRAM_API_KEY}"
                }
                
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        "https://api.deepgram.com/v1/listen",
                        files=files,
                        params=params,
                        headers=headers
                    )
                    
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Deepgram API error: {response.text}"
                        )
                    
                    result = response.json()
                    
                    # Extract transcript
                    transcript = ""
                    words = []
                    confidence = 0.0
                    duration = 0.0
                    
                    if result.get("results") and result["results"].get("channels"):
                        channel = result["results"]["channels"][0]
                        
                        if channel.get("alternatives"):
                            alternative = channel["alternatives"][0]
                            transcript = alternative.get("transcript", "")
                            confidence = alternative.get("confidence", 0.0)
                            
                            if alternative.get("words"):
                                words = alternative["words"]
                    
                    if result.get("metadata") and result["metadata"].get("duration"):
                        duration = result["metadata"]["duration"]
                    
                    return TranscriptionResponse(
                        success=True,
                        transcript=transcript,
                        words=words,
                        confidence=confidence,
                        duration=duration,
                        language=language or "en-US",
                        model=model or "nova-2"
                    )
        
    except Exception as e:
        logger.error(f"Error transcribing audio file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error transcribing audio: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")

