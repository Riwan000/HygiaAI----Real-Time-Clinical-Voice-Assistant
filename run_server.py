#!/usr/bin/env python3
"""
Simple script to run the FastAPI server
"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Only watch the src directory for changes to avoid Windows path length issues
    # with recursive node_modules directories in frontend
    reload_dirs = ["src"]
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=reload_dirs
    )

