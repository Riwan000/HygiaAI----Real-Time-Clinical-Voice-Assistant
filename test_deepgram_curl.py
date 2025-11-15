"""
Test Deepgram API directly using curl-like request
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_deepgram_api():
    """Test Deepgram API with a direct HTTP request"""
    
    # Get API key
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ DEEPGRAM_API_KEY not found in environment")
        return False
    
    print("=" * 80)
    print("Testing Deepgram API Directly")
    print("=" * 80)
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # API endpoint
    url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
    
    # Headers
    headers = {
        "Authorization": f"Token {api_key}",
        "content-type": "application/json"
    }
    
    # Request body
    payload = {
        "url": "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
    }
    
    print(f"\n📡 Making request to: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print("\n" + "-" * 80)
    
    try:
        # Make the request
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print("-" * 80)
            
            # Extract transcript
            if 'results' in result and 'channels' in result['results']:
                channel = result['results']['channels'][0]
                if 'alternatives' in channel and len(channel['alternatives']) > 0:
                    transcript = channel['alternatives'][0].get('transcript', '')
                    confidence = channel['alternatives'][0].get('confidence', 0)
                    print(f"\n📝 Transcript:")
                    print(f"   {transcript}")
                    print(f"\n🎯 Confidence: {confidence:.2%}")
            
            print(f"\n📊 Full Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_deepgram_api()
    print("\n" + "=" * 80)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed")
    print("=" * 80)

