"""
License and Access Validator for Knowledge Ingestion

Validates that only open-access content is ingested and enforces access policies.
"""

import logging
import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from enum import Enum

logger = logging.getLogger(__name__)


class AccessType(Enum):
    """Access type classification"""
    OPEN = "open"
    RESTRICTED = "restricted"
    PRIVATE = "private"
    UNKNOWN = "unknown"


class LicenseValidator:
    """
    Validates license and access type for knowledge base documents
    
    Features:
    - Detects open-access indicators
    - Validates license information
    - Enforces open-access-only policy
    - Checks Creative Commons licenses
    - Validates public domain indicators
    """
    
    # Open-access license patterns
    OPEN_ACCESS_PATTERNS = [
        r"creative\s+commons",
        r"cc\s*[-]?\s*(by|nc|nd|sa|zero)",
        r"public\s+domain",
        r"open\s+access",
        r"free\s+to\s+use",
        r"unrestricted",
        r"permission\s+granted",
        r"licensed\s+under.*open",
        r"mit\s+license",
        r"apache\s+license",
        r"bsd\s+license",
        r"gnu\s+(gpl|lgpl|fdl)",
    ]
    
    # Restricted access indicators
    RESTRICTED_PATTERNS = [
        r"copyright\s+protected",
        r"all\s+rights\s+reserved",
        r"proprietary",
        r"confidential",
        r"restricted\s+access",
        r"subscription\s+required",
        r"login\s+required",
        r"members\s+only",
    ]
    
    # Open-access source domains (known open-access medical sources)
    OPEN_ACCESS_DOMAINS = [
        "ncbi.nlm.nih.gov",
        "pubmed.ncbi.nlm.nih.gov",
        "pmc.ncbi.nlm.nih.gov",
        "who.int",
        "cdc.gov",
        "nice.org.uk",
        "medlineplus.gov",
        "open.umn.edu",
        "journals.plos.org",
        "biomedcentral.com",
        "medrxiv.org",
        "biorxiv.org",
    ]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize license validator
        
        Args:
            strict_mode: If True, only allow explicitly open-access content
        """
        self.strict_mode = strict_mode
        logger.info("License validator initialized (strict_mode={})".format(strict_mode))
    
    def validate_access(
        self,
        document: Dict[str, Any],
        url: Optional[str] = None,
        license_text: Optional[str] = None
    ) -> Tuple[bool, AccessType, Optional[str]]:
        """
        Validate document access type
        
        Args:
            document: Document dictionary with metadata
            url: Document URL (for domain checking)
            license_text: Optional license text to analyze
            
        Returns:
            Tuple of (is_valid, access_type, reason)
        """
        # Check URL domain
        if url:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check against known open-access domains
            for open_domain in self.OPEN_ACCESS_DOMAINS:
                if open_domain in domain:
                    return (True, AccessType.OPEN, f"Known open-access domain: {domain}")
        
        # Check document metadata for license information
        metadata_text = ""
        if "license" in document:
            metadata_text += str(document["license"]).lower() + " "
        if "access_type" in document:
            metadata_text += str(document["access_type"]).lower() + " "
        if "copyright" in document:
            metadata_text += str(document["copyright"]).lower() + " "
        if "rights" in document:
            metadata_text += str(document["rights"]).lower() + " "
        
        # Combine with provided license text
        full_text = (metadata_text + (license_text or "")).lower()
        
        # Check for open-access patterns
        for pattern in self.OPEN_ACCESS_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                return (True, AccessType.OPEN, f"Open-access license detected: {pattern}")
        
        # Check for restricted patterns
        for pattern in self.RESTRICTED_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                if self.strict_mode:
                    return (False, AccessType.RESTRICTED, f"Restricted access detected: {pattern}")
                else:
                    return (True, AccessType.RESTRICTED, f"Restricted access detected: {pattern}")
        
        # Default behavior based on strict mode
        if self.strict_mode:
            # In strict mode, require explicit open-access indication
            return (False, AccessType.UNKNOWN, "No open-access license detected (strict mode)")
        else:
            # In non-strict mode, allow unknown (assume open if from trusted sources)
            if url:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.lower()
                # Allow if from .gov, .edu, or .org domains (common for open-access)
                if any(domain.endswith(ext) for ext in [".gov", ".edu", ".org"]):
                    return (True, AccessType.OPEN, f"Trusted domain type: {domain}")
            
            return (True, AccessType.UNKNOWN, "No explicit license found (non-strict mode)")
    
    def validate_provenance_url(self, url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate provenance URL
        
        Args:
            url: Provenance URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return (False, "Provenance URL is required")
        
        if not isinstance(url, str):
            return (False, "Provenance URL must be a string")
        
        # Check URL format
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                return (False, "Provenance URL must include scheme (http:// or https://)")
            
            if parsed.scheme not in ["http", "https"]:
                return (False, f"Provenance URL must use http or https, got {parsed.scheme}")
            
            if not parsed.netloc:
                return (False, "Provenance URL must include domain")
            
            return (True, None)
        
        except Exception as e:
            return (False, f"Invalid URL format: {e}")
    
    def enforce_open_access_only(
        self,
        document: Dict[str, Any],
        url: Optional[str] = None,
        license_text: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforce open-access-only policy
        
        Args:
            document: Document dictionary
            url: Document URL
            license_text: Optional license text
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        is_valid, access_type, reason = self.validate_access(document, url, license_text)
        
        if not is_valid or access_type != AccessType.OPEN:
            error_msg = f"Only open-access content is allowed. {reason}"
            logger.warning(f"Access validation failed: {error_msg}")
            return (False, error_msg)
        
        logger.info(f"Access validation passed: {reason}")
        return (True, None)

