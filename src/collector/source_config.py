"""
Source Configuration for Medical Knowledge Collectors

Defines configuration for various open-access medical sources.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class MedicalSource(Enum):
    """Medical knowledge sources"""
    NCBI_BOOKSHELF = "ncbi_bookshelf"
    PUBMED_OA = "pubmed_oa"
    WHO_ELENA = "who_elena"
    CDC_PUBLICATIONS = "cdc_publications"
    NICE_CKS = "nice_cks"
    MEDLINEPLUS = "medlineplus"
    OPEN_TEXTBOOK_LIBRARY = "open_textbook_library"
    PLOS_MEDICINE = "plos_medicine"
    BIOMED_CENTRAL = "biomed_central"
    MEDRXIV = "medrxiv"


@dataclass
class SourceConfig:
    """Configuration for a medical knowledge source"""
    source: MedicalSource
    base_url: str
    allowed_domains: List[str]
    start_urls: List[str]
    allowed_file_types: List[str] = field(default_factory=lambda: [".pdf", ".html", ".xml", ".epub"])
    crawl_depth: int = 3
    max_pages: int = 1000
    respect_robots: bool = True
    crawl_delay: float = 1.0
    metadata_extractors: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source.value,
            "base_url": self.base_url,
            "allowed_domains": self.allowed_domains,
            "start_urls": self.start_urls,
            "allowed_file_types": self.allowed_file_types,
            "crawl_depth": self.crawl_depth,
            "max_pages": self.max_pages,
            "respect_robots": self.respect_robots,
            "crawl_delay": self.crawl_delay,
            "metadata_extractors": self.metadata_extractors
        }


# Predefined source configurations
SOURCE_CONFIGS: Dict[MedicalSource, SourceConfig] = {
    MedicalSource.NCBI_BOOKSHELF: SourceConfig(
        source=MedicalSource.NCBI_BOOKSHELF,
        base_url="https://www.ncbi.nlm.nih.gov/books",
        allowed_domains=["ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov"],
        start_urls=["https://www.ncbi.nlm.nih.gov/books"],
        allowed_file_types=[".html", ".xml", ".pdf"],
        crawl_depth=5,
        max_pages=5000
    ),
    MedicalSource.PUBMED_OA: SourceConfig(
        source=MedicalSource.PUBMED_OA,
        base_url="https://www.ncbi.nlm.nih.gov/pmc",
        allowed_domains=["ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov"],
        start_urls=["https://www.ncbi.nlm.nih.gov/pmc"],
        allowed_file_types=[".html", ".xml", ".pdf"],
        crawl_depth=4,
        max_pages=10000
    ),
    MedicalSource.WHO_ELENA: SourceConfig(
        source=MedicalSource.WHO_ELENA,
        base_url="https://www.who.int/elena",
        allowed_domains=["who.int", "www.who.int"],
        start_urls=["https://www.who.int/elena"],
        allowed_file_types=[".html", ".pdf"],
        crawl_depth=3,
        max_pages=1000
    ),
    MedicalSource.CDC_PUBLICATIONS: SourceConfig(
        source=MedicalSource.CDC_PUBLICATIONS,
        base_url="https://www.cdc.gov",
        allowed_domains=["cdc.gov", "www.cdc.gov"],
        start_urls=["https://www.cdc.gov/publications"],
        allowed_file_types=[".html", ".pdf"],
        crawl_depth=3,
        max_pages=2000
    ),
    MedicalSource.NICE_CKS: SourceConfig(
        source=MedicalSource.NICE_CKS,
        base_url="https://cks.nice.org.uk",
        allowed_domains=["nice.org.uk", "cks.nice.org.uk"],
        start_urls=["https://cks.nice.org.uk"],
        allowed_file_types=[".html", ".pdf"],
        crawl_depth=3,
        max_pages=500
    ),
    MedicalSource.MEDLINEPLUS: SourceConfig(
        source=MedicalSource.MEDLINEPLUS,
        base_url="https://medlineplus.gov",
        allowed_domains=["medlineplus.gov", "www.medlineplus.gov"],
        start_urls=["https://medlineplus.gov"],
        allowed_file_types=[".html"],
        crawl_depth=3,
        max_pages=2000
    ),
    MedicalSource.OPEN_TEXTBOOK_LIBRARY: SourceConfig(
        source=MedicalSource.OPEN_TEXTBOOK_LIBRARY,
        base_url="https://open.umn.edu/opentextbooks",
        allowed_domains=["open.umn.edu", "umn.edu"],
        start_urls=["https://open.umn.edu/opentextbooks"],
        allowed_file_types=[".html", ".pdf", ".epub"],
        crawl_depth=4,
        max_pages=1000
    ),
    MedicalSource.PLOS_MEDICINE: SourceConfig(
        source=MedicalSource.PLOS_MEDICINE,
        base_url="https://journals.plos.org/plosmedicine",
        allowed_domains=["journals.plos.org", "plos.org"],
        start_urls=["https://journals.plos.org/plosmedicine"],
        allowed_file_types=[".html", ".pdf", ".xml"],
        crawl_depth=4,
        max_pages=5000
    ),
    MedicalSource.BIOMED_CENTRAL: SourceConfig(
        source=MedicalSource.BIOMED_CENTRAL,
        base_url="https://www.biomedcentral.com",
        allowed_domains=["biomedcentral.com", "www.biomedcentral.com"],
        start_urls=["https://www.biomedcentral.com"],
        allowed_file_types=[".html", ".pdf", ".xml"],
        crawl_depth=4,
        max_pages=10000
    ),
    MedicalSource.MEDRXIV: SourceConfig(
        source=MedicalSource.MEDRXIV,
        base_url="https://www.medrxiv.org",
        allowed_domains=["medrxiv.org", "www.medrxiv.org"],
        start_urls=["https://www.medrxiv.org"],
        allowed_file_types=[".html", ".pdf"],
        crawl_depth=3,
        max_pages=5000
    )
}

