#!/usr/bin/env python3
"""
Helper script to set up Qdrant Cloud configuration in .env file
"""

import os
import sys

def setup_qdrant_cloud():
    """Add QDRANT_URL and QDRANT_API_KEY to .env file"""
    
    env_file = ".env"
    
    # Check if .env exists
    if not os.path.exists(env_file):
        print(f"⚠️  {env_file} file not found. Creating it...")
        with open(env_file, "w") as f:
            f.write("# Environment Variables\n\n")
    
    # Read existing .env
    lines = []
    url_found = False
    key_found = False
    
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
    
    # Check if QDRANT_URL already exists
    for i, line in enumerate(lines):
        if line.strip().startswith("QDRANT_URL="):
            url_found = True
            url_line_idx = i
        if line.strip().startswith("QDRANT_API_KEY="):
            key_found = True
            key_line_idx = i
    
    print("\n" + "="*60)
    print("Qdrant Cloud Setup")
    print("="*60)
    
    # Get Qdrant URL
    if url_found:
        print("\n⚠️  QDRANT_URL already exists in .env file")
        response = input("Do you want to update it? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping URL update.")
            url_to_set = None
        else:
            print("\n📋 Enter your Qdrant Cloud URL:")
            print("   Example: https://c92cec87-f4ea-4566-abd9-abc4fbc17f60.us-east4-0.gcp.cloud.qdrant.io:6333")
            url_to_set = input("\nQDRANT_URL: ").strip()
    else:
        print("\n📋 Enter your Qdrant Cloud URL:")
        print("   Example: https://c92cec87-f4ea-4566-abd9-abc4fbc17f60.us-east4-0.gcp.cloud.qdrant.io:6333")
        url_to_set = input("\nQDRANT_URL: ").strip()
    
    # Get Qdrant API Key
    if key_found:
        print("\n⚠️  QDRANT_API_KEY already exists in .env file")
        response = input("Do you want to update it? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping API key update.")
            key_to_set = None
        else:
            print("\n📋 Enter your Qdrant API Key:")
            print("   (It should be a JWT token)")
            key_to_set = input("\nQDRANT_API_KEY: ").strip()
    else:
        print("\n📋 Enter your Qdrant API Key:")
        print("   (It should be a JWT token)")
        key_to_set = input("\nQDRANT_API_KEY: ").strip()
    
    # Update or add the values
    if url_to_set:
        if url_found:
            lines[url_line_idx] = f"QDRANT_URL={url_to_set}\n"
        else:
            if lines and not lines[-1].endswith("\n"):
                lines.append("\n")
            lines.append(f"QDRANT_URL={url_to_set}\n")
    
    if key_to_set:
        if key_found:
            lines[key_line_idx] = f"QDRANT_API_KEY={key_to_set}\n"
        else:
            if lines and not lines[-1].endswith("\n"):
                lines.append("\n")
            lines.append(f"QDRANT_API_KEY={key_to_set}\n")
    
    # Write back to .env
    with open(env_file, "w") as f:
        f.writelines(lines)
    
    print("\n✅ Successfully updated .env file!")
    print("\n📝 Configuration:")
    if url_to_set:
        print(f"   QDRANT_URL={url_to_set[:50]}...")
    if key_to_set:
        print(f"   QDRANT_API_KEY={key_to_set[:20]}...")
    
    print("\n🧪 Testing connection...")
    print("   Run: python test_qdrant_connection.py")

if __name__ == "__main__":
    try:
        setup_qdrant_cloud()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

