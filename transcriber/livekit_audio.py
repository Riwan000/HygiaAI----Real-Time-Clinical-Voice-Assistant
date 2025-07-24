import asyncio
import pyaudio
from livekit.rtc.audio_stream import AudioStream
from livekit.rtc.room import Room
from livekit.rtc.track import Track
from livekit.rtc.audio_source import AudioSource
from livekit.rtc.audio_frame import AudioFrame
from livekit.api.access_token import AccessToken, VideoGrants
from config import settings
import numpy as np

CHUNK_SIZE = 1024
RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
SAMPLE_WIDTH = pyaudio.get_sample_size(FORMAT)

async def connect_livekit_room(identity=None):
    if identity is None:
        identity = settings.LIVEKIT_USERNAME
    grant = VideoGrants(room=settings.LIVEKIT_ROOM)
    token = (
        AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name("Real-Time Voice Agent")
        .with_grants(grant)
    )
    room = Room()
    await room.connect(url=settings.LIVEKIT_URL, token=token.to_jwt())
    return room

async def publish_mic_to_livekit():
    room = await connect_livekit_room(identity="publisher")
    source = AudioSource(RATE, CHANNELS)
    room.local_participant.publish_track(source)
    p = pyaudio.PyAudio()
    mic_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )
    print("[LiveKit] Publishing microphone audio...")
    try:
        while True:
            data = mic_stream.read(CHUNK_SIZE, exception_on_overflow=False)
            frame = AudioFrame(
                data,
                sample_rate=RATE,
                num_channels=CHANNELS,
                samples_per_channel=CHUNK_SIZE,
            )
            await source.capture_frame(frame)
            await asyncio.sleep(0.01)
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        p.terminate()
        await room.disconnect()

async def subscribe_and_yield_audio_chunks():
    room = await connect_livekit_room(identity="subscriber")
    audio_stream = None
    print("[LiveKit] Waiting for remote audio track...")
    async for event in room.events:
        if event.__class__.__name__ == "TrackSubscribed":
            if getattr(event.track, "kind", None) == Track.kind.KIND_AUDIO:
                audio_stream = AudioStream(event.track)
                print("[LiveKit] Subscribed to remote audio track.")
                break
    if audio_stream:
        async for frame in audio_stream:
            yield frame.frame.data
    await room.disconnect()

async def get_livekit_audio_stream_iterator():
    room = await connect_livekit_room()
    asyncio.create_task(publish_mic_to_livekit())
    audio_stream = None
    async for event in room.events:
        if event.__class__.__name__ == "TrackSubscribed":
            if getattr(event.track, "kind", None) == Track.kind.KIND_AUDIO:
                audio_stream = AudioStream(event.track)
                print("[LiveKit] Subscribed to remote audio track.")
                break
    if audio_stream:
        async for frame in audio_stream:
            yield frame.frame.data
