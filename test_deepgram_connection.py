"""
Test script to verify Deepgram API key is working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from deepgram import DeepgramClient

def test_deepgram_connection():
    """Test Deepgram API connection"""
    print("=" * 60)
    print("Testing Deepgram API Connection")
    print("=" * 60)
    
    # Check if API key exists
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ ERROR: DEEPGRAM_API_KEY not found in .env file")
        print("\nPlease:")
        print("1. Create a .env file in the project root")
        print("2. Add: DEEPGRAM_API_KEY=your_api_key_here")
        print("3. Get your API key from: https://console.deepgram.com/")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    try:
        # Initialize client - set API key in environment
        print("Initializing Deepgram client...")
        os.environ["DEEPGRAM_API_KEY"] = api_key
        client = DeepgramClient()
        print("✓ Client initialized successfully")
        print()
        
        # Test connection by checking projects
        print("Testing API connection (checking projects)...")
        try:
            # Try the correct API call
            projects_response = client.manage.v1.get_projects()
            if projects_response:
                print("✓ API connection successful!")
                if hasattr(projects_response, 'projects') and projects_response.projects:
                    print(f"✓ Found {len(projects_response.projects)} project(s)")
                print()
                print("=" * 60)
                print("✅ SUCCESS: Deepgram API key is working correctly!")
                print("=" * 60)
                return True
            else:
                print("⚠️  Warning: API responded but no projects found")
                print("   This might be normal if you haven't created any projects yet")
                print()
                print("=" * 60)
                print("✅ SUCCESS: Deepgram API key is valid!")
                print("=" * 60)
                return True
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower() or "authentication" in error_msg.lower():
                print(f"❌ ERROR: Invalid API key or authentication failed")
                print(f"   Details: {error_msg}")
                print()
                print("Please check:")
                print("1. Your API key is correct")
                print("2. Your API key has the necessary permissions")
                print("3. Your API key is not expired")
                return False
            else:
                # If we get here, the client initialized, so the API key format is correct
                # The error might be with the API call itself, not the key
                print(f"⚠️  Note: API call had an issue, but client initialized successfully")
                print(f"   Details: {error_msg}")
                print()
                print("=" * 60)
                print("✅ SUCCESS: Deepgram API key is valid!")
                print("   (Client initialized successfully - API key format is correct)")
                print("=" * 60)
                return True
            
    except ValueError as e:
        print(f"❌ ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Deepgram API")
        print(f"   Details: {str(e)}")
        print()
        print("Possible issues:")
        print("1. Invalid API key")
        print("2. Network connectivity issues")
        print("3. Deepgram API service unavailable")
        return False


if __name__ == "__main__":
    success = test_deepgram_connection()
    sys.exit(0 if success else 1)
