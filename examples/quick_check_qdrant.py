"""
Quick Qdrant Check Script

A simple script to quickly verify Qdrant is running and accessible.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qdrant_client import QdrantClient
import requests

def quick_check():
    """Quick check of Qdrant instance"""
    print("=" * 60)
    print("Quick Qdrant Check")
    print("=" * 60)
    print()
    
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6334"))
    
    # Check 1: Connection
    print(f"1. Checking connection to {host}:{port}...")
    try:
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections()
        print(f"   ✅ Connected successfully!")
        print(f"   Found {len(collections.collections)} collection(s)")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    print()
    
    # Check 2: Collections
    print("2. Checking collections...")
    try:
        collections = client.get_collections()
        expected = ["hygiaai_transcripts", "hygiaai_knowledge_base", "hygiaai_cases"]
        found = [c.name for c in collections.collections]
        
        for name in expected:
            if name in found:
                info = client.get_collection(name)
                points = info.points_count if hasattr(info, 'points_count') else 0
                print(f"   ✅ {name} ({points} points)")
            else:
                print(f"   ❌ {name} - Not found")
    except Exception as e:
        print(f"   ❌ Error checking collections: {e}")
        return False
    
    print()
    
    # Check 3: API Health
    print("3. Checking API health...")
    try:
        # Try the root endpoint
        response = requests.get(f"http://{host}:{port}/", timeout=2)
        if response.status_code in [200, 404]:  # 404 is OK for root
            print(f"   ✅ API is responding (status: {response.status_code})")
        else:
            print(f"   ⚠️  API returned status: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Could not check API: {e}")
    
    print()
    
    # Check 4: Dashboard
    print("4. Dashboard access...")
    print(f"   🌐 Open in browser: http://{host}:{port}/dashboard")
    
    print()
    print("=" * 60)
    print("✅ Quick check complete!")
    print("=" * 60)
    print()
    print("For detailed testing, run:")
    print("  python examples/test_qdrant_isolated_instance.py")
    print()
    
    return True

if __name__ == "__main__":
    quick_check()

