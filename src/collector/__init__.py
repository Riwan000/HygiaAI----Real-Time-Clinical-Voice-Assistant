"""
Open-Access Medical Knowledge Collector

Handles:
- Web crawling for open-access medical sources
- robots.txt compliance
- Document extraction and parsing
- Metadata extraction
- Integration with knowledge ingestion pipeline
"""

from .web_crawler import WebCrawler, CrawlerConfig, CrawlResult
from .robots_parser import RobotsParser
from .document_parser import DocumentParser, ParsedDocument
from .source_config import SourceConfig, MedicalSource, SOURCE_CONFIGS
from .knowledge_collector import KnowledgeCollector
from .scheduler import RescanScheduler, ScanMetrics, DeltaDetector, ScanStateManager

__all__ = [
    "WebCrawler",
    "CrawlerConfig",
    "CrawlResult",
    "RobotsParser",
    "DocumentParser",
    "ParsedDocument",
    "SourceConfig",
    "MedicalSource",
    "SOURCE_CONFIGS",
    "KnowledgeCollector",
    "RescanScheduler",
    "ScanMetrics",
    "DeltaDetector",
    "ScanStateManager"
]

