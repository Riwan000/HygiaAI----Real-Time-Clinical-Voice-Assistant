"""
WebSocket proxy for Deepgram transcription
Bypasses browser restrictions by proxying WebSocket through backend
"""
import os
import json
import logging
import asyncio
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.routing import APIRouter
import websockets
from websockets.exceptions import ConnectionClosed

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
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        deepgram_url = f"{DEEPGRAM_WS_URL}?{query_string}&token={DEEPGRAM_API_KEY}"
        
        logger.info(f"Connecting to Deepgram: {deepgram_url[:80]}...")
        
        # Connect to Deepgram WebSocket
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

