#!/usr/bin/env python3
"""
Quick script to add Google Gemini API key to .env file
"""

import os
import sys

def setup_gemini_key():
    """Add or update GOOGLE_API_KEY in .env file"""
    
    env_file = ".env"
    
    # Check if .env exists
    if not os.path.exists(env_file):
        print(f"⚠️  {env_file} file not found. Creating it...")
        with open(env_file, "w") as f:
            f.write("# Environment Variables\n\n")
    
    # Read existing .env
    lines = []
    key_found = False
    
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
    
    # Check if GOOGLE_API_KEY already exists
    for i, line in enumerate(lines):
        if line.strip().startswith("GOOGLE_API_KEY="):
            key_found = True
            print(f"✓ Found existing GOOGLE_API_KEY at line {i+1}")
            break
    
    # Get API key from user
    print("\n" + "="*60)
    print("Google Gemini API Key Setup")
    print("="*60)
    
    if key_found:
        print("\n⚠️  GOOGLE_API_KEY already exists in .env file")
        response = input("Do you want to update it? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled. No changes made.")
            return
    
    print("\n📋 Paste your Gemini API key from Google AI Studio:")
    print("   (It should start with 'AIza...')")
    api_key = input("\nAPI Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    if not api_key.startswith("AIza"):
        print("⚠️  Warning: API key doesn't start with 'AIza'. Are you sure it's correct?")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return
    
    # Update or add the key
    if key_found:
        # Update existing line
        for i, line in enumerate(lines):
            if line.strip().startswith("GOOGLE_API_KEY="):
                lines[i] = f"GOOGLE_API_KEY={api_key}\n"
                break
    else:
        # Add new line
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"GOOGLE_API_KEY={api_key}\n")
    
    # Write back to .env
    with open(env_file, "w") as f:
        f.writelines(lines)
    
    print("\n✅ Successfully added GOOGLE_API_KEY to .env file!")
    print("\n📝 Next steps:")
    print("   1. Restart your backend server if it's running")
    print("   2. Test the connection with: python -c \"import google.generativeai as genai; import os; from dotenv import load_dotenv; load_dotenv(); genai.configure(api_key=os.getenv('GOOGLE_API_KEY')); model = genai.GenerativeModel('gemini-1.5-pro'); print('✅ Connection successful!')\"")

if __name__ == "__main__":
    try:
        setup_gemini_key()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

