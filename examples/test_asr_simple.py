#!/usr/bin/env python3
"""
Simple ASR Transcription Test

Quick test to verify Deepgram transcription is working.
Shows how to use the transcription system.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.transcription import DeepgramClient, TranscriptionConfig

async def test_transcription():
    """Test transcription with Deepgram"""
    print("=" * 80)
    print("  ASR Transcription Test")
    print("=" * 80)
    print()
    
    # Check for API key
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ DEEPGRAM_API_KEY not found!")
        print()
        print("To test transcription:")
        print("1. Get API key from: https://console.deepgram.com/")
        print("2. Add to .env file: DEEPGRAM_API_KEY=your_key_here")
        print("3. Or export: export DEEPGRAM_API_KEY=your_key_here")
        print()
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    try:
        # Initialize client
        print("Initializing Deepgram client...")
        os.environ["DEEPGRAM_API_KEY"] = api_key
        client = DeepgramClient(api_key=api_key)
        print("✓ Client initialized")
        print()
        
        # Check for test audio file
        test_files = [
            "test_audio.wav",
            "test_audio.mp3",
            "examples/test_audio.wav",
            "data/test_audio.wav",
            "test.wav",
            "test.mp3"
        ]
        
        audio_file = None
        for file_path in test_files:
            if Path(file_path).exists():
                audio_file = file_path
                break
        
        if not audio_file:
            print("⚠ No audio file found for testing")
            print()
            print("To test with real audio:")
            print("1. Place a WAV or MP3 file in the project root")
            print("2. Name it 'test_audio.wav' or 'test_audio.mp3'")
            print("3. Run this script again")
            print()
            print("For now, showing how the API would be called...")
            print()
            print("Example usage:")
            print("  result = await client.transcribe_file('audio.wav')")
            print("  print(result['transcript'])")
            print()
            return True
        
        # Transcribe the file
        print(f"Transcribing: {audio_file}")
        print("This may take a few seconds...")
        print()
        
        result = await client.transcribe_file(audio_file, session_id="test_session")
        
        if result and result.get("transcript"):
            print("✓ Transcription successful!")
            print()
            print("Transcript:")
            print("-" * 80)
            print(result["transcript"])
            print("-" * 80)
            print()
            
            if result.get("confidence"):
                print(f"Confidence: {result['confidence']:.2%}")
            if result.get("metadata", {}).get("duration"):
                print(f"Duration: {result['metadata']['duration']:.2f}s")
            print()
            
            return True
        else:
            print("⚠ Transcription completed but no transcript returned")
            print(f"Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_transcription())
    
    print("=" * 80)
    if success:
        print("  ✓ Test completed")
    else:
        print("  ✗ Test failed or skipped")
    print("=" * 80)
    
    sys.exit(0 if success else 1)

