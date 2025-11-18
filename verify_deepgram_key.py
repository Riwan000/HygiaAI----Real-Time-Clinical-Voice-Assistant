#!/usr/bin/env python3
"""Verify Deepgram API key using REST API"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_deepgram_key():
    """Verify Deepgram API key using REST API"""
    try:
        deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        
        if not deepgram_api_key:
            print("❌ DEEPGRAM_API_KEY not found in environment variables")
            return False
        
        print(f"✓ Found DEEPGRAM_API_KEY: {deepgram_api_key[:20]}...")
        print(f"   Key length: {len(deepgram_api_key)} characters")
        
        # Check key format
        if len(deepgram_api_key) < 30:
            print("⚠️  Warning: API key seems too short (should be ~40+ characters)")
        
        print("\n🔌 Testing API key with Deepgram REST API...")
        
        # Test with Deepgram projects endpoint
        url = "https://api.deepgram.com/v1/projects"
        headers = {
            "Authorization": f"Token {deepgram_api_key}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API key is valid!")
            projects = response.json()
            print(f"   Found {len(projects.get('projects', []))} project(s)")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed (401)")
            print("   Your API key is invalid or expired")
            print("   Get a new API key at: https://console.deepgram.com")
            print(f"   Response: {response.text[:200]}")
            return False
        elif response.status_code == 403:
            print("❌ Access forbidden (403)")
            print("   Your API key doesn't have the required permissions")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Deepgram API Key Verification")
    print("="*60 + "\n")
    verify_deepgram_key()

