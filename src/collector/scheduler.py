"""
Scheduler for Weekly Re-scans and Delta Updates

Handles:
- Scheduled weekly re-scans of knowledge sources
- Delta detection using hashes/ETags
- Version tracking for updated documents
- Logging of added/updated/ignored counts
"""

import logging
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.executors.pool import ThreadPoolExecutor
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("APScheduler not available. Install with: pip install apscheduler")

from .knowledge_collector import KnowledgeCollector
from .source_config import MedicalSource, SOURCE_CONFIGS
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline

logger = logging.getLogger(__name__)


@dataclass
class ScanMetrics:
    """Metrics for a scan operation"""
    source: str
    scan_time: datetime
    total_documents: int = 0
    added: int = 0
    updated: int = 0
    ignored: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source,
            "scan_time": self.scan_time.isoformat(),
            "total_documents": self.total_documents,
            "added": self.added,
            "updated": self.updated,
            "ignored": self.ignored,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds
        }


@dataclass
class DocumentState:
    """State of a document for delta detection"""
    url: str
    hash: str
    etag: Optional[str] = None
    last_modified: Optional[datetime] = None
    version: str = "1.0"
    last_scan: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "url": self.url,
            "hash": self.hash,
            "etag": self.etag,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "version": self.version,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentState":
        """Create from dictionary"""
        return cls(
            url=data["url"],
            hash=data["hash"],
            etag=data.get("etag"),
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None,
            version=data.get("version", "1.0"),
            last_scan=datetime.fromisoformat(data["last_scan"]) if data.get("last_scan") else None
        )


class DeltaDetector:
    """Detects changes in documents using hashes and ETags"""
    
    @staticmethod
    def compute_document_hash(document: Dict[str, Any]) -> str:
        """
        Compute hash for a document
        
        Args:
            document: Document dictionary
            
        Returns:
            SHA-256 hash
        """
        # Create hash from document content
        content = str(document.get("title", "")) + str(document.get("text", "")) + str(document.get("content", ""))
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()
    
    @staticmethod
    def extract_etag(response_headers: Dict[str, Any]) -> Optional[str]:
        """
        Extract ETag from HTTP response headers
        
        Args:
            response_headers: HTTP response headers
            
        Returns:
            ETag value or None
        """
        etag = response_headers.get("ETag") or response_headers.get("etag")
        if etag:
            # Remove quotes if present
            return etag.strip('"')
        return None
    
    @staticmethod
    def extract_last_modified(response_headers: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract Last-Modified from HTTP response headers
        
        Args:
            response_headers: HTTP response headers
            
        Returns:
            Last-Modified datetime or None
        """
        last_modified = response_headers.get("Last-Modified") or response_headers.get("last-modified")
        if last_modified:
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(last_modified)
            except Exception:
                pass
        return None
    
    @staticmethod
    def has_changed(
        current_hash: str,
        current_etag: Optional[str],
        stored_state: Optional[DocumentState]
    ) -> bool:
        """
        Check if document has changed
        
        Args:
            current_hash: Current document hash
            current_etag: Current ETag (if available)
            stored_state: Previously stored document state
            
        Returns:
            True if document has changed
        """
        if not stored_state:
            return True  # New document
        
        # Check hash first (most reliable)
        if current_hash != stored_state.hash:
            return True
        
        # Check ETag if available
        if current_etag and stored_state.etag:
            if current_etag != stored_state.etag:
                return True
        
        return False
    
    @staticmethod
    def increment_version(current_version: str) -> str:
        """
        Increment document version
        
        Args:
            current_version: Current version string (e.g., "1.0")
            
        Returns:
            Incremented version string
        """
        try:
            # Try to parse as float
            version_num = float(current_version)
            # Increment minor version
            new_version = version_num + 0.1
            # Format to one decimal place
            return f"{new_version:.1f}"
        except ValueError:
            # If not a number, append .1
            return f"{current_version}.1"


class ScanStateManager:
    """Manages scan state and document tracking"""
    
    def __init__(self, state_file: str = "data/scan_state.json"):
        """
        Initialize scan state manager
        
        Args:
            state_file: Path to state file
        """
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.document_states: Dict[str, DocumentState] = {}
        self.last_scan_times: Dict[str, datetime] = {}
        self.load_state()
    
    def load_state(self):
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    
                # Load document states
                self.document_states = {
                    url: DocumentState.from_dict(state_data)
                    for url, state_data in data.get("document_states", {}).items()
                }
                
                # Load last scan times
                self.last_scan_times = {
                    source: datetime.fromisoformat(time_str)
                    for source, time_str in data.get("last_scan_times", {}).items()
                }
                
                logger.info(f"Loaded scan state: {len(self.document_states)} documents, {len(self.last_scan_times)} sources")
            except Exception as e:
                logger.error(f"Error loading scan state: {e}")
                self.document_states = {}
                self.last_scan_times = {}
    
    def save_state(self):
        """Save state to file"""
        try:
            data = {
                "document_states": {
                    url: state.to_dict()
                    for url, state in self.document_states.items()
                },
                "last_scan_times": {
                    source: time.isoformat()
                    for source, time in self.last_scan_times.items()
                }
            }
            
            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved scan state: {len(self.document_states)} documents")
        except Exception as e:
            logger.error(f"Error saving scan state: {e}")
    
    def get_document_state(self, url: str) -> Optional[DocumentState]:
        """Get document state by URL"""
        return self.document_states.get(url)
    
    def update_document_state(
        self,
        url: str,
        hash: str,
        etag: Optional[str] = None,
        last_modified: Optional[datetime] = None,
        version: Optional[str] = None
    ):
        """Update document state"""
        existing = self.document_states.get(url)
        
        if existing:
            # Update existing state
            existing.hash = hash
            if etag:
                existing.etag = etag
            if last_modified:
                existing.last_modified = last_modified
            if version:
                existing.version = version
            existing.last_scan = datetime.now(timezone.utc)
        else:
            # Create new state
            self.document_states[url] = DocumentState(
                url=url,
                hash=hash,
                etag=etag,
                last_modified=last_modified,
                version=version or "1.0",
                last_scan=datetime.now(timezone.utc)
            )
    
    def get_last_scan_time(self, source: str) -> Optional[datetime]:
        """Get last scan time for a source"""
        return self.last_scan_times.get(source)
    
    def update_last_scan_time(self, source: str, scan_time: datetime):
        """Update last scan time for a source"""
        self.last_scan_times[source] = scan_time


class RescanScheduler:
    """
    Scheduler for weekly re-scans and delta updates
    
    Features:
    - Weekly scheduled re-scans
    - Delta detection using hashes/ETags
    - Version tracking
    - Metrics logging
    """
    
    def __init__(
        self,
        collector: KnowledgeCollector,
        ingestion_pipeline: KnowledgeIngestionPipeline,
        state_file: str = "data/scan_state.json",
        scan_interval_weeks: int = 1
    ):
        """
        Initialize re-scan scheduler
        
        Args:
            collector: KnowledgeCollector instance
            ingestion_pipeline: KnowledgeIngestionPipeline instance
            state_file: Path to state file
            scan_interval_weeks: Interval between scans in weeks
        """
        if not APSCHEDULER_AVAILABLE:
            raise ImportError("APScheduler is required. Install with: pip install apscheduler")
        
        self.collector = collector
        self.ingestion_pipeline = ingestion_pipeline
        self.state_manager = ScanStateManager(state_file)
        self.delta_detector = DeltaDetector()
        self.scan_interval_weeks = scan_interval_weeks
        
        # Metrics storage
        self.scan_metrics: List[ScanMetrics] = []
        
        # Scheduler
        self.scheduler = BackgroundScheduler(
            executors={"default": ThreadPoolExecutor(max_workers=2)}
        )
        
        logger.info("Re-scan scheduler initialized")
    
    def scan_source(
        self,
        source: MedicalSource,
        max_pages: Optional[int] = None,
        dry_run: bool = False
    ) -> ScanMetrics:
        """
        Scan a source and perform delta ingestion
        
        Args:
            source: Medical source to scan
            max_pages: Optional maximum pages
            dry_run: If True, don't actually ingest
            
        Returns:
            Scan metrics
        """
        start_time = datetime.now(timezone.utc)
        metrics = ScanMetrics(
            source=source.value,
            scan_time=start_time
        )
        
        try:
            logger.info(f"Starting scan for source: {source.value}")
            
            # Collect documents from source
            results = self.collector.collect_from_source(source, max_pages=max_pages)
            successful_results = [r for r in results if r.success and r.parsed_document]
            metrics.total_documents = len(successful_results)
            
            # Process each document
            for result in successful_results:
                if not result.parsed_document:
                    continue
                
                parsed_doc = result.parsed_document
                
                # Prepare document for ingestion
                document_data = {
                    "url": parsed_doc.url,
                    "title": parsed_doc.title,
                    "text": parsed_doc.content,
                    "source": parsed_doc.source,
                    "author": parsed_doc.author,
                    "year": parsed_doc.year,
                    "provenance_url": parsed_doc.url
                }
                
                # Compute hash
                doc_hash = self.delta_detector.compute_document_hash(document_data)
                
                # Get stored state
                stored_state = self.state_manager.get_document_state(parsed_doc.url)
                
                # Check if changed
                has_changed = self.delta_detector.has_changed(
                    current_hash=doc_hash,
                    current_etag=None,  # ETag would come from HTTP response
                    stored_state=stored_state
                )
                
                if not has_changed:
                    metrics.ignored += 1
                    logger.debug(f"Document unchanged: {parsed_doc.url}")
                    continue
                
                # Determine if new or updated
                is_new = stored_state is None
                
                # Increment version if updated
                if is_new:
                    version = "1.0"
                else:
                    version = self.delta_detector.increment_version(stored_state.version)
                
                # Update document data with version
                document_data["version"] = version
                
                if not dry_run:
                    # Ingest document
                    try:
                        point_ids = self.ingestion_pipeline.ingest_document(
                            document_data,
                            force_update=not is_new
                        )
                        
                        if point_ids:
                            if is_new:
                                metrics.added += 1
                            else:
                                metrics.updated += 1
                            
                            # Update state
                            self.state_manager.update_document_state(
                                url=parsed_doc.url,
                                hash=doc_hash,
                                version=version
                            )
                    except Exception as e:
                        logger.error(f"Error ingesting document {parsed_doc.url}: {e}")
                        metrics.errors += 1
                else:
                    # Dry run - just count
                    if is_new:
                        metrics.added += 1
                    else:
                        metrics.updated += 1
            
            # Update last scan time
            self.state_manager.update_last_scan_time(source.value, start_time)
            self.state_manager.save_state()
            
            # Calculate duration
            end_time = datetime.now(timezone.utc)
            metrics.duration_seconds = (end_time - start_time).total_seconds()
            
            # Store metrics
            self.scan_metrics.append(metrics)
            
            logger.info(f"Scan complete for {source.value}: {metrics.added} added, {metrics.updated} updated, {metrics.ignored} ignored")
            
        except Exception as e:
            logger.error(f"Error scanning source {source.value}: {e}")
            metrics.errors += 1
            end_time = datetime.now(timezone.utc)
            metrics.duration_seconds = (end_time - start_time).total_seconds()
        
        return metrics
    
    def schedule_weekly_rescan(
        self,
        sources: Optional[List[MedicalSource]] = None,
        day_of_week: int = 0,  # Monday
        hour: int = 2,  # 2 AM
        minute: int = 0
    ):
        """
        Schedule weekly re-scan
        
        Args:
            sources: List of sources to scan (default: all configured sources)
            day_of_week: Day of week (0=Monday, 6=Sunday)
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
        """
        if sources is None:
            sources = list(SOURCE_CONFIGS.keys())
        
        def scan_job():
            """Job function to run scans"""
            logger.info("Starting scheduled weekly re-scan")
            for source in sources:
                try:
                    self.scan_source(source)
                except Exception as e:
                    logger.error(f"Error in scheduled scan for {source.value}: {e}")
            logger.info("Scheduled weekly re-scan complete")
        
        # Schedule job
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        self.scheduler.add_job(
            scan_job,
            trigger=trigger,
            id="weekly_rescan",
            name="Weekly Knowledge Base Re-scan",
            replace_existing=True
        )
        
        logger.info(f"Scheduled weekly re-scan: Day {day_of_week}, {hour:02d}:{minute:02d}")
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Re-scan scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Re-scan scheduler stopped")
    
    def get_metrics(self, source: Optional[str] = None) -> List[ScanMetrics]:
        """
        Get scan metrics
        
        Args:
            source: Optional source filter
            
        Returns:
            List of scan metrics
        """
        if source:
            return [m for m in self.scan_metrics if m.source == source]
        return self.scan_metrics
    
    def get_last_scan_time(self, source: str) -> Optional[datetime]:
        """Get last scan time for a source"""
        return self.state_manager.get_last_scan_time(source)

