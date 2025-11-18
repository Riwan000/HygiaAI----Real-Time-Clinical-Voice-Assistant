#!/usr/bin/env python3
"""
Debug Multimodal Input 500 Error

This script helps debug the 500 error by testing the endpoint
with detailed error output.
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ENDPOINT = f"{API_BASE_URL}/api/v1/clinical_memory/ingest"


def test_minimal_request():
    """Test with minimal required fields"""
    print("="*80)
    print("TEST: Minimal Request (text only)")
    print("="*80)
    
    data = {
        "patient_id": "DEBUG_TEST_001",
        "transcript_text": "Patient presents with cough and fever."
    }
    
    print(f"\n📤 Sending request to: {ENDPOINT}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(ENDPOINT, data=data, timeout=30)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"\n✅ Success!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"\n❌ Error Response:")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Detail: {error_data.get('detail', 'No detail provided')}")
                print(f"Full Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Cannot connect to {API_BASE_URL}")
        print(f"   Make sure backend server is running!")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def test_with_metadata():
    """Test with full metadata"""
    print("\n" + "="*80)
    print("TEST: Full Request (with metadata)")
    print("="*80)
    
    data = {
        "patient_id": "DEBUG_TEST_002",
        "transcript_text": "Patient presents with chest pain. History of hypertension.",
        "age_group": "adult",
        "region": "urban",
        "comorbidities": json.dumps(["hypertension"]),
        "diagnosis": "Chest pain, etiology unknown"
    }
    
    print(f"\n📤 Sending request to: {ENDPOINT}")
    print(f"Data keys: {list(data.keys())}")
    
    try:
        response = requests.post(ENDPOINT, data=data, timeout=30)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"\n✅ Success!")
            result = response.json()
            print(f"Case ID: {result.get('case_id')}")
            print(f"Status: {result.get('status')}")
        else:
            print(f"\n❌ Error Response:")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Detail: {error_data.get('detail', 'No detail provided')}")
            except:
                print(f"Raw Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def check_backend_health():
    """Check if backend is running"""
    print("="*80)
    print("Checking Backend Health")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Backend responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {API_BASE_URL}")
        print(f"   Please start the backend server: python run_server.py")
        return False
    except Exception as e:
        print(f"⚠️  Error checking health: {e}")
        return False


if __name__ == "__main__":
    print("="*80)
    print("  Multimodal Input Error Debugger")
    print("="*80)
    
    # Check backend health
    if not check_backend_health():
        print("\n⚠️  Backend is not running. Please start it first.")
        sys.exit(1)
    
    # Run tests
    test_minimal_request()
    test_with_metadata()
    
    print("\n" + "="*80)
    print("  Debugging Tips")
    print("="*80)
    print("""
1. Check backend logs for detailed error messages
2. Verify all required fields are being sent
3. Check if Qdrant is accessible
4. Verify environment variables are set correctly
5. Check if CaseModality/CaseMetadata models are correct
6. Look for import errors in backend logs
    """)

