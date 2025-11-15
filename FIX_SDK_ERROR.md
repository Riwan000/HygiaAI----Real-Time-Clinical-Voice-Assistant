# Fix Deepgram SDK Structure Error

If you're getting the error:
```
Deepgram SDK structure error: Deepgram SDK structure not recognized. 
Listen type: ListenRouter, Available attributes: [...]
```

## Quick Fix

Run this command to clear cache and test:

```bash
python clear_cache_and_test.py
```

## Manual Fix Steps

### 1. Clear Python Cache

**Windows PowerShell:**
```powershell
Get-ChildItem -Path . -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
```

**Windows CMD:**
```cmd
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
for /r . %f in (*.pyc) do @if exist "%f" del /f /q "%f"
```

**Linux/Mac:**
```bash
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### 2. Restart Your Python Environment

- **If using an IDE (VS Code, PyCharm, etc.)**: Restart the IDE completely
- **If using a terminal**: Close and reopen the terminal
- **If using Jupyter**: Restart the kernel

### 3. Test Again

```bash
python examples/test_asr_simple.py
```

## Why This Happens

Python caches compiled bytecode (`.pyc` files) in `__pycache__` directories. When you update code, sometimes Python uses the old cached version instead of the new code.

## Prevention

The code has been updated to:
- Use `getattr()` instead of `hasattr()` for more reliable attribute access
- Check both `'v1' in available_attrs` and `hasattr()` for compatibility
- Add error handling around SDK structure access

## Verify Your SDK Version

```bash
python -c "import deepgram; print(deepgram.__version__)"
```

Should show: `5.3.0` or similar

## Still Having Issues?

1. Make sure you're using the latest code (pull latest changes)
2. Verify your Deepgram SDK version: `pip install --upgrade deepgram-sdk`
3. Check that `src/transcription/deepgram_client.py` has the latest changes
4. Try running with `-B` flag to disable bytecode: `python -B examples/test_asr_simple.py`


