"""
Schema Validator for Knowledge Base Documents

Validates document payloads and metadata against the defined schema standards.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .schema import (
    KnowledgeBaseMetadata,
    KnowledgeBaseSchema,
    EmbeddingType,
    AccessType
)

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Exception raised for schema validation errors"""
    pass


class SchemaValidator:
    """
    Validator for knowledge base document schemas
    
    Features:
    - Validates required fields
    - Validates field types and formats
    - Validates embedding dimensions
    - Validates chunking metadata
    """
    
    REQUIRED_METADATA_FIELDS = [
        "title",
        "source"
    ]
    
    OPTIONAL_METADATA_FIELDS = [
        "domain",
        "year",
        "embedding_type",
        "access_type",
        "provenance_url",
        "version",
        "author",
        "chunk_index",
        "chunk_total",
        "created_at",
        "updated_at"
    ]
    
    REQUIRED_DOCUMENT_FIELDS = [
        "text"  # At least text or content should be present
    ]
    
    VALID_DOMAINS = [
        "pathology",
        "pharmacology",
        "guidelines",
        "anatomy",
        "surgery",
        "pediatrics",
        "cardiology",
        "oncology",
        "general"
    ]
    
    VALID_EMBEDDING_TYPES = [e.value for e in EmbeddingType]
    VALID_ACCESS_TYPES = [a.value for a in AccessType]
    
    # Embedding dimensions
    TEXT_EMBEDDING_DIM = 768  # S-PubMedBert-MS-MARCO
    IMAGE_EMBEDDING_DIM = 512  # CLIP
    
    # Chunking standards
    DEFAULT_CHUNK_SIZE = 512
    DEFAULT_CHUNK_OVERLAP = 50
    MIN_CHUNK_SIZE = 100
    MAX_CHUNK_SIZE = 2048
    
    def __init__(self):
        """Initialize schema validator"""
        logger.info("Schema validator initialized")
    
    def validate_metadata(
        self,
        metadata: Dict[str, Any],
        strict: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate metadata dictionary
        
        Args:
            metadata: Metadata dictionary to validate
            strict: If True, all optional fields must be present
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_METADATA_FIELDS:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")
            elif not metadata[field]:
                errors.append(f"Required field '{field}' is empty")
        
        # Validate field types and values
        if "title" in metadata:
            if not isinstance(metadata["title"], str):
                errors.append("Field 'title' must be a string")
            elif len(metadata["title"]) == 0:
                errors.append("Field 'title' cannot be empty")
        
        if "source" in metadata:
            if not isinstance(metadata["source"], str):
                errors.append("Field 'source' must be a string")
            elif len(metadata["source"]) == 0:
                errors.append("Field 'source' cannot be empty")
        
        if "domain" in metadata and metadata["domain"]:
            if metadata["domain"] not in self.VALID_DOMAINS:
                errors.append(f"Invalid domain: {metadata['domain']}. Must be one of: {self.VALID_DOMAINS}")
        
        if "year" in metadata and metadata["year"] is not None:
            if not isinstance(metadata["year"], int):
                errors.append("Field 'year' must be an integer")
            elif metadata["year"] < 1900 or metadata["year"] > 2100:
                errors.append(f"Field 'year' must be between 1900 and 2100, got {metadata['year']}")
        
        if "embedding_type" in metadata and metadata["embedding_type"]:
            if metadata["embedding_type"] not in self.VALID_EMBEDDING_TYPES:
                errors.append(f"Invalid embedding_type: {metadata['embedding_type']}. Must be one of: {self.VALID_EMBEDDING_TYPES}")
        
        if "access_type" in metadata and metadata["access_type"]:
            if metadata["access_type"] not in self.VALID_ACCESS_TYPES:
                errors.append(f"Invalid access_type: {metadata['access_type']}. Must be one of: {self.VALID_ACCESS_TYPES}")
        
        if "provenance_url" in metadata and metadata["provenance_url"]:
            if not isinstance(metadata["provenance_url"], str):
                errors.append("Field 'provenance_url' must be a string")
            elif not metadata["provenance_url"].startswith(("http://", "https://")):
                errors.append("Field 'provenance_url' must be a valid URL")
        
        if "chunk_index" in metadata and metadata["chunk_index"] is not None:
            if not isinstance(metadata["chunk_index"], int):
                errors.append("Field 'chunk_index' must be an integer")
            elif metadata["chunk_index"] < 0:
                errors.append("Field 'chunk_index' must be non-negative")
        
        if "chunk_total" in metadata and metadata["chunk_total"] is not None:
            if not isinstance(metadata["chunk_total"], int):
                errors.append("Field 'chunk_total' must be an integer")
            elif metadata["chunk_total"] < 1:
                errors.append("Field 'chunk_total' must be at least 1")
        
        # Validate chunk_index <= chunk_total
        if "chunk_index" in metadata and "chunk_total" in metadata:
            if metadata["chunk_index"] is not None and metadata["chunk_total"] is not None:
                if metadata["chunk_index"] >= metadata["chunk_total"]:
                    errors.append(f"chunk_index ({metadata['chunk_index']}) must be less than chunk_total ({metadata['chunk_total']})")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_document(
        self,
        document: Dict[str, Any],
        strict: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate document dictionary
        
        Args:
            document: Document dictionary to validate
            strict: If True, all optional fields must be present
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for text or content field
        has_text = "text" in document and document["text"]
        has_content = "content" in document and document["content"]
        
        if not has_text and not has_content:
            errors.append("Document must have either 'text' or 'content' field")
        
        if "text" in document and document["text"]:
            if not isinstance(document["text"], str):
                errors.append("Field 'text' must be a string")
            elif len(document["text"].strip()) == 0:
                errors.append("Field 'text' cannot be empty")
        
        if "content" in document and document["content"]:
            if not isinstance(document["content"], str):
                errors.append("Field 'content' must be a string")
            elif len(document["content"].strip()) == 0:
                errors.append("Field 'content' cannot be empty")
        
        # Validate title if present
        if "title" in document:
            if not isinstance(document["title"], str):
                errors.append("Field 'title' must be a string")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_embedding(
        self,
        embedding: List[float],
        embedding_type: EmbeddingType = EmbeddingType.TEXT
    ) -> Tuple[bool, List[str]]:
        """
        Validate embedding vector
        
        Args:
            embedding: Embedding vector to validate
            embedding_type: Type of embedding (text, image, or multimodal)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(embedding, list):
            errors.append("Embedding must be a list")
            return False, errors
        
        if len(embedding) == 0:
            errors.append("Embedding cannot be empty")
            return False, errors
        
        # Check dimension based on type
        expected_dim = self.TEXT_EMBEDDING_DIM if embedding_type == EmbeddingType.TEXT else self.IMAGE_EMBEDDING_DIM
        
        if len(embedding) != expected_dim:
            errors.append(f"Embedding dimension mismatch: expected {expected_dim}, got {len(embedding)}")
        
        # Check all values are floats
        for i, val in enumerate(embedding):
            if not isinstance(val, (int, float)):
                errors.append(f"Embedding value at index {i} must be a number, got {type(val)}")
                break
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_chunking(
        self,
        chunk_size: int,
        chunk_overlap: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate chunking parameters
        
        Args:
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(chunk_size, int):
            errors.append("chunk_size must be an integer")
        elif chunk_size < self.MIN_CHUNK_SIZE:
            errors.append(f"chunk_size ({chunk_size}) must be at least {self.MIN_CHUNK_SIZE}")
        elif chunk_size > self.MAX_CHUNK_SIZE:
            errors.append(f"chunk_size ({chunk_size}) must be at most {self.MAX_CHUNK_SIZE}")
        
        if not isinstance(chunk_overlap, int):
            errors.append("chunk_overlap must be an integer")
        elif chunk_overlap < 0:
            errors.append("chunk_overlap must be non-negative")
        elif chunk_overlap >= chunk_size:
            errors.append(f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_knowledge_base_schema(
        self,
        schema: KnowledgeBaseSchema
    ) -> Tuple[bool, List[str]]:
        """
        Validate a complete KnowledgeBaseSchema object
        
        Args:
            schema: KnowledgeBaseSchema instance to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate ID
        if not schema.id:
            errors.append("Schema ID cannot be empty")
        
        # Validate metadata
        if schema.metadata:
            is_valid, metadata_errors = self.validate_metadata(schema.metadata.to_dict())
            if not is_valid:
                errors.extend([f"Metadata: {e}" for e in metadata_errors])
        else:
            errors.append("Schema must have metadata")
        
        # Validate embeddings
        if schema.text_embedding and schema.image_embedding:
            # Multi-modal
            is_valid, text_errors = self.validate_embedding(schema.text_embedding, EmbeddingType.TEXT)
            if not is_valid:
                errors.extend([f"Text embedding: {e}" for e in text_errors])
            
            is_valid, image_errors = self.validate_embedding(schema.image_embedding, EmbeddingType.IMAGE)
            if not is_valid:
                errors.extend([f"Image embedding: {e}" for e in image_errors])
        elif schema.text_embedding:
            # Text only
            embedding_type = schema.metadata.embedding_type if schema.metadata else EmbeddingType.TEXT
            is_valid, text_errors = self.validate_embedding(schema.text_embedding, embedding_type)
            if not is_valid:
                errors.extend([f"Text embedding: {e}" for e in text_errors])
        elif schema.vector:
            # Single vector
            embedding_type = schema.metadata.embedding_type if schema.metadata else EmbeddingType.TEXT
            is_valid, vector_errors = self.validate_embedding(schema.vector, embedding_type)
            if not is_valid:
                errors.extend([f"Vector: {e}" for e in vector_errors])
        else:
            errors.append("Schema must have at least one embedding (text_embedding, image_embedding, or vector)")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_for_qdrant_query(
        self,
        filters: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate filter dictionary for Qdrant queries
        
        Args:
            filters: Filter dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        valid_filter_keys = [
            "title", "source", "domain", "year", "embedding_type", "access_type",
            "provenance_url", "version", "author", "chunk_index", "chunk_total",
            "created_at", "updated_at", "doc_hash", "text"
        ]
        
        for key in filters.keys():
            if key not in valid_filter_keys:
                errors.append(f"Invalid filter key: {key}. Valid keys: {valid_filter_keys}")
        
        # Validate range filters
        for key, value in filters.items():
            if isinstance(value, dict):
                if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                    # Range filter
                    for op in ["gte", "lte", "gt", "lt"]:
                        if op in value:
                            val = value[op]
                            # Allow numbers, strings (for ISO datetime), or datetime objects
                            if not isinstance(val, (int, float, str, datetime)):
                                errors.append(f"Range filter '{key}.{op}' must be a number, ISO datetime string, or datetime object")
                            # If it's a string, try to validate it could be a datetime or number
                            elif isinstance(val, str):
                                # Check if it's a valid ISO datetime or numeric string
                                try:
                                    # Try parsing as ISO datetime
                                    datetime.fromisoformat(val.replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    try:
                                        # Try parsing as number
                                        float(val)
                                    except (ValueError, TypeError):
                                        errors.append(f"Range filter '{key}.{op}' string value must be a valid ISO datetime or number")
                elif "in" in value:
                    # In filter
                    if not isinstance(value["in"], list):
                        errors.append(f"Filter '{key}.in' must be a list")
        
        is_valid = len(errors) == 0
        return is_valid, errors

