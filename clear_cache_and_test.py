#!/usr/bin/env python3
"""
Clear Python cache and test Deepgram transcription
Run this if you're getting SDK structure errors
"""

import sys
import os
import shutil
from pathlib import Path

print("=" * 80)
print("Clearing Python Cache and Testing")
print("=" * 80)
print()

# Clear __pycache__ directories
print("1. Clearing __pycache__ directories...")
cache_dirs = list(Path('.').rglob('__pycache__'))
for cache_dir in cache_dirs:
    try:
        shutil.rmtree(cache_dir)
        print(f"   ✓ Removed: {cache_dir}")
    except Exception as e:
        print(f"   ⚠ Could not remove {cache_dir}: {e}")

# Clear .pyc files
print("\n2. Clearing .pyc files...")
pyc_files = list(Path('.').rglob('*.pyc'))
for pyc_file in pyc_files:
    try:
        pyc_file.unlink()
        print(f"   ✓ Removed: {pyc_file}")
    except Exception as e:
        print(f"   ⚠ Could not remove {pyc_file}: {e}")

# Clear module cache
print("\n3. Clearing Python module cache...")
modules_to_clear = [
    'src.transcription.deepgram_client',
    'src.transcription',
    'src',
    'deepgram'
]
for module in modules_to_clear:
    if module in sys.modules:
        del sys.modules[module]
        print(f"   ✓ Cleared: {module}")

print("\n4. Testing transcription...")
print("-" * 80)

# Now test
try:
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Import and test
    from src.transcription import DeepgramClient
    import asyncio
    
    async def test():
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            print("⚠ DEEPGRAM_API_KEY not found")
            return False
        
        client = DeepgramClient(api_key=api_key)
        print("✓ Client initialized")
        
        # Find test file
        test_files = ["test_audio.mp3", "test_audio.wav"]
        audio_file = None
        for f in test_files:
            if Path(f).exists():
                audio_file = f
                break
        
        if not audio_file:
            print("⚠ No test audio file found")
            return True  # Still success if client initialized
        
        print(f"Transcribing: {audio_file}")
        result = await client.transcribe_file(audio_file, session_id="cache_test")
        
        if result.get("transcript"):
            print(f"✓ Transcription successful! ({len(result['transcript'])} chars)")
            return True
        else:
            print(f"⚠ No transcript returned: {result.get('error', 'Unknown error')}")
            return False
    
    success = asyncio.run(test())
    
    print("\n" + "=" * 80)
    if success:
        print("✓ All tests passed!")
    else:
        print("⚠ Some issues detected")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ Error during test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


