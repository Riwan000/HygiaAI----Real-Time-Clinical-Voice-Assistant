"""
Web Crawler for Open-Access Medical Sources

Crawls medical knowledge sources while respecting robots.txt and extracting documents.
"""

import logging
import re
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin, urlunparse
from pathlib import Path
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .robots_parser import RobotsParser
from .document_parser import DocumentParser, ParsedDocument
from .source_config import SourceConfig, MedicalSource

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result of crawling a URL"""
    url: str
    success: bool
    parsed_document: Optional[ParsedDocument] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    crawled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "url": self.url,
            "success": self.success,
            "status_code": self.status_code,
            "crawled_at": self.crawled_at.isoformat()
        }
        
        if self.parsed_document:
            result["parsed_document"] = self.parsed_document.to_dict()
        if self.error:
            result["error"] = self.error
        
        return result


@dataclass
class CrawlerConfig:
    """Configuration for web crawler"""
    user_agent: str = "HygiaAI-Collector/1.0"
    timeout: int = 30
    max_retries: int = 3
    respect_robots: bool = True
    crawl_delay: float = 1.0
    max_concurrent: int = 1
    allowed_file_types: List[str] = field(default_factory=lambda: [".pdf", ".html", ".xml", ".epub"])
    follow_external_links: bool = False
    max_depth: int = 3
    max_pages: int = 1000


class WebCrawler:
    """
    Web crawler for open-access medical sources
    
    Features:
    - Respects robots.txt
    - Filters URLs by file type
    - Extracts documents and metadata
    - Polite crawling with delays
    - Retry logic
    """
    
    def __init__(self, config: Optional[CrawlerConfig] = None):
        """
        Initialize web crawler
        
        Args:
            config: Optional crawler configuration
        """
        self.config = config or CrawlerConfig()
        self.robots_parser = RobotsParser(user_agent=self.config.user_agent) if self.config.respect_robots else None
        self.document_parser = DocumentParser()
        
        # Session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({"User-Agent": self.config.user_agent})
        
        # Crawl state
        self.visited_urls: Set[str] = set()
        self.crawl_results: List[CrawlResult] = []
        
        logger.info("Web crawler initialized")
    
    def _is_allowed_file_type(self, url: str) -> bool:
        """
        Check if URL points to an allowed file type
        
        Args:
            url: URL to check
            
        Returns:
            True if file type is allowed
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for file_type in self.config.allowed_file_types:
            if path.endswith(file_type):
                return True
        
        # If no extension, allow HTML by default
        if not Path(path).suffix:
            return True
        
        return False
    
    def _extract_links(self, html_content: str, base_url: str, allowed_domains: List[str]) -> List[str]:
        """
        Extract links from HTML content
        
        Args:
            html_content: HTML content
            base_url: Base URL for resolving relative links
            allowed_domains: List of allowed domains
            
        Returns:
            List of absolute URLs
        """
        links = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(base_url, href)
                
                # Parse URL
                parsed = urlparse(absolute_url)
                
                # Check if domain is allowed
                if any(domain in parsed.netloc for domain in allowed_domains):
                    # Remove fragment
                    clean_url = urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        ''  # Remove fragment
                    ))
                    links.append(clean_url)
        except Exception as e:
            logger.warning(f"Error extracting links from {base_url}: {e}")
        
        return links
    
    def crawl_url(
        self,
        url: str,
        source_config: Optional[SourceConfig] = None
    ) -> CrawlResult:
        """
        Crawl a single URL
        
        Args:
            url: URL to crawl
            source_config: Optional source configuration
            
        Returns:
            CrawlResult object
        """
        # Check if already visited
        if url in self.visited_urls:
            return CrawlResult(url=url, success=False, error="Already visited")
        
        # Check robots.txt
        if self.robots_parser and not self.robots_parser.can_fetch(url):
            logger.info(f"URL not allowed by robots.txt: {url}")
            return CrawlResult(url=url, success=False, error="Disallowed by robots.txt")
        
        # Check file type
        if not self._is_allowed_file_type(url):
            logger.debug(f"URL not in allowed file types: {url}")
            return CrawlResult(url=url, success=False, error="File type not allowed")
        
        # Wait for crawl delay
        if self.robots_parser:
            self.robots_parser.wait_if_needed(url)
        else:
            time.sleep(self.config.crawl_delay)
        
        # Fetch URL
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            
            # Parse document
            content_type = response.headers.get('Content-Type', '')
            parsed_doc = self.document_parser.parse_document(
                content=response.content,
                url=url,
                content_type=content_type
            )
            
            self.visited_urls.add(url)
            result = CrawlResult(
                url=url,
                success=True,
                parsed_document=parsed_doc,
                status_code=response.status_code
            )
            self.crawl_results.append(result)
            
            logger.info(f"Successfully crawled: {url} ({parsed_doc.file_type})")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.warning(f"Error crawling {url}: {error_msg}")
            result = CrawlResult(
                url=url,
                success=False,
                error=error_msg,
                status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            )
            self.crawl_results.append(result)
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error crawling {url}: {e}")
            result = CrawlResult(
                url=url,
                success=False,
                error=error_msg
            )
            self.crawl_results.append(result)
            return result
    
    def crawl(
        self,
        source_config: SourceConfig,
        start_urls: Optional[List[str]] = None
    ) -> List[CrawlResult]:
        """
        Crawl a source starting from seed URLs
        
        Args:
            source_config: Source configuration
            start_urls: Optional list of start URLs (overrides config)
            
        Returns:
            List of crawl results
        """
        start_urls = start_urls or source_config.start_urls
        to_visit: List[tuple[str, int]] = [(url, 0) for url in start_urls]  # (url, depth)
        visited = set()
        results = []
        
        logger.info(f"Starting crawl for {source_config.source.value} from {len(start_urls)} seed URLs")
        
        while to_visit and len(results) < source_config.max_pages:
            url, depth = to_visit.pop(0)
            
            # Skip if already visited or too deep
            if url in visited or depth > source_config.crawl_depth:
                continue
            
            visited.add(url)
            
            # Crawl URL
            result = self.crawl_url(url, source_config)
            results.append(result)
            
            # If successful and HTML, extract links for further crawling
            if result.success and result.parsed_document:
                if result.parsed_document.file_type == "html" and depth < source_config.crawl_depth:
                    try:
                        response = self.session.get(url, timeout=self.config.timeout)
                        links = self._extract_links(
                            response.text,
                            url,
                            source_config.allowed_domains
                        )
                        
                        # Add new links to visit queue
                        for link in links:
                            if link not in visited and self._is_allowed_file_type(link):
                                to_visit.append((link, depth + 1))
                    except Exception as e:
                        logger.debug(f"Error extracting links from {url}: {e}")
        
        logger.info(f"Crawl completed: {len(results)} URLs crawled")
        return results
    
    def get_results(self) -> List[CrawlResult]:
        """Get all crawl results"""
        return self.crawl_results
    
    def get_successful_results(self) -> List[CrawlResult]:
        """Get only successful crawl results"""
        return [r for r in self.crawl_results if r.success]
    
    def reset(self):
        """Reset crawler state"""
        self.visited_urls.clear()
        self.crawl_results.clear()
        logger.info("Crawler state reset")

