"""
Configuration management utilities
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get configuration value from environment
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    return os.getenv(key, default)


def get_deepgram_api_key() -> str:
    """Get Deepgram API key from environment"""
    api_key = get_config("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
    return api_key

