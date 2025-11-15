"""
Unit tests for schema validator
"""

import pytest
from src.storage.schema_validator import (
    SchemaValidator,
    SchemaValidationError
)
from src.storage.schema import (
    KnowledgeBaseMetadata,
    KnowledgeBaseSchema,
    EmbeddingType,
    AccessType
)


class TestSchemaValidator:
    """Test SchemaValidator"""
    
    def test_initialization(self):
        """Test validator initialization"""
        validator = SchemaValidator()
        assert validator is not None
    
    def test_validate_metadata_valid(self):
        """Test validating valid metadata"""
        validator = SchemaValidator()
        
        metadata = {
            "title": "Test Document",
            "source": "demo",
            "domain": "pathology",
            "year": 2023,
            "embedding_type": "text",
            "access_type": "open"
        }
        
        is_valid, errors = validator.validate_metadata(metadata)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_metadata_missing_required(self):
        """Test validating metadata with missing required fields"""
        validator = SchemaValidator()
        
        metadata = {
            "title": "Test Document"
            # Missing "source"
        }
        
        is_valid, errors = validator.validate_metadata(metadata)
        assert is_valid is False
        assert any("source" in error.lower() for error in errors)
    
    def test_validate_metadata_invalid_domain(self):
        """Test validating metadata with invalid domain"""
        validator = SchemaValidator()
        
        metadata = {
            "title": "Test Document",
            "source": "demo",
            "domain": "invalid_domain"
        }
        
        is_valid, errors = validator.validate_metadata(metadata)
        assert is_valid is False
        assert any("domain" in error.lower() for error in errors)
    
    def test_validate_metadata_invalid_year(self):
        """Test validating metadata with invalid year"""
        validator = SchemaValidator()
        
        metadata = {
            "title": "Test Document",
            "source": "demo",
            "year": 1800  # Too old
        }
        
        is_valid, errors = validator.validate_metadata(metadata)
        assert is_valid is False
        assert any("year" in error.lower() for error in errors)
    
    def test_validate_metadata_invalid_url(self):
        """Test validating metadata with invalid URL"""
        validator = SchemaValidator()
        
        metadata = {
            "title": "Test Document",
            "source": "demo",
            "provenance_url": "not-a-valid-url"
        }
        
        is_valid, errors = validator.validate_metadata(metadata)
        assert is_valid is False
        assert any("url" in error.lower() for error in errors)
    
    def test_validate_metadata_chunk_validation(self):
        """Test chunk index/total validation"""
        validator = SchemaValidator()
        
        metadata = {
            "title": "Test Document",
            "source": "demo",
            "chunk_index": 5,
            "chunk_total": 3  # chunk_index >= chunk_total
        }
        
        is_valid, errors = validator.validate_metadata(metadata)
        assert is_valid is False
        assert any("chunk_index" in error.lower() for error in errors)
    
    def test_validate_document_valid(self):
        """Test validating valid document"""
        validator = SchemaValidator()
        
        document = {
            "title": "Test Document",
            "text": "This is test content for the document."
        }
        
        is_valid, errors = validator.validate_document(document)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_document_missing_text(self):
        """Test validating document without text"""
        validator = SchemaValidator()
        
        document = {
            "title": "Test Document"
            # Missing "text" or "content"
        }
        
        is_valid, errors = validator.validate_document(document)
        assert is_valid is False
        assert any("text" in error.lower() or "content" in error.lower() for error in errors)
    
    def test_validate_embedding_text(self):
        """Test validating text embedding"""
        validator = SchemaValidator()
        
        # Valid 768-dim embedding
        embedding = [0.1] * 768
        is_valid, errors = validator.validate_embedding(embedding, EmbeddingType.TEXT)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_embedding_wrong_dimension(self):
        """Test validating embedding with wrong dimension"""
        validator = SchemaValidator()
        
        # Wrong dimension (384 instead of 768)
        embedding = [0.1] * 384
        is_valid, errors = validator.validate_embedding(embedding, EmbeddingType.TEXT)
        assert is_valid is False
        assert any("dimension" in error.lower() for error in errors)
    
    def test_validate_embedding_empty(self):
        """Test validating empty embedding"""
        validator = SchemaValidator()
        
        embedding = []
        is_valid, errors = validator.validate_embedding(embedding, EmbeddingType.TEXT)
        assert is_valid is False
        assert any("empty" in error.lower() for error in errors)
    
    def test_validate_chunking_valid(self):
        """Test validating valid chunking parameters"""
        validator = SchemaValidator()
        
        is_valid, errors = validator.validate_chunking(512, 50)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_chunking_invalid_size(self):
        """Test validating invalid chunk size"""
        validator = SchemaValidator()
        
        is_valid, errors = validator.validate_chunking(50, 10)  # Too small
        assert is_valid is False
        assert any("chunk_size" in error.lower() for error in errors)
    
    def test_validate_chunking_invalid_overlap(self):
        """Test validating invalid overlap"""
        validator = SchemaValidator()
        
        is_valid, errors = validator.validate_chunking(512, 600)  # Overlap >= size
        assert is_valid is False
        assert any("overlap" in error.lower() for error in errors)
    
    def test_validate_knowledge_base_schema(self):
        """Test validating complete KnowledgeBaseSchema"""
        validator = SchemaValidator()
        
        metadata = KnowledgeBaseMetadata(
            title="Test Document",
            source="demo",
            domain="pathology"
        )
        
        schema = KnowledgeBaseSchema(
            id="test-id",
            text_embedding=[0.1] * 768,
            metadata=metadata
        )
        
        is_valid, errors = validator.validate_knowledge_base_schema(schema)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_knowledge_base_schema_no_embedding(self):
        """Test validating schema without embedding"""
        validator = SchemaValidator()
        
        metadata = KnowledgeBaseMetadata(
            title="Test Document",
            source="demo"
        )
        
        schema = KnowledgeBaseSchema(
            id="test-id",
            metadata=metadata
            # No embedding
        )
        
        is_valid, errors = validator.validate_knowledge_base_schema(schema)
        assert is_valid is False
        assert any("embedding" in error.lower() for error in errors)
    
    def test_validate_for_qdrant_query(self):
        """Test validating Qdrant query filters"""
        validator = SchemaValidator()
        
        filters = {
            "domain": "pathology",
            "year": {"gte": 2020, "lte": 2023},
            "source": "demo"
        }
        
        is_valid, errors = validator.validate_for_qdrant_query(filters)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_for_qdrant_query_invalid_key(self):
        """Test validating filters with invalid key"""
        validator = SchemaValidator()
        
        filters = {
            "invalid_field": "value"
        }
        
        is_valid, errors = validator.validate_for_qdrant_query(filters)
        assert is_valid is False
        assert any("invalid" in error.lower() for error in errors)
    
    def test_validate_for_qdrant_query_invalid_range(self):
        """Test validating filters with invalid range"""
        validator = SchemaValidator()
        
        filters = {
            "year": {"gte": "not-a-number"}
        }
        
        is_valid, errors = validator.validate_for_qdrant_query(filters)
        assert is_valid is False
        assert any("range" in error.lower() for error in errors)

