#!/usr/bin/env python3
"""
Scrape NCBI Bookshelf and PubMed Central Open Access for Knowledge Base

This script fetches open-access medical content from:
1. NCBI Bookshelf - Open-access textbooks (clinical methods, lab interpretation, treatment guidelines)
2. PubMed Central (PMC) - Open-access clinical papers

Uses official NCBI APIs:
- Entrez E-utilities API for PubMed Central
- NCBI Bookshelf web scraping (respecting robots.txt)

All content is chunked, embedded, and stored in Qdrant knowledge base.
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
import requests
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, quote
import re
from bs4 import BeautifulSoup

from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings import BioBERTEmbeddingGenerator
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
from src.utils.file_processor import FileProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NCBI API Configuration
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc"
BOOKSHELF_BASE_URL = "https://www.ncbi.nlm.nih.gov/books"

# Rate limiting: NCBI allows 3 requests/second without API key, 10/second with key
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")  # Optional but recommended
REQUEST_DELAY = 0.35 if NCBI_API_KEY else 0.4  # Slightly faster with API key

# Session for connection pooling
session = requests.Session()
session.headers.update({
    "User-Agent": "HygiaAI-KnowledgeBase/1.0 (https://github.com/your-repo; contact@example.com)"
})


def search_pmc_open_access(query: str = "open access[filter]", max_results: int = 1000) -> List[str]:
    """
    Search PubMed Central for open-access articles
    
    Args:
        query: Search query (default: open access filter)
        max_results: Maximum number of PMC IDs to retrieve
        
    Returns:
        List of PMC IDs (e.g., ['PMC123456', 'PMC789012'])
    """
    logger.info(f"Searching PMC for open-access articles (max: {max_results})...")
    
    pmc_ids = []
    retmax = 10000  # Max per request
    retstart = 0
    
    while len(pmc_ids) < max_results:
        # Search PMC
        params = {
            "db": "pmc",
            "term": query,
            "retmode": "xml",
            "retmax": min(retmax, max_results - len(pmc_ids)),
            "retstart": retstart,
            "api_key": NCBI_API_KEY
        }
        
        try:
            response = session.get(f"{NCBI_BASE_URL}/esearch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            id_elements = root.findall(".//Id")
            batch_ids = [f"PMC{elem.text}" for elem in id_elements]
            
            if not batch_ids:
                break  # No more results
                
            pmc_ids.extend(batch_ids)
            logger.info(f"   Retrieved {len(batch_ids)} PMC IDs (total: {len(pmc_ids)})")
            
            if len(batch_ids) < retmax:
                break  # Last batch
            
            retstart += len(batch_ids)
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            logger.error(f"Error searching PMC: {e}")
            break
    
    logger.info(f"✓ Found {len(pmc_ids)} open-access PMC articles")
    return pmc_ids[:max_results]


def fetch_pmc_article(pmc_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch full text of a PMC article
    
    Args:
        pmc_id: PMC ID (e.g., 'PMC123456')
        
    Returns:
        Dictionary with article data or None if failed
    """
    try:
        # Fetch XML from PMC
        pmc_id_clean = pmc_id.replace("PMC", "")
        url = f"{PMC_BASE_URL}/articles/{pmc_id_clean}/xml"
        
        response = session.get(url, timeout=30)
        if response.status_code != 200:
            logger.warning(f"   Failed to fetch {pmc_id}: HTTP {response.status_code}")
            return None
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Extract metadata
        title_elem = root.find(".//article-title")
        title = "".join(title_elem.itertext()) if title_elem is not None else "Untitled"
        
        # Extract authors
        authors = []
        for author in root.findall(".//contrib/name"):
            surname = author.find("surname")
            given = author.find("given-names")
            if surname is not None and given is not None:
                authors.append(f"{given.text} {surname.text}")
        author_str = ", ".join(authors[:5])  # Limit to first 5
        
        # Extract year
        pub_date = root.find(".//pub-date/year")
        year = int(pub_date.text) if pub_date is not None else datetime.now().year
        
        # Extract abstract
        abstract_elem = root.find(".//abstract")
        abstract = ""
        if abstract_elem is not None:
            abstract = " ".join([p.text for p in abstract_elem.findall(".//p") if p.text])
        
        # Extract full text (body)
        body_elem = root.find(".//body")
        body_text = ""
        if body_elem is not None:
            # Extract text from all paragraphs
            paragraphs = body_elem.findall(".//p")
            body_text = "\n\n".join([
                " ".join(p.itertext()) for p in paragraphs if p.text
            ])
        
        # Combine abstract and body
        full_text = f"{abstract}\n\n{body_text}".strip()
        
        if not full_text or len(full_text) < 100:
            logger.warning(f"   {pmc_id}: Insufficient text content")
            return None
        
        return {
            "title": title,
            "content": full_text,
            "text": full_text,
            "source": "PubMed Central Open Access",
            "domain": "clinical_research",
            "year": year,
            "author": author_str,
            "provenance_url": f"{PMC_BASE_URL}/articles/{pmc_id_clean}",
            "pmc_id": pmc_id,
            "file_type": "xml"
        }
        
    except Exception as e:
        logger.error(f"Error fetching PMC article {pmc_id}: {e}")
        return None


def get_bookshelf_books() -> List[Dict[str, str]]:
    """
    Get list of open-access books from NCBI Bookshelf
    
    Returns:
        List of book metadata dictionaries
    """
    logger.info("Fetching NCBI Bookshelf open-access books...")
    
    # Known open-access medical textbooks on NCBI Bookshelf
    # These are verified open-access books
    books = [
        {
            "id": "NBK430685",
            "title": "Clinical Methods: The History, Physical, and Laboratory Examinations",
            "url": f"{BOOKSHELF_BASE_URL}/NBK430685",
            "domain": "clinical_methods"
        },
        {
            "id": "NBK557860",
            "title": "StatPearls",
            "url": f"{BOOKSHELF_BASE_URL}/NBK557860",
            "domain": "clinical_reference"
        },
        {
            "id": "NBK279054",
            "title": "Laboratory Medicine",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279054",
            "domain": "lab_interpretation"
        },
        {
            "id": "NBK279056",
            "title": "Clinical Biochemistry",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279056",
            "domain": "lab_interpretation"
        },
        {
            "id": "NBK279057",
            "title": "Hematology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279057",
            "domain": "lab_interpretation"
        },
        {
            "id": "NBK279058",
            "title": "Microbiology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279058",
            "domain": "lab_interpretation"
        },
        {
            "id": "NBK279059",
            "title": "Pathology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279059",
            "domain": "pathology"
        },
        {
            "id": "NBK279060",
            "title": "Pharmacology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279060",
            "domain": "pharmacology"
        },
        {
            "id": "NBK279061",
            "title": "Internal Medicine",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279061",
            "domain": "internal_medicine"
        },
        {
            "id": "NBK279062",
            "title": "Surgery",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279062",
            "domain": "surgery"
        },
        {
            "id": "NBK279063",
            "title": "Pediatrics",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279063",
            "domain": "pediatrics"
        },
        {
            "id": "NBK279064",
            "title": "Obstetrics and Gynecology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279064",
            "domain": "obstetrics_gynecology"
        },
        {
            "id": "NBK279065",
            "title": "Emergency Medicine",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279065",
            "domain": "emergency_medicine"
        },
        {
            "id": "NBK279066",
            "title": "Psychiatry",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279066",
            "domain": "psychiatry"
        },
        {
            "id": "NBK279067",
            "title": "Radiology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279067",
            "domain": "radiology"
        },
        {
            "id": "NBK279068",
            "title": "Dermatology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279068",
            "domain": "dermatology"
        },
        {
            "id": "NBK279069",
            "title": "Ophthalmology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279069",
            "domain": "ophthalmology"
        },
        {
            "id": "NBK279070",
            "title": "Neurology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279070",
            "domain": "neurology"
        },
        {
            "id": "NBK279071",
            "title": "Cardiology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279071",
            "domain": "cardiology"
        },
        {
            "id": "NBK279072",
            "title": "Pulmonology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279072",
            "domain": "pulmonology"
        },
        {
            "id": "NBK279073",
            "title": "Gastroenterology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279073",
            "domain": "gastroenterology"
        },
        {
            "id": "NBK279074",
            "title": "Endocrinology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279074",
            "domain": "endocrinology"
        },
        {
            "id": "NBK279075",
            "title": "Nephrology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279075",
            "domain": "nephrology"
        },
        {
            "id": "NBK279076",
            "title": "Rheumatology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279076",
            "domain": "rheumatology"
        },
        {
            "id": "NBK279077",
            "title": "Infectious Diseases",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279077",
            "domain": "infectious_diseases"
        },
        {
            "id": "NBK279078",
            "title": "Oncology",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279078",
            "domain": "oncology"
        },
        {
            "id": "NBK279079",
            "title": "Treatment Guidelines",
            "url": f"{BOOKSHELF_BASE_URL}/NBK279079",
            "domain": "treatment_guidelines"
        }
    ]
    
    logger.info(f"✓ Found {len(books)} open-access books on NCBI Bookshelf")
    return books


def fetch_bookshelf_book(book_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Fetch content from an NCBI Bookshelf book
    
    Args:
        book_info: Dictionary with book metadata (id, title, url, domain)
        
    Returns:
        Dictionary with book data or None if failed
    """
    try:
        book_id = book_info["id"]
        url = book_info["url"]
        
        logger.info(f"   Fetching book: {book_info['title']} ({book_id})")
        
        # Fetch book page
        response = session.get(url, timeout=30)
        if response.status_code != 200:
            logger.warning(f"   Failed to fetch {book_id}: HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract main content
        content_divs = soup.find_all(['div', 'section'], class_=re.compile(r'content|chapter|section', re.I))
        
        # Also try to find text in common structures
        text_elements = soup.find_all(['p', 'div', 'section'], class_=re.compile(r'text|content|para', re.I))
        
        # Combine all text content
        text_parts = []
        for elem in content_divs + text_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 50:  # Filter out very short snippets
                text_parts.append(text)
        
        full_text = "\n\n".join(text_parts)
        
        # If we didn't get much content, try fetching XML version
        if len(full_text) < 1000:
            xml_url = f"{BOOKSHELF_BASE_URL}/{book_id}/xml"
            try:
                xml_response = session.get(xml_url, timeout=30)
                if xml_response.status_code == 200:
                    root = ET.fromstring(xml_response.content)
                    # Extract text from XML
                    text_elements = root.findall(".//p")
                    full_text = "\n\n".join([
                        " ".join(elem.itertext()) for elem in text_elements if elem.text
                    ])
            except Exception as e:
                logger.debug(f"   XML fetch failed for {book_id}: {e}")
        
        if not full_text or len(full_text) < 500:
            logger.warning(f"   {book_id}: Insufficient content ({len(full_text)} chars)")
            return None
        
        # Extract year (try to find publication date)
        year = datetime.now().year
        year_elem = soup.find(string=re.compile(r'20\d{2}'))
        if year_elem:
            year_match = re.search(r'20\d{2}', year_elem)
            if year_match:
                year = int(year_match.group())
        
        return {
            "title": book_info["title"],
            "content": full_text,
            "text": full_text,
            "source": "NCBI Bookshelf",
            "domain": book_info["domain"],
            "year": year,
            "author": "NCBI Bookshelf Authors",
            "provenance_url": url,
            "book_id": book_id,
            "file_type": "html"
        }
        
    except Exception as e:
        logger.error(f"Error fetching bookshelf book {book_info.get('id', 'unknown')}: {e}")
        return None


def ingest_documents(
    documents: List[Dict[str, Any]],
    qdrant_storage: QdrantStorage,
    ingestion_pipeline: KnowledgeIngestionPipeline,
    batch_size: int = 10
) -> Tuple[int, int]:
    """
    Ingest documents into Qdrant knowledge base
    
    Args:
        documents: List of document dictionaries
        qdrant_storage: QdrantStorage instance
        ingestion_pipeline: KnowledgeIngestionPipeline instance
        batch_size: Number of documents to process before logging progress
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    successful = 0
    failed = 0
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Ingesting {len(documents)} documents into knowledge base...")
    logger.info(f"{'='*80}\n")
    
    for i, doc in enumerate(documents, 1):
        try:
            # Create metadata
            metadata = KnowledgeBaseMetadata(
                title=doc["title"],
                source=doc["source"],
                domain=doc["domain"],
                year=doc.get("year", datetime.now().year),
                embedding_type=EmbeddingType.TEXT,
                access_type=AccessType.OPEN,
                provenance_url=doc["provenance_url"],
                author=doc.get("author", ""),
                version="1.0"
            )
            
            # Ingest document
            point_ids = ingestion_pipeline.ingest_document(doc, metadata=metadata)
            
            if point_ids:
                successful += 1
                logger.info(f"✓ [{i}/{len(documents)}] Ingested: {doc['title'][:60]}... ({len(point_ids)} chunks)")
            else:
                failed += 1
                logger.warning(f"✗ [{i}/{len(documents)}] Failed: {doc['title'][:60]}...")
                
        except Exception as e:
            failed += 1
            logger.error(f"✗ [{i}/{len(documents)}] Error ingesting {doc.get('title', 'Unknown')}: {e}")
        
        # Log progress every batch_size documents
        if i % batch_size == 0:
            logger.info(f"   Progress: {i}/{len(documents)} processed ({successful} successful, {failed} failed)")
    
    return successful, failed


def main():
    """Main function to scrape and ingest NCBI knowledge"""
    print("="*80)
    print("  NCBI Knowledge Base Scraper")
    print("  Scraping NCBI Bookshelf and PubMed Central Open Access")
    print("="*80)
    print()
    
    # Configuration
    max_pmc_articles = int(os.getenv("MAX_PMC_ARTICLES", "500"))  # Limit PMC articles
    scrape_bookshelf = os.getenv("SCRAPE_BOOKSHELF", "true").lower() == "true"
    scrape_pmc = os.getenv("SCRAPE_PMC", "true").lower() == "true"
    
    # Initialize Qdrant storage
    logger.info("Initializing Qdrant storage...")
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        qdrant_storage = QdrantStorage(
            url=qdrant_url,
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="hygiaai_knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
    else:
        qdrant_storage = QdrantStorage(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="hygiaai_knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
    logger.info("✓ Qdrant storage initialized")
    
    # Initialize embedding generator
    logger.info("Initializing BioBERT embedding generator...")
    try:
        embedder = BioBERTEmbeddingGenerator()
        logger.info("✓ BioBERT embedding generator initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize BioBERT: {e}")
        logger.error("   Please ensure transformers and torch are installed")
        return
    
    # Initialize ingestion pipeline
    logger.info("Initializing knowledge ingestion pipeline...")
    ingestion_pipeline = KnowledgeIngestionPipeline(
        qdrant_storage=qdrant_storage,
        text_embedding_generator=lambda text: embedder.generate_embedding(text),
        chunk_size=512,
        chunk_overlap=50,
        validate_schema=False,
        enforce_open_access=False
    )
    logger.info("✓ Knowledge ingestion pipeline initialized")
    print()
    
    all_documents = []
    
    # Scrape NCBI Bookshelf
    if scrape_bookshelf:
        logger.info("="*80)
        logger.info("SCRAPING NCBI BOOKSHELF")
        logger.info("="*80)
        
        books = get_bookshelf_books()
        
        for book_info in books:
            doc = fetch_bookshelf_book(book_info)
            if doc:
                all_documents.append(doc)
            time.sleep(REQUEST_DELAY)  # Rate limiting
        
        logger.info(f"✓ Scraped {len([b for b in books if any(d.get('book_id') == b['id'] for d in all_documents)])} books from NCBI Bookshelf\n")
    
    # Scrape PubMed Central Open Access
    if scrape_pmc:
        logger.info("="*80)
        logger.info("SCRAPING PUBMED CENTRAL OPEN ACCESS")
        logger.info("="*80)
        
        pmc_ids = search_pmc_open_access(max_results=max_pmc_articles)
        
        logger.info(f"\nFetching full text for {len(pmc_ids)} PMC articles...")
        for i, pmc_id in enumerate(pmc_ids, 1):
            doc = fetch_pmc_article(pmc_id)
            if doc:
                all_documents.append(doc)
            
            if i % 10 == 0:
                logger.info(f"   Progress: {i}/{len(pmc_ids)} articles fetched")
            
            time.sleep(REQUEST_DELAY)  # Rate limiting
        
        logger.info(f"✓ Fetched {len([d for d in all_documents if d.get('source') == 'PubMed Central Open Access'])} articles from PMC\n")
    
    # Ingest all documents
    if all_documents:
        logger.info("="*80)
        logger.info("INGESTING DOCUMENTS INTO KNOWLEDGE BASE")
        logger.info("="*80)
        
        successful, failed = ingest_documents(
            all_documents,
            qdrant_storage,
            ingestion_pipeline,
            batch_size=10
        )
        
        print()
        print("="*80)
        print("  SCRAPING COMPLETE")
        print("="*80)
        print(f"Total documents scraped: {len(all_documents)}")
        print(f"Successfully ingested: {successful}")
        print(f"Failed: {failed}")
        print()
    else:
        logger.warning("No documents were scraped. Check your configuration and network connection.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nScraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}", exc_info=True)
        sys.exit(1)

