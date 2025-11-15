"""
Robots.txt Parser for Web Crawler

Respects robots.txt rules for polite crawling.
"""

import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import time

logger = logging.getLogger(__name__)


class RobotsParser:
    """
    Robots.txt parser for respecting crawl rules
    
    Features:
    - Parse robots.txt files
    - Check if URLs are allowed
    - Respect crawl delays
    - Cache parsed rules
    """
    
    def __init__(self, user_agent: str = "HygiaAI-Collector/1.0"):
        """
        Initialize robots parser
        
        Args:
            user_agent: User agent string for crawler
        """
        self.user_agent = user_agent
        self.parsers: Dict[str, RobotFileParser] = {}
        self.crawl_delays: Dict[str, float] = {}
        self.last_access_times: Dict[str, float] = {}
        
        logger.info(f"Robots parser initialized with user agent: {user_agent}")
    
    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    def _get_parser(self, url: str) -> Optional[RobotFileParser]:
        """Get or create RobotFileParser for a domain"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self.parsers:
            try:
                robots_url = self._get_robots_url(url)
                parser = RobotFileParser(robots_url)
                parser.read()
                self.parsers[domain] = parser
                
                # Extract crawl delay
                crawl_delay = parser.crawl_delay(self.user_agent)
                if crawl_delay:
                    self.crawl_delays[domain] = crawl_delay
                
                logger.info(f"Parsed robots.txt for {domain}")
            except Exception as e:
                logger.warning(f"Could not parse robots.txt for {domain}: {e}")
                # Create a permissive parser if robots.txt is unavailable
                parser = RobotFileParser()
                self.parsers[domain] = parser
        
        return self.parsers.get(domain)
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt
        
        Args:
            url: URL to check
            
        Returns:
            True if URL can be fetched
        """
        parser = self._get_parser(url)
        if not parser:
            # If no parser available, allow by default (but log warning)
            logger.warning(f"No robots.txt parser for {url}, allowing fetch")
            return True
        
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Allow by default if check fails
    
    def get_crawl_delay(self, url: str) -> float:
        """
        Get crawl delay for a domain (in seconds)
        
        Args:
            url: URL to get delay for
            
        Returns:
            Crawl delay in seconds (default: 1.0)
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        return self.crawl_delays.get(domain, 1.0)  # Default 1 second
    
    def wait_if_needed(self, url: str):
        """
        Wait if crawl delay is required
        
        Args:
            url: URL that was just accessed
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        delay = self.get_crawl_delay(url)
        last_access = self.last_access_times.get(domain, 0)
        elapsed = time.time() - last_access
        
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.debug(f"Waiting {wait_time:.2f}s for crawl delay on {domain}")
            time.sleep(wait_time)
        
        self.last_access_times[domain] = time.time()
    
    def is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed (alias for can_fetch)
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed
        """
        return self.can_fetch(url)

