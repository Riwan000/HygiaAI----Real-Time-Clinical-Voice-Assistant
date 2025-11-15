"""
Unit tests for license validator
"""

import pytest
from src.compliance.license_validator import LicenseValidator, AccessType


class TestLicenseValidator:
    """Test LicenseValidator"""
    
    @pytest.fixture
    def validator_strict(self):
        """Create strict validator"""
        return LicenseValidator(strict_mode=True)
    
    @pytest.fixture
    def validator_loose(self):
        """Create non-strict validator"""
        return LicenseValidator(strict_mode=False)
    
    def test_validate_provenance_url_valid(self, validator_strict):
        """Test valid provenance URL"""
        is_valid, error = validator_strict.validate_provenance_url("https://example.com/doc.html")
        assert is_valid is True
        assert error is None
    
    def test_validate_provenance_url_missing(self, validator_strict):
        """Test missing provenance URL"""
        is_valid, error = validator_strict.validate_provenance_url(None)
        assert is_valid is False
        assert "required" in error.lower()
    
    def test_validate_provenance_url_invalid_scheme(self, validator_strict):
        """Test invalid URL scheme"""
        is_valid, error = validator_strict.validate_provenance_url("ftp://example.com/doc.html")
        assert is_valid is False
        assert "http" in error.lower()
    
    def test_validate_provenance_url_no_scheme(self, validator_strict):
        """Test URL without scheme"""
        is_valid, error = validator_strict.validate_provenance_url("example.com/doc.html")
        assert is_valid is False
        assert "scheme" in error.lower()
    
    def test_validate_access_open_domain(self, validator_strict):
        """Test open-access domain detection"""
        doc = {}
        is_valid, access_type, reason = validator_strict.validate_access(
            doc, url="https://ncbi.nlm.nih.gov/book/123"
        )
        assert is_valid is True
        assert access_type == AccessType.OPEN
        assert "domain" in reason.lower()
    
    def test_validate_access_creative_commons(self, validator_strict):
        """Test Creative Commons license detection"""
        doc = {"license": "This work is licensed under Creative Commons Attribution 4.0"}
        is_valid, access_type, reason = validator_strict.validate_access(doc)
        assert is_valid is True
        assert access_type == AccessType.OPEN
        assert "creative" in reason.lower() or "cc" in reason.lower()
    
    def test_validate_access_public_domain(self, validator_strict):
        """Test public domain detection"""
        doc = {"license": "This work is in the public domain"}
        is_valid, access_type, reason = validator_strict.validate_access(doc)
        assert is_valid is True
        assert access_type == AccessType.OPEN
    
    def test_validate_access_restricted(self, validator_strict):
        """Test restricted access detection"""
        doc = {"copyright": "All rights reserved. Copyright protected."}
        is_valid, access_type, reason = validator_strict.validate_access(doc)
        assert is_valid is False
        assert access_type == AccessType.RESTRICTED
    
    def test_validate_access_unknown_strict(self, validator_strict):
        """Test unknown access in strict mode"""
        doc = {}
        is_valid, access_type, reason = validator_strict.validate_access(doc)
        assert is_valid is False
        assert access_type == AccessType.UNKNOWN
        assert "strict" in reason.lower()
    
    def test_validate_access_unknown_loose(self, validator_loose):
        """Test unknown access in non-strict mode"""
        doc = {}
        is_valid, access_type, reason = validator_loose.validate_access(doc, url="https://example.gov/doc.html")
        assert is_valid is True
        assert access_type in [AccessType.OPEN, AccessType.UNKNOWN]
    
    def test_enforce_open_access_allowed(self, validator_strict):
        """Test enforcement allows open-access content"""
        doc = {"license": "Creative Commons"}
        is_allowed, error = validator_strict.enforce_open_access_only(doc)
        assert is_allowed is True
        assert error is None
    
    def test_enforce_open_access_denied(self, validator_strict):
        """Test enforcement denies restricted content"""
        doc = {"copyright": "All rights reserved"}
        is_allowed, error = validator_strict.enforce_open_access_only(doc)
        assert is_allowed is False
        assert "open-access" in error.lower() or "allowed" in error.lower()
    
    def test_enforce_open_access_unknown_strict(self, validator_strict):
        """Test enforcement denies unknown in strict mode"""
        doc = {}
        is_allowed, error = validator_strict.enforce_open_access_only(doc)
        assert is_allowed is False
        assert error is not None

