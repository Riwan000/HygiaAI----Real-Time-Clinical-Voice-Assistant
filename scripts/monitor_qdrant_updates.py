#!/usr/bin/env python3
"""
Monitor Qdrant Database Updates in Real-Time

This script monitors Qdrant collections and shows updates as they happen.
Useful for verifying that data ingestion is working correctly.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)


class QdrantMonitor:
    """Monitor Qdrant collections for updates"""
    
    def __init__(self):
        self.collections = [
            "clinical_kb_collection",
            "patient_memory_collection",
            "hygiaai_cases"
        ]
        self.last_counts: Dict[str, int] = {}
        self.last_timestamps: Dict[str, str] = {}
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get current point count for a collection"""
        try:
            qdrant_url = os.getenv("QDRANT_URL")
            if qdrant_url:
                storage = QdrantStorage(
                    url=qdrant_url,
                    api_key=os.getenv("QDRANT_API_KEY"),
                    collection_name=collection_name,
                    vector_size=768
                )
            else:
                storage = QdrantStorage(
                    host=os.getenv("QDRANT_HOST", "localhost"),
                    port=int(os.getenv("QDRANT_PORT", "6334")),
                    api_key=os.getenv("QDRANT_API_KEY"),
                    collection_name=collection_name,
                    vector_size=768
                )
            
            collection_info = storage.get_collection_info()
            return collection_info.get("points_count", 0)
        except Exception as e:
            return -1  # Error indicator
    
    def monitor(self, interval: int = 5):
        """Monitor collections for updates"""
        print("="*80)
        print("  Qdrant Database Update Monitor")
        print("="*80)
        print(f"\nMonitoring collections: {', '.join(self.collections)}")
        print(f"Update interval: {interval} seconds")
        print(f"Press Ctrl+C to stop\n")
        
        # Initialize baseline counts
        print("📊 Initializing baseline counts...")
        for collection in self.collections:
            count = self.get_collection_count(collection)
            self.last_counts[collection] = count
            self.last_timestamps[collection] = datetime.now(timezone.utc).isoformat()
            if count >= 0:
                print(f"  ✓ {collection}: {count:,} points")
            else:
                print(f"  ✗ {collection}: Error connecting")
        
        print(f"\n{'='*80}")
        print("  Monitoring Updates (Press Ctrl+C to stop)")
        print(f"{'='*80}\n")
        
        try:
            while True:
                updates_detected = False
                
                for collection in self.collections:
                    current_count = self.get_collection_count(collection)
                    
                    if current_count < 0:
                        print(f"⚠️  {collection}: Connection error")
                        continue
                    
                    last_count = self.last_counts.get(collection, 0)
                    
                    if current_count != last_count:
                        updates_detected = True
                        diff = current_count - last_count
                        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
                        
                        if diff > 0:
                            print(f"🟢 [{timestamp}] {collection}: +{diff:,} points (Total: {current_count:,})")
                        else:
                            print(f"🔴 [{timestamp}] {collection}: {diff:,} points (Total: {current_count:,})")
                        
                        self.last_counts[collection] = current_count
                        self.last_timestamps[collection] = datetime.now(timezone.utc).isoformat()
                
                if not updates_detected:
                    # Show current status every 30 seconds
                    if int(time.time()) % 30 == 0:
                        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
                        status_line = " | ".join([
                            f"{col}: {self.last_counts.get(col, 0):,}"
                            for col in self.collections
                        ])
                        print(f"⏱️  [{timestamp}] Status: {status_line}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n{'='*80}")
            print("  Monitoring Stopped")
            print(f"{'='*80}")
            print("\n📊 Final Status:")
            for collection in self.collections:
                count = self.last_counts.get(collection, 0)
                timestamp = self.last_timestamps.get(collection, "N/A")
                print(f"  - {collection}: {count:,} points (Last update: {timestamp})")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Qdrant database updates")
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Update check interval in seconds (default: 5)"
    )
    
    args = parser.parse_args()
    
    monitor = QdrantMonitor()
    monitor.monitor(interval=args.interval)


if __name__ == "__main__":
    main()

