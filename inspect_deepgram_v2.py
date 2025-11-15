"""Inspect Deepgram v2 SDK structure"""
import os
os.environ['DEEPGRAM_API_KEY'] = 'test_key'

from deepgram import Deepgram

try:
    dg = Deepgram('test_key')
    print("✓ Deepgram initialized")
    
    # Check transcription
    if hasattr(dg, 'transcription'):
        t = dg.transcription
        print(f"\nTranscription type: {type(t).__name__}")
        print(f"Transcription methods: {[x for x in dir(t) if not x.startswith('_')]}")
        
        # Check sync_prerecorded
        if hasattr(t, 'sync_prerecorded'):
            sync = t.sync_prerecorded
            print(f"\nsync_prerecorded type: {type(sync).__name__}")
            print(f"sync_prerecorded methods: {[x for x in dir(sync) if not x.startswith('_')]}")
            
            # Try to get method signature
            if hasattr(sync, '__call__'):
                import inspect
                try:
                    sig = inspect.signature(sync)
                    print(f"sync_prerecorded signature: {sig}")
                except:
                    print("Could not get signature")
        
        # Check prerecorded
        if hasattr(t, 'prerecorded'):
            pre = t.prerecorded
            print(f"\nprerecorded type: {type(pre).__name__}")
            print(f"prerecorded methods: {[x for x in dir(pre) if not x.startswith('_')]}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

