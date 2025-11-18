#!/usr/bin/env python3
"""
Startup script for Railway deployment
Provides better error handling and logging
"""
import sys
import os
import subprocess

def main():
    # Set up logging to stderr (Railway captures this)
    port = os.getenv("PORT", "8000")
    
    print(f"=== Starting HygiaAI API Server ===", file=sys.stderr)
    print(f"Python version: {sys.version}", file=sys.stderr)
    print(f"PORT: {port}", file=sys.stderr)
    print(f"PATH: {os.getenv('PATH', '')}", file=sys.stderr)
    print(f"Working directory: {os.getcwd()}", file=sys.stderr)
    
    # Verify uvicorn is available - check PATH first, then import
    print("Checking for uvicorn...", file=sys.stderr)
    try:
        import shutil
        uvicorn_path = shutil.which("uvicorn")
        if uvicorn_path:
            print(f"uvicorn found in PATH: {uvicorn_path}", file=sys.stderr)
    except Exception:
        pass  # shutil might not be available, but that's okay
    
    # Always import uvicorn module (required for uvicorn.run())
    try:
        import uvicorn
        print(f"uvicorn module imported: {uvicorn.__file__}", file=sys.stderr)
    except ImportError:
        print("ERROR: uvicorn module not found. Trying to import from .local", file=sys.stderr)
        # Try adding .local/bin to path
        local_bin = os.path.expanduser("~/.local/bin")
        if local_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"
            print(f"Added {local_bin} to PATH", file=sys.stderr)
        try:
            import uvicorn
            print(f"uvicorn found after path adjustment: {uvicorn.__file__}", file=sys.stderr)
        except ImportError:
            print("ERROR: uvicorn still not found", file=sys.stderr)
            print("PATH:", os.environ.get("PATH", ""), file=sys.stderr)
            sys.exit(1)
    
    # Verify python-multipart is installed (required for FastAPI form data)
    print("Checking for python-multipart...", file=sys.stderr)
    try:
        import multipart
        print(f"python-multipart found: {multipart.__file__}", file=sys.stderr)
    except ImportError:
        print("WARNING: python-multipart not found. FastAPI form data may fail.", file=sys.stderr)
        print("Attempting to install python-multipart...", file=sys.stderr)
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "python-multipart>=0.0.6"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print("python-multipart installed successfully", file=sys.stderr)
            else:
                print(f"Failed to install python-multipart: {result.stderr}", file=sys.stderr)
        except Exception as install_error:
            print(f"Error installing python-multipart: {install_error}", file=sys.stderr)
    
    # Verify the app module can be imported
    print("Verifying app module can be imported...", file=sys.stderr)
    try:
        from src.api.main import app
        print("App imported successfully", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Failed to import app module: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    
    # Start the server
    print(f"Starting uvicorn server on port {port}...", file=sys.stderr)
    print(f"Server will listen on 0.0.0.0:{port}", file=sys.stderr)
    print(f"Health endpoint will be available at http://0.0.0.0:{port}/health", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    sys.stderr.flush()
    
    # Use uvicorn.run directly instead of subprocess for better error handling
    # Ensure we bind to 0.0.0.0 to accept connections from Railway's healthcheck
    try:
        print("Starting uvicorn...", file=sys.stderr)
        sys.stderr.flush()
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",  # Must be 0.0.0.0 to accept Railway healthcheck connections
            port=int(port),
            log_level="info",
            access_log=True  # Enable access logs to see healthcheck requests
        )
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Failed to start uvicorn server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

