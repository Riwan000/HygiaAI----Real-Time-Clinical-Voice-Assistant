"""
Test Deepgram SDK client after the fix
"""
import os
import asyncio
from dotenv import load_dotenv
from src.transcription.deepgram_client import DeepgramClient

load_dotenv()

async def test_sdk_client():
    """Test the SDK client with the fixed code"""
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ DEEPGRAM_API_KEY not found")
        return False
    
    print("=" * 80)
    print("Testing Deepgram SDK Client (After Fix)")
    print("=" * 80)
    
    try:
        # Initialize client
        client = DeepgramClient(api_key=api_key)
        print("✓ Client initialized")
        
        # Test with URL (same as curl test)
        audio_url = "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
        print(f"\n📡 Transcribing URL: {audio_url}")
        
        result = await client.transcribe_file(
            file_path=audio_url
        )
        
        if result and result.get('transcript'):
            transcript = result['transcript']
            confidence = result.get('confidence', 0)
            
            print("\n✅ SUCCESS!")
            print("-" * 80)
            print(f"📝 Transcript ({len(transcript)} chars):")
            print(f"   {transcript[:200]}..." if len(transcript) > 200 else f"   {transcript}")
            print(f"\n🎯 Confidence: {confidence:.2%}")
            return True
        else:
            print("\n❌ No transcript returned")
            print(f"Result: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sdk_client())
    print("\n" + "=" * 80)
    if success:
        print("✅ SDK Client test completed successfully!")
    else:
        print("❌ SDK Client test failed")
    print("=" * 80)

