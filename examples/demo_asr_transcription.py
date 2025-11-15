#!/usr/bin/env python3
"""
ASR Transcription Demo

Demonstrates Deepgram transcription functionality:
1. File-based transcription
2. Streaming transcription (simulated)
3. Real-time transcription with processing
"""

import sys
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.transcription import DeepgramClient, TranscriptionConfig
from src.transcription.transcript_processor import TranscriptProcessor

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_result(success, message):
    """Print a test result"""
    status = "✓" if success else "✗"
    print(f"{status} {message}")

async def demo_file_transcription():
    """Demonstrate file-based transcription"""
    print_section("1. File-Based Transcription")
    
    # Check if API key is available
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("⚠ DEEPGRAM_API_KEY not found in environment variables")
        print("  To test transcription, you need to:")
        print("  1. Get a Deepgram API key from https://console.deepgram.com/")
        print("  2. Set it in your .env file: DEEPGRAM_API_KEY=your_key_here")
        print("  3. Or export it: export DEEPGRAM_API_KEY=your_key_here")
        print("\n  For now, showing simulated transcription...")
        return False
    
    try:
        # Set API key in environment first
        os.environ["DEEPGRAM_API_KEY"] = api_key
        # Initialize Deepgram client
        client = DeepgramClient(api_key=api_key)
        print_result(True, "Deepgram client initialized")
        
        # Check if we have a test audio file
        test_audio_files = [
            "test_audio.wav",
            "test_audio.mp3",
            "examples/test_audio.wav",
            "data/test_audio.wav"
        ]
        
        audio_file = None
        for file_path in test_audio_files:
            if Path(file_path).exists():
                audio_file = file_path
                break
        
        if not audio_file:
            print("⚠ No test audio file found. Creating a simulated transcription...")
            print("\n  To test with real audio:")
            print("  1. Place an audio file (WAV, MP3) in the project root")
            print("  2. Name it 'test_audio.wav' or 'test_audio.mp3'")
            print("  3. Run this script again")
            
            # Simulate transcription result
            simulated_result = {
                "transcript": "Patient presents with fever, cough, and shortness of breath. Temperature is 38.5 degrees Celsius. Blood pressure 120 over 80.",
                "is_final": True,
                "confidence": 0.95,
                "session_id": "demo_session_001",
                "metadata": {
                    "duration": 5.2,
                    "model": "nova-2"
                }
            }
            
            print("\n  Simulated Transcription Result:")
            print(f"    Transcript: {simulated_result['transcript']}")
            print(f"    Confidence: {simulated_result['confidence']:.2f}")
            print(f"    Duration: {simulated_result['metadata']['duration']}s")
            return True
        
        # Transcribe actual audio file
        print(f"  Transcribing audio file: {audio_file}")
        result = await client.transcribe_file(audio_file, session_id="demo_session_001")
        
        if result and result.get("transcript"):
            print_result(True, "Transcription successful")
            print(f"\n  Transcript:")
            print(f"    {result['transcript']}")
            print(f"\n  Metadata:")
            print(f"    Confidence: {result.get('confidence', 'N/A')}")
            print(f"    Duration: {result.get('metadata', {}).get('duration', 'N/A')}s")
            print(f"    Session ID: {result.get('session_id', 'N/A')}")
            return True
        else:
            print_result(False, "Transcription returned no results")
            return False
            
    except ValueError as e:
        if "API key" in str(e):
            print_result(False, f"API key issue: {e}")
            print("\n  Please set DEEPGRAM_API_KEY in your .env file")
            return False
        raise
    except Exception as e:
        print_result(False, f"Transcription error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def demo_streaming_transcription():
    """Demonstrate streaming transcription (simulated)"""
    print_section("2. Streaming Transcription (Simulated)")
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("⚠ Streaming transcription requires DEEPGRAM_API_KEY")
        print("  Simulating streaming transcription...")
        
        # Simulate streaming results
        simulated_chunks = [
            "Patient presents with",
            "Patient presents with fever",
            "Patient presents with fever and cough",
            "Patient presents with fever, cough, and shortness of breath."
        ]
        
        print("\n  Simulated Streaming Transcription:")
        for i, chunk in enumerate(simulated_chunks, 1):
            print(f"    Chunk {i}: {chunk}")
            await asyncio.sleep(0.5)  # Simulate delay
        
        print("\n  Final transcript: Patient presents with fever, cough, and shortness of breath.")
        return True
    
    try:
        # Set API key in environment first
        os.environ["DEEPGRAM_API_KEY"] = api_key
        client = DeepgramClient(api_key=api_key)
        print_result(True, "Deepgram client initialized for streaming")
        
        # Note: Real streaming requires actual audio input (microphone or audio stream)
        print("\n  To test real streaming transcription:")
        print("  1. Connect a microphone to your system")
        print("  2. Use the streaming API with audio input")
        print("  3. See examples/test_streaming_transcription.py for implementation")
        
        return True
        
    except Exception as e:
        print_result(False, f"Streaming setup error: {e}")
        return False

def demo_transcript_processing():
    """Demonstrate transcript processing"""
    print_section("3. Transcript Processing")
    
    # Sample transcript
    sample_transcript = """
    Patient presents with fever, cough, and shortness of breath.
    Temperature is 38.5 degrees Celsius. Blood pressure 120 over 80.
    Patient reports chest pain and fatigue.
    History of diabetes and hypertension.
    """
    
    print("  Original Transcript:")
    print(f"    {sample_transcript.strip()}")
    
    try:
        # Initialize processor
        processor = TranscriptProcessor()
        print_result(True, "TranscriptProcessor initialized")
        
        # Process transcript (expects dict with 'transcript' key)
        processed = processor.process_transcript({"transcript": sample_transcript})
        
        if processed:
            print_result(True, "Transcript processed successfully")
            print(f"\n  Processed Transcript:")
            print(f"    {processed.get('corrected_transcript', 'N/A')}")
            
            print(f"\n  Medical Entities Extracted: {len(processed.get('medical_entities', []))}")
            for entity in processed.get('medical_entities', [])[:5]:
                entity_text = entity.get('text', 'N/A') if isinstance(entity, dict) else getattr(entity, 'text', 'N/A')
                entity_type = entity.get('type', 'N/A') if isinstance(entity, dict) else getattr(entity, 'entity_type', 'N/A')
                if hasattr(entity_type, 'value'):
                    entity_type = entity_type.value
                print(f"    - {entity_text} ({entity_type})")
            
            print(f"\n  Corrections Applied: {len(processed.get('corrections', []))}")
            for correction in processed.get('corrections', [])[:3]:
                print(f"    - {correction.get('original', 'N/A')} → {correction.get('corrected', 'N/A')}")
            
            return True
        else:
            print_result(False, "Processing returned no results")
            return False
            
    except Exception as e:
        print_result(False, f"Processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def demo_full_pipeline():
    """Demonstrate full transcription pipeline"""
    print_section("4. Full Transcription Pipeline")
    
    # Simulate the full flow
    print("  Simulating full transcription pipeline:")
    print("    1. Audio input → Deepgram API")
    print("    2. Raw transcript received")
    print("    3. Medical entity extraction")
    print("    4. Terminology validation")
    print("    5. Spell checking")
    print("    6. Final processed transcript")
    
    sample_transcript = "Patient presents with fever, cough, and shortness of breath."
    
    try:
        processor = TranscriptProcessor()
        processed = processor.process_transcript({"transcript": sample_transcript})
        
        if processed:
            print_result(True, "Full pipeline executed successfully")
            print(f"\n  Input: {sample_transcript}")
            print(f"  Output: {processed.get('corrected_transcript', 'N/A')}")
            print(f"  Entities: {len(processed.get('medical_entities', []))}")
            return True
        return False
        
    except Exception as e:
        print_result(False, f"Pipeline error: {e}")
        return False

def main():
    """Run ASR transcription demo"""
    print("=" * 80)
    print("  HygiaAI - ASR Transcription Demo")
    print("=" * 80)
    
    results = {
        "file_transcription": False,
        "streaming_transcription": False,
        "transcript_processing": False,
        "full_pipeline": False
    }
    
    # Run demos
    try:
        # File transcription
        results["file_transcription"] = asyncio.run(demo_file_transcription())
        
        # Streaming transcription
        results["streaming_transcription"] = asyncio.run(demo_streaming_transcription())
        
        # Transcript processing
        results["transcript_processing"] = demo_transcript_processing()
        
        # Full pipeline
        results["full_pipeline"] = asyncio.run(demo_full_pipeline())
        
    except KeyboardInterrupt:
        print("\n\n⚠ Demo interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print_section("Demo Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"Total Demos: {total}")
    print(f"Successful: {passed}")
    print(f"Failed/Skipped: {total - passed}")
    
    print("\n" + "=" * 80)
    if passed == total:
        print("  ✓ All Demos Completed Successfully!")
    else:
        print("  ⚠ Some demos skipped (API key or audio file not available)")
    print("=" * 80)
    
    print("\n📝 Next Steps:")
    print("  1. Get Deepgram API key: https://console.deepgram.com/")
    print("  2. Add to .env file: DEEPGRAM_API_KEY=your_key_here")
    print("  3. Add test audio file (WAV/MP3) to test real transcription")
    print("  4. Run this script again to see live transcription")

if __name__ == "__main__":
    main()

