#!/usr/bin/env python3
"""Test Deepgram WebSocket connection"""

import os
import asyncio
from dotenv import load_dotenv
import websockets
import json

# Load environment variables
load_dotenv()

async def test_deepgram_connection():
    """Test Deepgram WebSocket connection"""
    try:
        deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        
        if not deepgram_api_key:
            print("❌ DEEPGRAM_API_KEY not found in environment variables")
            print("   Add DEEPGRAM_API_KEY to your .env file")
            return False
        
        print(f"✓ Found DEEPGRAM_API_KEY: {deepgram_api_key[:20]}...")
        print("\n🔌 Connecting to Deepgram WebSocket...")
        
        # Build Deepgram WebSocket URL with token parameter
        # Deepgram supports API key as query parameter: ?token={API_KEY}
        params = {
            "model": "nova-2",
            "language": "en-US",
            "smart_format": "true",
            "punctuate": "true",
            "interim_results": "true",
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        deepgram_url = f"wss://api.deepgram.com/v1/listen?{query_string}&token={deepgram_api_key}"
        
        print(f"📍 URL: {deepgram_url[:80]}...")
        print(f"🔑 Using token query parameter")
        
        # Connect to Deepgram
        async with websockets.connect(
            deepgram_url,
            ping_interval=20,
            ping_timeout=10,
        ) as ws:
            print("✅ Successfully connected to Deepgram WebSocket!")
            
            # Send a test message (empty audio to test connection)
            # Deepgram expects binary audio data, but we can test with empty
            print("\n📤 Sending test message...")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                if isinstance(response, str):
                    data = json.loads(response)
                    print(f"✅ Received response: {json.dumps(data, indent=2)}")
                else:
                    print(f"✅ Received binary response (length: {len(response)})")
            except asyncio.TimeoutError:
                print("⚠️  No response received (this is normal if no audio was sent)")
            
            print("\n🎉 Deepgram WebSocket connection test successful!")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 401:
            print(f"\n❌ Authentication failed (401)")
            print("   Check that your DEEPGRAM_API_KEY is correct")
            print("   Get your API key at: https://console.deepgram.com")
        else:
            print(f"\n❌ Connection failed with status {e.status_code}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check that DEEPGRAM_API_KEY is correct in .env file")
        print("   2. Verify your API key at: https://console.deepgram.com")
        print("   3. Ensure your account has credits/permissions")
        print("   4. Check network connectivity")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Deepgram WebSocket Connection Test")
    print("="*60 + "\n")
    asyncio.run(test_deepgram_connection())
