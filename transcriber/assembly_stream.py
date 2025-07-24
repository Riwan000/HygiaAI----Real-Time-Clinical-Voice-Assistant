import asyncio
import aiohttp
import json
from config import settings

ASSEMBLYAI_WS_URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

async def stream_to_assemblyai(audio_chunk_generator):
    session = aiohttp.ClientSession()
    async with session.ws_connect(
        ASSEMBLYAI_WS_URL,
        headers={"Authorization": settings.ASSEMBLYAI_API_KEY}
    ) as ws:
        async def send_audio():
            async for chunk in audio_chunk_generator:
                await ws.send_bytes(chunk)
        async def receive_transcripts():
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("message_type") == "FinalTranscript":
                        print("[Transcript]", data.get("text"))
        await asyncio.gather(send_audio(), receive_transcripts())
    await session.close()
