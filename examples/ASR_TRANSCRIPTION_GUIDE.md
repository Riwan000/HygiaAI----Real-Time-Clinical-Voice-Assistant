# ASR Transcription Guide

This guide shows you how to use the HygiaAI ASR (Automatic Speech Recognition) transcription system.

## Quick Start

### 1. Setup API Key

Get your Deepgram API key from: https://console.deepgram.com/

Add it to your `.env` file:
```bash
DEEPGRAM_API_KEY=your_api_key_here
```

### 2. Test Connection

```bash
python test_deepgram_connection.py
```

### 3. Test Transcription

```bash
# Simple test
python examples/test_asr_simple.py

# Full demo
python examples/demo_asr_transcription.py
```

## Usage Examples

### File-Based Transcription

```python
import asyncio
from src.transcription import DeepgramClient

async def transcribe_audio():
    client = DeepgramClient()
    result = await client.transcribe_file("audio.wav")
    print(result["transcript"])

asyncio.run(transcribe_audio())
```

### Streaming Transcription

```python
import asyncio
from src.transcription import DeepgramClient

async def stream_transcription():
    client = DeepgramClient()
    
    # Create audio stream (from microphone or file)
    async def audio_stream():
        # Your audio stream generator here
        yield audio_chunk_1
        yield audio_chunk_2
        # ...
    
    async for result in client.transcribe_audio_stream(audio_stream()):
        if result.get("is_final"):
            print(f"Final: {result['transcript']}")
        else:
            print(f"Interim: {result['transcript']}")

asyncio.run(stream_transcription())
```

### Transcript Processing

```python
from src.transcription.transcript_processor import TranscriptProcessor

processor = TranscriptProcessor()

# Process raw transcript
raw_transcript = {
    "transcript": "Patient has fevr and caugh",
    "confidence": 0.95
}

processed = processor.process_transcript(raw_transcript)

print(processed["corrected_transcript"])
# Output: "Patient has fever and cough"

print(processed["medical_entities"])
# Output: List of extracted medical entities
```

## Configuration

### Transcription Config

```python
from src.transcription import TranscriptionConfig, DeepgramClient

# Custom configuration
config = TranscriptionConfig(
    language="en-US",
    model="nova-2",  # Best accuracy
    smart_format=True,  # Auto punctuation
    diarize=True,  # Speaker identification
    interim_results=True  # Real-time results
)

client = DeepgramClient()
client.update_config(config)
```

### Available Models

- `nova-2` - Latest, best accuracy (recommended)
- `nova` - Previous generation
- `base` - Faster, lower cost
- `enhanced` - Better for medical terminology

## Features

### 1. Medical Terminology Support
- Automatic correction of medical terms
- Spell checking for medical vocabulary
- Entity extraction (symptoms, diagnoses, medications)

### 2. Speaker Diarization
- Identifies doctor vs patient
- Separates multiple speakers
- Timestamps for each speaker

### 3. Real-Time Processing
- Streaming transcription
- Interim results
- Adaptive buffering based on network quality

### 4. Error Handling
- Automatic retry with backoff
- Fallback mechanisms
- Network quality detection

## Testing

### Test with Audio File

1. Place audio file in project root:
   - `test_audio.wav`
   - `test_audio.mp3`
   - Or any WAV/MP3 file

2. Run test:
   ```bash
   python examples/test_asr_simple.py
   ```

### Test Connection

```bash
python test_deepgram_connection.py
```

## API Reference

### DeepgramClient

#### `transcribe_file(file_path, session_id=None)`
Transcribe an audio file.

**Parameters:**
- `file_path` (str): Path to audio file
- `session_id` (str, optional): Session identifier

**Returns:**
```python
{
    "transcript": "Transcribed text...",
    "is_final": True,
    "confidence": 0.95,
    "session_id": "session_123",
    "metadata": {
        "duration": 5.2
    }
}
```

#### `transcribe_audio_stream(audio_stream, session_id=None)`
Stream transcription for real-time audio.

**Parameters:**
- `audio_stream` (AsyncIterator[bytes]): Audio data stream
- `session_id` (str, optional): Session identifier

**Returns:**
- AsyncIterator of transcription results

## Troubleshooting

### API Key Issues

**Error:** `DEEPGRAM_API_KEY not found`

**Solution:**
1. Check `.env` file exists
2. Verify key is set: `DEEPGRAM_API_KEY=your_key`
3. Restart terminal/IDE

### Audio File Issues

**Error:** `File not found`

**Solution:**
- Use absolute path
- Check file format (WAV, MP3 supported)
- Verify file permissions

### Network Issues

**Error:** Connection timeout

**Solution:**
- Check internet connection
- Verify Deepgram service status
- Try again (automatic retry included)

## Next Steps

1. ✅ Test connection: `python test_deepgram_connection.py`
2. ✅ Test transcription: `python examples/test_asr_simple.py`
3. ✅ Process transcripts: See `examples/demo_asr_transcription.py`
4. ✅ Integrate with full pipeline: See end-to-end test

## Support

- Deepgram Docs: https://developers.deepgram.com/
- Deepgram Console: https://console.deepgram.com/
- Project Issues: Check GitHub issues

