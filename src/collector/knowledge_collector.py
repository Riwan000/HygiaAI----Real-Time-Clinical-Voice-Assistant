"""
Main Knowledge Collector

Orchestrates crawling, parsing, and storage of open-access medical knowledge.
"""

import logging
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse

from .web_crawler import WebCrawler, CrawlerConfig, CrawlResult
from .source_config import SourceConfig, MedicalSource, SOURCE_CONFIGS
from .document_parser import ParsedDocument
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType

logger = logging.getLogger(__name__)


class KnowledgeCollector:
    """
    Main knowledge collector for open-access medical sources
    
    Features:
    - Crawl multiple medical sources
    - Extract and parse documents
    - Persist raw and parsed data
    - Integrate with knowledge ingestion pipeline
    - Track crawl state and progress
    """
    
    def __init__(
        self,
        storage_directory: str = "data/collected",
        ingestion_pipeline: Optional[KnowledgeIngestionPipeline] = None,
        crawler_config: Optional[CrawlerConfig] = None
    ):
        """
        Initialize knowledge collector
        
        Args:
            storage_directory: Directory to store raw and parsed documents
            ingestion_pipeline: Optional knowledge ingestion pipeline for Qdrant
            crawler_config: Optional crawler configuration
        """
        self.storage_directory = Path(storage_directory)
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.storage_directory / "raw").mkdir(exist_ok=True)
        (self.storage_directory / "parsed").mkdir(exist_ok=True)
        (self.storage_directory / "metadata").mkdir(exist_ok=True)
        
        self.ingestion_pipeline = ingestion_pipeline
        self.crawler = WebCrawler(config=crawler_config)
        
        # Crawl state
        self.crawl_history: List[Dict[str, Any]] = []
        
        logger.info(f"Knowledge collector initialized: {storage_directory}")
    
    def _generate_document_id(self, url: str) -> str:
        """Generate unique document ID from URL"""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def _save_raw_document(self, url: str, content: bytes, content_type: str) -> Path:
        """
        Save raw document to disk
        
        Args:
            url: Document URL
            content: Document content (bytes)
            content_type: Content type
            
        Returns:
            Path to saved file
        """
        doc_id = self._generate_document_id(url)
        
        # Determine file extension
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix or ".html"
        if ext not in [".pdf", ".html", ".xml", ".epub"]:
            ext = ".html"  # Default
        
        file_path = self.storage_directory / "raw" / f"{doc_id}{ext}"
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.debug(f"Saved raw document: {file_path}")
        return file_path
    
    def _save_parsed_document(self, parsed_doc: ParsedDocument) -> Path:
        """
        Save parsed document to disk
        
        Args:
            parsed_doc: Parsed document
            
        Returns:
            Path to saved file
        """
        doc_id = self._generate_document_id(parsed_doc.url)
        file_path = self.storage_directory / "parsed" / f"{doc_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(parsed_doc.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved parsed document: {file_path}")
        return file_path
    
    def _save_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> Path:
        """
        Save document metadata
        
        Args:
            doc_id: Document ID
            metadata: Metadata dictionary
            
        Returns:
            Path to saved metadata file
        """
        file_path = self.storage_directory / "metadata" / f"{doc_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def collect_from_source(
        self,
        source: MedicalSource,
        max_pages: Optional[int] = None
    ) -> List[CrawlResult]:
        """
        Collect documents from a medical source
        
        Args:
            source: Medical source to collect from
            max_pages: Optional maximum pages to collect (overrides config)
            
        Returns:
            List of crawl results
        """
        if source not in SOURCE_CONFIGS:
            raise ValueError(f"Unknown source: {source}")
        
        source_config = SOURCE_CONFIGS[source]
        
        # Override max_pages if provided
        if max_pages:
            source_config = SourceConfig(
                **{**source_config.to_dict(), "max_pages": max_pages}
            )
        
        logger.info(f"Starting collection from {source.value}")
        
        # Crawl source
        results = self.crawler.crawl(source_config)
        
        # Process results
        successful_results = [r for r in results if r.success]
        logger.info(f"Collected {len(successful_results)} documents from {source.value}")
        
        # Save crawl history
        self.crawl_history.append({
            "source": source.value,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "total_urls": len(results),
            "successful": len(successful_results),
            "failed": len(results) - len(successful_results)
        })
        
        return results
    
    def process_and_store(
        self,
        crawl_result: CrawlResult,
        source: MedicalSource,
        domain: Optional[str] = None
    ) -> Optional[str]:
        """
        Process crawl result and store in Qdrant
        
        Args:
            crawl_result: Crawl result to process
            source: Medical source
            domain: Optional domain classification
            
        Returns:
            Point ID if stored in Qdrant, None otherwise
        """
        if not crawl_result.success or not crawl_result.parsed_document:
            return None
        
        parsed_doc = crawl_result.parsed_document
        
        # Prepare document data for ingestion
        document_data = {
            "url": parsed_doc.url,
            "title": parsed_doc.title,
            "content": parsed_doc.content,
            "source": parsed_doc.source,
            "author": parsed_doc.author,
            "year": parsed_doc.year,
            "file_type": parsed_doc.file_type,
            "provenance_url": parsed_doc.url,
            **parsed_doc.metadata
        }
        
        # Create metadata
        metadata = KnowledgeBaseMetadata(
            title=parsed_doc.title,
            source=source.value,
            domain=domain or self._infer_domain(parsed_doc),
            year=parsed_doc.year,
            embedding_type=EmbeddingType.TEXT,
            access_type=AccessType.OPEN,
            provenance_url=parsed_doc.url,
            author=parsed_doc.author
        )
        
        # Ingest into Qdrant if pipeline available
        if self.ingestion_pipeline:
            try:
                point_ids = self.ingestion_pipeline.ingest_document(
                    document_data,
                    metadata=metadata
                )
                logger.info(f"Stored document {parsed_doc.url} in Qdrant: {len(point_ids)} chunks")
                return point_ids[0] if point_ids else None
            except Exception as e:
                logger.error(f"Error ingesting document {parsed_doc.url}: {e}")
                return None
        
        return None
    
    def _infer_domain(self, parsed_doc: ParsedDocument) -> Optional[str]:
        """
        Infer medical domain from document content
        
        Args:
            parsed_doc: Parsed document
            
        Returns:
            Inferred domain or None
        """
        content_lower = parsed_doc.content.lower()
        title_lower = parsed_doc.title.lower()
        text = f"{title_lower} {content_lower}"
        
        # Simple keyword-based domain inference
        domain_keywords = {
            "pathology": ["pathology", "disease", "diagnosis", "biopsy", "histology"],
            "pharmacology": ["drug", "medication", "pharmacology", "dosage", "prescription"],
            "guidelines": ["guideline", "recommendation", "protocol", "standard"],
            "anatomy": ["anatomy", "physiology", "organ", "system"],
            "surgery": ["surgery", "surgical", "procedure", "operation"],
            "pediatrics": ["pediatric", "child", "infant", "neonatal"],
            "cardiology": ["cardiac", "heart", "cardiovascular", "ecg", "echocardiography"],
            "oncology": ["cancer", "tumor", "oncology", "chemotherapy", "malignancy"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text for keyword in keywords):
                return domain
        
        return None
    
    def collect_and_store(
        self,
        source: MedicalSource,
        max_pages: Optional[int] = None,
        store_in_qdrant: bool = True
    ) -> Dict[str, Any]:
        """
        Collect from source and store documents
        
        Args:
            source: Medical source to collect from
            max_pages: Optional maximum pages
            store_in_qdrant: Whether to store in Qdrant
            
        Returns:
            Summary dictionary
        """
        # Collect documents
        results = self.collect_from_source(source, max_pages=max_pages)
        
        successful_results = [r for r in results if r.success]
        stored_count = 0
        
        # Process and store each document
        for result in successful_results:
            # Save raw and parsed documents
            if result.parsed_document:
                # Note: We'd need the raw content to save it
                # For now, just save parsed
                self._save_parsed_document(result.parsed_document)
            
            # Store in Qdrant if requested
            if store_in_qdrant:
                point_id = self.process_and_store(result, source)
                if point_id:
                    stored_count += 1
        
        summary = {
            "source": source.value,
            "total_crawled": len(results),
            "successful": len(successful_results),
            "stored_in_qdrant": stored_count if store_in_qdrant else 0,
            "failed": len(results) - len(successful_results)
        }
        
        logger.info(f"Collection complete: {summary}")
        return summary
    
    def get_crawl_history(self) -> List[Dict[str, Any]]:
        """Get crawl history"""
        return self.crawl_history

