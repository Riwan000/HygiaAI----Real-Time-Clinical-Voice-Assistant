"""
Document Parser for Medical Sources

Parses various document formats (HTML, PDF, XML, EPUB) and extracts metadata.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse
from pathlib import Path

logger = logging.getLogger(__name__)

# Optional libraries
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup4 not available. Install with: pip install beautifulsoup4")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available. Install with: pip install PyPDF2")

try:
    import xml.etree.ElementTree as ET
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False


@dataclass
class ParsedDocument:
    """Parsed document with metadata"""
    url: str
    title: str
    content: str
    source: str
    domain: str
    author: Optional[str] = None
    year: Optional[int] = None
    file_type: str = "html"
    metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "domain": self.domain,
            "author": self.author,
            "year": self.year,
            "file_type": self.file_type,
            "metadata": self.metadata,
            "parsed_at": self.parsed_at.isoformat()
        }


class DocumentParser:
    """
    Document parser for various formats
    
    Features:
    - Parse HTML documents
    - Extract PDF text (if PyPDF2 available)
    - Parse XML documents
    - Extract metadata (title, author, year)
    """
    
    def __init__(self):
        """Initialize document parser"""
        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup4 not available. HTML parsing will be limited.")
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 not available. PDF parsing will not work.")
        
        logger.info("Document parser initialized")
    
    def parse_html(self, html_content: str, url: str) -> ParsedDocument:
        """
        Parse HTML document
        
        Args:
            html_content: HTML content string
            url: Source URL
            
        Returns:
            ParsedDocument object
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if BS4_AVAILABLE:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.get_text().strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()
            elif soup.find('meta', property='og:title'):
                title = soup.find('meta', property='og:title').get('content', '').strip()
            
            # Extract author
            author = None
            author_meta = soup.find('meta', attrs={'name': re.compile(r'author', re.I)})
            if author_meta:
                author = author_meta.get('content', '').strip()
            
            # Extract year from various meta tags or content
            year = self._extract_year(html_content, soup)
            
            # Extract main content (remove scripts, styles, etc.)
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            content = soup.get_text(separator=' ', strip=True)
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
            
        else:
            # Fallback: basic regex extraction
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', ' ', html_content)
            content = re.sub(r'\s+', ' ', content).strip()
            
            author = None
            year = self._extract_year(html_content, None)
        
        return ParsedDocument(
            url=url,
            title=title or url,
            content=content,
            source=domain,
            domain=domain,
            author=author,
            year=year,
            file_type="html"
        )
    
    def parse_pdf(self, pdf_content: bytes, url: str) -> ParsedDocument:
        """
        Parse PDF document
        
        Args:
            pdf_content: PDF file content as bytes
            url: Source URL
            
        Returns:
            ParsedDocument object
        """
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not available. Install with: pip install PyPDF2")
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        try:
            from io import BytesIO
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            content_parts = []
            for page in pdf_reader.pages:
                content_parts.append(page.extract_text())
            
            content = '\n\n'.join(content_parts)
            
            # Extract metadata
            metadata = pdf_reader.metadata or {}
            title = metadata.get('/Title', '') or url
            author = metadata.get('/Author', '')
            year = None
            
            # Try to extract year from creation/modification date
            if '/CreationDate' in metadata:
                year = self._extract_year_from_date(metadata['/CreationDate'])
            elif '/ModDate' in metadata:
                year = self._extract_year_from_date(metadata['/ModDate'])
            
            # If no year in metadata, try to extract from content
            if not year:
                year = self._extract_year(content, None)
            
        except Exception as e:
            logger.error(f"Error parsing PDF {url}: {e}")
            raise
        
        return ParsedDocument(
            url=url,
            title=title,
            content=content,
            source=domain,
            domain=domain,
            author=author,
            year=year,
            file_type="pdf",
            metadata={"pdf_pages": len(pdf_reader.pages) if 'pdf_reader' in locals() else 0}
        )
    
    def parse_xml(self, xml_content: str, url: str) -> ParsedDocument:
        """
        Parse XML document
        
        Args:
            xml_content: XML content string
            url: Source URL
            
        Returns:
            ParsedDocument object
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        try:
            root = ET.fromstring(xml_content)
            
            # Try to find title
            title = ""
            for elem in root.iter():
                if elem.tag.lower() in ['title', 'dc:title', 'dcterms:title']:
                    title = elem.text or ""
                    break
            
            # Extract text content
            content = ET.tostring(root, encoding='unicode', method='text')
            
            # Extract author
            author = None
            for elem in root.iter():
                if elem.tag.lower() in ['author', 'creator', 'dc:creator', 'dcterms:creator']:
                    author = elem.text or ""
                    break
            
            # Extract year
            year = self._extract_year(xml_content, None)
            
        except Exception as e:
            logger.error(f"Error parsing XML {url}: {e}")
            # Fallback: treat as text
            content = xml_content
            title = url
            author = None
            year = None
        
        return ParsedDocument(
            url=url,
            title=title or url,
            content=content,
            source=domain,
            domain=domain,
            author=author,
            year=year,
            file_type="xml"
        )
    
    def _extract_year(self, text: str, soup: Optional[Any] = None) -> Optional[int]:
        """
        Extract year from text or HTML
        
        Args:
            text: Text content
            soup: Optional BeautifulSoup object
            
        Returns:
            Year as integer or None
        """
        # Try meta tags first (if soup available)
        if soup:
            year_meta = soup.find('meta', attrs={'name': re.compile(r'date|year', re.I)})
            if year_meta:
                year_str = year_meta.get('content', '')
                year_match = re.search(r'\b(19|20)\d{2}\b', year_str)
                if year_match:
                    return int(year_match.group())
        
        # Search for 4-digit years (1900-2099)
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, text)
        
        if years:
            # Get the most recent year found
            year_str = ''.join(years[-1]) if isinstance(years[-1], tuple) else years[-1]
            try:
                year = int(year_str)
                # Validate year is reasonable
                if 1900 <= year <= 2100:
                    return year
            except ValueError:
                pass
        
        return None
    
    def _extract_year_from_date(self, date_str: str) -> Optional[int]:
        """Extract year from PDF date string (e.g., 'D:20230101120000Z')"""
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            try:
                year = int(year_match.group(1))
                if 1900 <= year <= 2100:
                    return year
            except ValueError:
                pass
        return None
    
    def parse_document(self, content: bytes, url: str, content_type: Optional[str] = None) -> ParsedDocument:
        """
        Parse document based on content type or file extension
        
        Args:
            content: Document content (bytes)
            url: Source URL
            content_type: Optional content type (e.g., 'text/html', 'application/pdf')
            
        Returns:
            ParsedDocument object
        """
        # Determine file type
        if content_type:
            if 'html' in content_type.lower():
                file_type = 'html'
            elif 'pdf' in content_type.lower():
                file_type = 'pdf'
            elif 'xml' in content_type.lower():
                file_type = 'xml'
            else:
                file_type = 'html'  # Default
        else:
            # Infer from URL
            parsed = urlparse(url)
            path = parsed.path.lower()
            if path.endswith('.pdf'):
                file_type = 'pdf'
            elif path.endswith('.xml'):
                file_type = 'xml'
            elif path.endswith('.epub'):
                file_type = 'epub'  # Not yet implemented
            else:
                file_type = 'html'
        
        # Parse based on type
        if file_type == 'pdf':
            return self.parse_pdf(content, url)
        elif file_type == 'xml':
            return self.parse_xml(content.decode('utf-8', errors='ignore'), url)
        elif file_type == 'html':
            return self.parse_html(content.decode('utf-8', errors='ignore'), url)
        else:
            # Default: try HTML parsing
            logger.warning(f"Unknown file type {file_type}, attempting HTML parse")
            return self.parse_html(content.decode('utf-8', errors='ignore'), url)

