"""
Storage Module for HygiaAI

Handles:
- Qdrant vector database integration
- Transcript storage and retrieval
- Knowledge base document storage
- Multi-vector embeddings
- Encryption for HIPAA compliance
- Database schema management
"""

from .qdrant_storage import QdrantStorage, TranscriptStorage
from .encryption import EncryptionManager, DeIdentificationManager
from .knowledge_ingestion import KnowledgeIngestionPipeline
from .schema import (
    TranscriptSchema,
    StorageMetadata,
    ModalityType,
    KnowledgeBaseSchema,
    KnowledgeBaseMetadata,
    EmbeddingType,
    AccessType,
)
from .schema_validator import SchemaValidator, SchemaValidationError

__all__ = [
    "QdrantStorage",
    "TranscriptStorage",
    "EncryptionManager",
    "DeIdentificationManager",
    "KnowledgeIngestionPipeline",
    "TranscriptSchema",
    "StorageMetadata",
    "ModalityType",
    "KnowledgeBaseSchema",
    "KnowledgeBaseMetadata",
    "EmbeddingType",
    "AccessType",
    "SchemaValidator",
    "SchemaValidationError",
]
