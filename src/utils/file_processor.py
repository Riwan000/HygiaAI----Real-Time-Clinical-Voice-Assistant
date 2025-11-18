"""
File Processing Utilities
Extracts text from various file formats for knowledge base ingestion
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available. PDF processing will be limited. Install with: pip install PyPDF2")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. DOCX processing will be limited. Install with: pip install python-docx")


class FileProcessor:
    """Process various file formats and extract text content"""
    
    @staticmethod
    def process_file(file_path: str, file_content: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Process a file and extract text content
        
        Args:
            file_path: Path to the file (or filename for content-based processing)
            file_content: Optional file content as bytes (if file is in memory)
            
        Returns:
            Dictionary with extracted content and metadata
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return FileProcessor._process_pdf(file_path, file_content)
        elif file_ext in ['.docx', '.doc']:
            return FileProcessor._process_docx(file_path, file_content)
        elif file_ext in ['.txt', '.md']:
            return FileProcessor._process_text(file_path, file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    @staticmethod
    def _process_pdf(file_path: str, file_content: Optional[bytes] = None) -> Dict[str, Any]:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 required for PDF processing. Install with: pip install PyPDF2")
        
        try:
            if file_content:
                import io
                pdf_file = io.BytesIO(file_content)
            else:
                pdf_file = open(file_path, 'rb')
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            num_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
            
            if not file_content:
                pdf_file.close()
            
            full_text = "\n\n".join(text_parts)
            
            # Try to extract metadata
            metadata = pdf_reader.metadata or {}
            title = metadata.get('/Title', Path(file_path).stem) if metadata else Path(file_path).stem
            
            return {
                "content": full_text,
                "title": title,
                "text": full_text,
                "file_type": "pdf",
                "num_pages": num_pages,
                "metadata": {
                    "author": metadata.get('/Author', ''),
                    "subject": metadata.get('/Subject', ''),
                    "creator": metadata.get('/Creator', ''),
                } if metadata else {}
            }
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            raise
    
    @staticmethod
    def _process_docx(file_path: str, file_content: Optional[bytes] = None) -> Dict[str, Any]:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx required for DOCX processing. Install with: pip install python-docx")
        
        try:
            if file_content:
                import io
                docx_file = io.BytesIO(file_content)
            else:
                docx_file = file_path
            
            doc = Document(docx_file)
            
            # Extract text from paragraphs
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            full_text = "\n\n".join(paragraphs)
            
            # Extract title (first paragraph or document properties)
            title = doc.core_properties.title or Path(file_path).stem
            if not title and paragraphs:
                title = paragraphs[0][:100]  # Use first paragraph as title
            
            return {
                "content": full_text,
                "title": title,
                "text": full_text,
                "file_type": "docx",
                "num_paragraphs": len(paragraphs),
                "metadata": {
                    "author": doc.core_properties.author or '',
                    "subject": doc.core_properties.subject or '',
                    "created": str(doc.core_properties.created) if doc.core_properties.created else '',
                }
            }
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
            raise
    
    @staticmethod
    def _process_text(file_path: str, file_content: Optional[bytes] = None) -> Dict[str, Any]:
        """Extract text from plain text file"""
        try:
            if file_content:
                # Try to decode as UTF-8, fallback to latin-1
                try:
                    text = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    text = file_content.decode('latin-1')
            else:
                # Try UTF-8 first, then latin-1
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        text = f.read()
            
            # Extract title (first line or filename)
            lines = text.split('\n')
            title = lines[0].strip()[:100] if lines and lines[0].strip() else Path(file_path).stem
            
            return {
                "content": text,
                "title": title,
                "text": text,
                "file_type": "text",
                "num_lines": len(lines),
                "metadata": {}
            }
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
            raise

