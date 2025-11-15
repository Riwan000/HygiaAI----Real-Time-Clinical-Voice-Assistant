"""
Encryption Module for HIPAA Compliance

Provides:
- End-to-end encryption for sensitive patient data
- De-identification utilities
- Secure key management
- Audit trail support
"""

import os
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Encryption manager for HIPAA-compliant data storage
    
    Features:
    - End-to-end encryption using Fernet (symmetric encryption)
    - Key derivation from password
    - De-identification of patient data
    - Secure key management
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            encryption_key: Optional encryption key. If None, generates from environment or creates new key.
        """
        self.encryption_key = encryption_key or self._get_or_create_key()
        self.cipher = self._create_cipher(self.encryption_key)
        logger.info("Encryption manager initialized")
    
    def _get_or_create_key(self) -> str:
        """
        Get encryption key from environment or create new one
        
        Returns:
            Encryption key as string
        """
        # Try to get from environment
        key = os.getenv("ENCRYPTION_KEY")
        if key:
            return key
        
        # Generate new key
        key = Fernet.generate_key().decode()
        logger.warning(
            "No ENCRYPTION_KEY found in environment. Generated new key. "
            "Store this key securely: ENCRYPTION_KEY=" + key
        )
        return key
    
    def _create_cipher(self, key: str) -> Fernet:
        """
        Create Fernet cipher from key
        
        Args:
            key: Encryption key (Fernet key as base64 string or password)
            
        Returns:
            Fernet cipher instance
        """
        try:
            # Try to use key directly as Fernet key (base64 encoded, 44 chars)
            if len(key) == 44:
                return Fernet(key.encode())
        except Exception:
            pass
        
        # Derive key from password
        key_bytes = key.encode() if isinstance(key, str) else key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'hygiaai_salt',  # In production, use random salt
            iterations=100000,
            backend=default_backend()
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        return Fernet(derived_key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data
        
        Args:
            data: Data to encrypt (string)
            
        Returns:
            Encrypted data as base64 string
        """
        if not data:
            return ""
        
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data as string
        """
        if not encrypted_data:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: list[str]) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary to encrypt
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        encrypted = data.copy()
        for field in fields_to_encrypt:
            if field in encrypted and encrypted[field]:
                if isinstance(encrypted[field], str):
                    encrypted[field] = self.encrypt(encrypted[field])
                elif isinstance(encrypted[field], dict):
                    # Recursively encrypt nested dictionaries
                    encrypted[field] = self.encrypt_dict(encrypted[field], list(encrypted[field].keys()))
        
        return encrypted
    
    def decrypt_dict(self, data: Dict[str, Any], fields_to_decrypt: list[str]) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary to decrypt
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        decrypted = data.copy()
        for field in fields_to_decrypt:
            if field in decrypted and decrypted[field]:
                if isinstance(decrypted[field], str):
                    try:
                        decrypted[field] = self.decrypt(decrypted[field])
                    except Exception as e:
                        logger.warning(f"Failed to decrypt field {field}: {e}")
                elif isinstance(decrypted[field], dict):
                    # Recursively decrypt nested dictionaries
                    decrypted[field] = self.decrypt_dict(decrypted[field], list(decrypted[field].keys()))
        
        return decrypted


class DeIdentificationManager:
    """
    De-identification manager for HIPAA compliance
    
    Removes or masks PHI (Protected Health Information) from data
    """
    
    # Common PHI patterns
    PHI_PATTERNS = {
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'phone': r'\b\d{3}-\d{3}-\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'date': r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    }
    
    def __init__(self):
        """Initialize de-identification manager"""
        self.patterns = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in self.PHI_PATTERNS.items()}
        logger.info("De-identification manager initialized")
    
    def deidentify_text(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        De-identify text by removing PHI
        
        Args:
            text: Text to de-identify
            replacement: Replacement string for PHI
            
        Returns:
            De-identified text
        """
        if not text:
            return text
        
        deidentified = text
        for name, pattern in self.patterns.items():
            deidentified = pattern.sub(replacement, deidentified)
        
        return deidentified
    
    def hash_patient_id(self, patient_id: str) -> str:
        """
        Hash patient ID for anonymization
        
        Args:
            patient_id: Original patient ID
            
        Returns:
            Hashed patient ID
        """
        if not patient_id:
            return ""
        
        # Use SHA-256 for one-way hashing
        return hashlib.sha256(str(patient_id).encode()).hexdigest()[:16]  # Use first 16 chars
    
    def deidentify_dict(self, data: Dict[str, Any], phi_fields: list[str]) -> Dict[str, Any]:
        """
        De-identify specific fields in a dictionary
        
        Args:
            data: Dictionary to de-identify
            phi_fields: List of field names containing PHI
            
        Returns:
            De-identified dictionary
        """
        deidentified = data.copy()
        for field in phi_fields:
            if field in deidentified and deidentified[field]:
                if isinstance(deidentified[field], str):
                    deidentified[field] = self.deidentify_text(deidentified[field])
                elif field == "patient_id" or field.endswith("_id"):
                    deidentified[field] = self.hash_patient_id(str(deidentified[field]))
        
        return deidentified

