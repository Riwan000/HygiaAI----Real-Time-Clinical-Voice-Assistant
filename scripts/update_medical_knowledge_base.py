#!/usr/bin/env python3
"""
Automated Medical Knowledge Base Update

This script updates the medical knowledge base regularly by:
1. Checking for updates from internet sources
2. Detecting changes in existing documents
3. Adding new knowledge
4. Tracking versions and update history
5. Sending notifications on updates

Can be run manually or scheduled via cron/task scheduler.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import logging
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings import BioBERTEmbeddingGenerator
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType

# Import knowledge fetching functions
from scripts.fetch_medical_knowledge_from_internet import (
    fetch_who_guideline,
    fetch_cdc_guideline,
    fetch_medical_reference_content,
    MEDICAL_SOURCES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Update tracking file
UPDATE_TRACKING_FILE = Path(project_root) / "data" / "knowledge_base_updates.json"


class KnowledgeBaseUpdater:
    """Manages regular updates to the medical knowledge base"""
    
    def __init__(
        self,
        qdrant_storage: Optional[QdrantStorage] = None,
        update_frequency_days: int = 7
    ):
        """
        Initialize knowledge base updater
        
        Args:
            qdrant_storage: Optional QdrantStorage instance
            update_frequency_days: How often to check for updates (default: 7 days)
        """
        import os
        
        if qdrant_storage:
            self.storage = qdrant_storage
        else:
            self.storage = QdrantStorage(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6334")),
                collection_name="hygiaai_knowledge_base",
                vector_size=768,
                enable_encryption=False,
                enable_deidentification=False
            )
        
        # Initialize embedding generator
        try:
            self.embedding_generator = BioBERTEmbeddingGenerator()
        except Exception as e:
            logger.warning(f"BioBERT initialization failed: {e}")
            self.embedding_generator = None
        
        def text_embedding_fn(text: str):
            if self.embedding_generator:
                return self.embedding_generator.generate_embedding(text)
            return [0.0] * 768
        
        self.ingestion_pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=self.storage,
            text_embedding_generator=text_embedding_fn,
            chunk_size=512,
            chunk_overlap=50,
            validate_schema=False,
            enforce_open_access=False
        )
        
        self.update_frequency_days = update_frequency_days
        self.update_history = self._load_update_history()
        
        logger.info("Knowledge base updater initialized")
    
    def _load_update_history(self) -> Dict[str, Any]:
        """Load update history from file"""
        if UPDATE_TRACKING_FILE.exists():
            try:
                with open(UPDATE_TRACKING_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading update history: {e}")
        
        return {
            "last_update": None,
            "update_frequency_days": self.update_frequency_days,
            "update_history": [],
            "document_versions": {}
        }
    
    def _save_update_history(self):
        """Save update history to file"""
        # Ensure directory exists
        UPDATE_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(UPDATE_TRACKING_FILE, 'w') as f:
                json.dump(self.update_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving update history: {e}")
    
    def _get_document_hash(self, document: Dict[str, Any]) -> str:
        """Generate hash for document to detect changes"""
        content = str(document.get("title", "")) + str(document.get("content", ""))
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _check_if_update_needed(self) -> bool:
        """Check if update is needed based on frequency"""
        last_update = self.update_history.get("last_update")
        
        if not last_update:
            return True
        
        try:
            last_update_date = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
            days_since_update = (datetime.now(timezone.utc) - last_update_date).days
            return days_since_update >= self.update_frequency_days
        except:
            return True
    
    def _check_document_changes(
        self,
        document: Dict[str, Any],
        doc_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if document has changed
        
        Returns:
            (has_changed, old_hash)
        """
        new_hash = self._get_document_hash(document)
        old_hash = self.update_history.get("document_versions", {}).get(doc_id)
        
        if old_hash and old_hash == new_hash:
            return False, old_hash
        
        return True, old_hash
    
    def update_knowledge_base(
        self,
        force_update: bool = False,
        check_changes: bool = True
    ) -> Dict[str, Any]:
        """
        Update knowledge base with latest information
        
        Args:
            force_update: Force update even if not needed
            check_changes: Check for changes before updating
            
        Returns:
            Update statistics
        """
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checked": False,
            "update_needed": False,
            "documents_checked": 0,
            "documents_updated": 0,
            "documents_new": 0,
            "documents_unchanged": 0,
            "errors": 0,
            "updated_documents": []
        }
        
        # Check if update is needed
        if not force_update and not self._check_if_update_needed():
            logger.info("Update not needed yet (within frequency window)")
            stats["checked"] = True
            stats["update_needed"] = False
            return stats
        
        stats["checked"] = True
        stats["update_needed"] = True
        
        logger.info("Starting knowledge base update...")
        
        # Fetch all medical knowledge
        all_knowledge = []
        
        # Fetch WHO guidelines
        logger.info("Checking WHO guidelines for updates...")
        for topic in MEDICAL_SOURCES["who_guidelines"]["topics"]:
            guideline = fetch_who_guideline(topic)
            if guideline:
                guideline["doc_id"] = f"who_{topic}"
                all_knowledge.append(guideline)
        
        # Fetch CDC guidelines
        logger.info("Checking CDC guidelines for updates...")
        for topic in MEDICAL_SOURCES["cdc_guidelines"]["topics"]:
            guideline = fetch_cdc_guideline(topic)
            if guideline:
                guideline["doc_id"] = f"cdc_{topic.replace('/', '_')}"
                all_knowledge.append(guideline)
        
        # Fetch medical references
        logger.info("Checking medical references for updates...")
        references = fetch_medical_reference_content()
        for i, ref in enumerate(references):
            ref["doc_id"] = f"medical_ref_{i}"
            all_knowledge.append(ref)
        
        stats["documents_checked"] = len(all_knowledge)
        
        # Process each document
        for doc in all_knowledge:
            doc_id = doc.get("doc_id", doc.get("title", "").lower().replace(" ", "_"))
            
            try:
                # Check if document has changed
                has_changed, old_hash = self._check_document_changes(doc, doc_id)
                
                if not has_changed and check_changes:
                    stats["documents_unchanged"] += 1
                    logger.debug(f"Document unchanged: {doc.get('title')}")
                    continue
                
                # Prepare document for ingestion
                document = {
                    "title": doc["title"],
                    "text": doc["content"],
                    "content": doc["content"],
                    "source": doc["source"],
                    "domain": doc.get("domain", "clinical_reference"),
                    "year": doc.get("year", datetime.now(timezone.utc).year),
                    "provenance_url": doc.get("provenance_url", f"https://hygiaai.internal/knowledge/{doc_id}"),
                    "author": doc.get("author", "Medical Source"),
                    "version": "1.0"
                }
                
                metadata = KnowledgeBaseMetadata(
                    title=doc["title"],
                    source=doc["source"],
                    domain=doc.get("domain", "clinical_reference"),
                    year=doc.get("year", datetime.now(timezone.utc).year),
                    embedding_type=EmbeddingType.TEXT,
                    access_type=AccessType.OPEN,
                    provenance_url=doc.get("provenance_url", document["provenance_url"]),
                    author=doc.get("author", "Medical Source"),
                    version="1.0"
                )
                
                # Ingest document (force update if changed)
                point_ids = self.ingestion_pipeline.ingest_document(
                    document,
                    metadata=metadata,
                    force_update=has_changed
                )
                
                if point_ids:
                    # Update tracking
                    new_hash = self._get_document_hash(doc)
                    if doc_id not in self.update_history.get("document_versions", {}):
                        stats["documents_new"] += 1
                        logger.info(f"✓ New document: {doc.get('title')}")
                    else:
                        stats["documents_updated"] += 1
                        logger.info(f"✓ Updated document: {doc.get('title')}")
                    
                    self.update_history.setdefault("document_versions", {})[doc_id] = new_hash
                    stats["updated_documents"].append({
                        "doc_id": doc_id,
                        "title": doc.get("title"),
                        "status": "new" if not old_hash else "updated",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                else:
                    stats["documents_unchanged"] += 1
                    
            except Exception as e:
                logger.error(f"Error updating document {doc.get('title')}: {e}")
                stats["errors"] += 1
        
        # Update history
        self.update_history["last_update"] = datetime.now(timezone.utc).isoformat()
        self.update_history["update_history"].append(stats)
        
        # Keep only last 50 update records
        if len(self.update_history["update_history"]) > 50:
            self.update_history["update_history"] = self.update_history["update_history"][-50:]
        
        self._save_update_history()
        
        logger.info(f"Update complete: {stats['documents_updated']} updated, {stats['documents_new']} new, {stats['documents_unchanged']} unchanged")
        
        return stats
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status"""
        last_update = self.update_history.get("last_update")
        days_since_update = None
        
        if last_update:
            try:
                last_update_date = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                days_since_update = (datetime.now(timezone.utc) - last_update_date).days
            except:
                pass
        
        return {
            "last_update": last_update,
            "days_since_update": days_since_update,
            "update_frequency_days": self.update_frequency_days,
            "update_needed": self._check_if_update_needed(),
            "total_documents": len(self.update_history.get("document_versions", {})),
            "recent_updates": self.update_history.get("update_history", [])[-5:]
        }


def update_knowledge_base(force: bool = False):
    """Main function to update knowledge base"""
    print("=" * 80)
    print("  Medical Knowledge Base Update")
    print("=" * 80)
    print()
    
    updater = KnowledgeBaseUpdater()
    
    # Check status
    status = updater.get_update_status()
    print(f"📊 Update Status:")
    print(f"   Last update: {status['last_update'] or 'Never'}")
    if status['days_since_update'] is not None:
        print(f"   Days since update: {status['days_since_update']}")
    print(f"   Update frequency: Every {status['update_frequency_days']} days")
    print(f"   Update needed: {'Yes' if status['update_needed'] or force else 'No'}")
    print(f"   Total documents tracked: {status['total_documents']}")
    print()
    
    if not status['update_needed'] and not force:
        print("ℹ️  Update not needed yet. Use --force to update anyway.")
        return
    
    # Perform update
    print("🔄 Starting update...")
    print()
    
    stats = updater.update_knowledge_base(force_update=force)
    
    # Print results
    print("=" * 80)
    print("  Update Results")
    print("=" * 80)
    print(f"✅ Documents checked: {stats['documents_checked']}")
    print(f"✅ Documents updated: {stats['documents_updated']}")
    print(f"✅ Documents new: {stats['documents_new']}")
    print(f"✅ Documents unchanged: {stats['documents_unchanged']}")
    if stats['errors'] > 0:
        print(f"⚠️  Errors: {stats['errors']}")
    print()
    
    if stats['updated_documents']:
        print("📝 Updated Documents:")
        for doc in stats['updated_documents']:
            print(f"   - {doc['title']} ({doc['status']})")
        print()
    
    print("✅ Knowledge base update complete!")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update medical knowledge base")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update even if not needed"
    )
    parser.add_argument(
        "--frequency",
        type=int,
        default=7,
        help="Update frequency in days (default: 7)"
    )
    
    args = parser.parse_args()
    
    if args.frequency != 7:
        # Update frequency in tracking file
        updater = KnowledgeBaseUpdater(update_frequency_days=args.frequency)
        updater.update_history["update_frequency_days"] = args.frequency
        updater._save_update_history()
        print(f"✅ Update frequency set to {args.frequency} days")
    
    update_knowledge_base(force=args.force)

