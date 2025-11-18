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
# Lazy import encryption to avoid blocking if cryptography not available
# EncryptionManager and DeIdentificationManager are imported on-demand
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

# Lazy import functions for encryption classes
def _get_encryption_manager():
    """Lazy import EncryptionManager"""
    from .encryption import EncryptionManager
    return EncryptionManager

def _get_deidentification_manager():
    """Lazy import DeIdentificationManager"""
    from .encryption import DeIdentificationManager
    return DeIdentificationManager

# Provide EncryptionManager and DeIdentificationManager as lazy imports
def __getattr__(name):
    if name == "EncryptionManager":
        return _get_encryption_manager()
    if name == "DeIdentificationManager":
        return _get_deidentification_manager()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "QdrantStorage",
    "TranscriptStorage",
    "EncryptionManager",  # Available via __getattr__
    "DeIdentificationManager",  # Available via __getattr__
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
