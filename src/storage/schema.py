"""
Storage Schema for Transcripts and Knowledge Base Documents

Defines data structures for storing transcripts and knowledge base documents in Qdrant
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum


class ModalityType(Enum):
    """Types of data modalities"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"


class EmbeddingType(Enum):
    """Types of embeddings"""
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"


class AccessType(Enum):
    """Access types for knowledge base documents"""
    OPEN = "open"
    RESTRICTED = "restricted"
    PRIVATE = "private"


@dataclass
class StorageMetadata:
    """Metadata for stored transcripts"""
    session_id: str
    patient_id: Optional[str] = None  # Anonymized/hashed
    doctor_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modality: ModalityType = ModalityType.TEXT
    confidence: Optional[float] = None
    speaker: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime to ISO format
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        if isinstance(data.get("processed_at"), datetime):
            data["processed_at"] = data["processed_at"].isoformat()
        # Convert enum to value
        if isinstance(data.get("modality"), ModalityType):
            data["modality"] = data["modality"].value
        return data


@dataclass
class TranscriptSchema:
    """Schema for transcript storage in Qdrant"""
    # Vector ID (unique identifier)
    id: str
    
    # Vector embedding (will be set separately)
    vector: Optional[List[float]] = None
    
    # Payload (metadata and transcript data)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Optional[StorageMetadata] = None
    
    def to_qdrant_point(self) -> Dict[str, Any]:
        """
        Convert to Qdrant point format
        
        Returns:
            Dictionary in Qdrant point format
        """
        point = {
            "id": self.id,
            "vector": self.vector or [],
        }
        
        # Add payload
        if self.metadata:
            point["payload"] = {
                **self.metadata.to_dict(),
                **self.payload
            }
        else:
            point["payload"] = self.payload
        
        return point
    
    @classmethod
    def from_qdrant_point(cls, point: Dict[str, Any]) -> "TranscriptSchema":
        """
        Create from Qdrant point format
        
        Args:
            point: Qdrant point dictionary
            
        Returns:
            TranscriptSchema instance
        """
        payload = point.get("payload", {})
        
        # Extract metadata
        metadata = StorageMetadata(
            session_id=payload.get("session_id", ""),
            patient_id=payload.get("patient_id"),
            doctor_id=payload.get("doctor_id"),
            timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.now(timezone.utc).isoformat())),
            modality=ModalityType(payload.get("modality", "text")),
            confidence=payload.get("confidence"),
            speaker=payload.get("speaker"),
            processed_at=datetime.fromisoformat(payload["processed_at"]) if payload.get("processed_at") else None
        )
        
        # Extract transcript data (exclude metadata fields)
        transcript_payload = {
            k: v for k, v in payload.items()
            if k not in ["session_id", "patient_id", "doctor_id", "timestamp", "modality", "confidence", "speaker", "processed_at"]
        }
        
        return cls(
            id=point.get("id", ""),
            vector=point.get("vector"),
            payload=transcript_payload,
            metadata=metadata
        )


@dataclass
class KnowledgeBaseMetadata:
    """Metadata for knowledge base documents"""
    title: str
    source: str  # e.g., "NCBI Bookshelf", "PubMed OA", "WHO eLENA"
    domain: Optional[str] = None  # e.g., "pathology", "pharmacology", "guidelines"
    year: Optional[int] = None
    embedding_type: EmbeddingType = EmbeddingType.TEXT
    access_type: AccessType = AccessType.OPEN
    provenance_url: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    chunk_index: Optional[int] = None  # For chunked documents
    chunk_total: Optional[int] = None  # Total number of chunks
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime to ISO format
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("updated_at"), datetime):
            data["updated_at"] = data["updated_at"].isoformat()
        # Convert enums to values
        if isinstance(data.get("embedding_type"), EmbeddingType):
            data["embedding_type"] = data["embedding_type"].value
        if isinstance(data.get("access_type"), AccessType):
            data["access_type"] = data["access_type"].value
        return data


@dataclass
class KnowledgeBaseSchema:
    """Schema for knowledge base document storage in Qdrant"""
    # Vector ID (unique identifier)
    id: str
    
    # Vector embedding(s) - can be single vector or multi-vector
    vector: Optional[List[float]] = None
    text_embedding: Optional[List[float]] = None  # For multi-modal
    image_embedding: Optional[List[float]] = None  # For multi-modal
    
    # Payload (metadata and document content)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Optional[KnowledgeBaseMetadata] = None
    
    def to_qdrant_point(self) -> Dict[str, Any]:
        """
        Convert to Qdrant point format
        
        Returns:
            Dictionary in Qdrant point format
        """
        point = {
            "id": self.id,
        }
        
        # Handle multi-vector embeddings
        if self.text_embedding and self.image_embedding:
            # Multi-vector: use named vectors
            point["vector"] = {
                "text": self.text_embedding,
                "image": self.image_embedding
            }
        elif self.text_embedding:
            # Single vector from text_embedding
            point["vector"] = self.text_embedding
        elif self.vector:
            # Single vector
            point["vector"] = self.vector
        else:
            # No vector provided - this should not happen in production
            # But we need to provide a valid vector for Qdrant
            raise ValueError("No embedding vector provided. Cannot store point without vector.")
        
        # Add payload
        if self.metadata:
            point["payload"] = {
                **self.metadata.to_dict(),
                **self.payload
            }
        else:
            point["payload"] = self.payload
        
        return point
    
    @classmethod
    def from_qdrant_point(cls, point: Dict[str, Any]) -> "KnowledgeBaseSchema":
        """
        Create from Qdrant point format
        
        Args:
            point: Qdrant point dictionary
            
        Returns:
            KnowledgeBaseSchema instance
        """
        payload = point.get("payload", {})
        vector = point.get("vector", {})
        
        # Handle multi-vector embeddings
        text_embedding = None
        image_embedding = None
        single_vector = None
        
        if isinstance(vector, dict):
            # Multi-vector
            text_embedding = vector.get("text")
            image_embedding = vector.get("image")
        elif isinstance(vector, list):
            # Single vector
            single_vector = vector
        
        # Extract metadata
        metadata = KnowledgeBaseMetadata(
            title=payload.get("title", ""),
            source=payload.get("source", ""),
            domain=payload.get("domain"),
            year=payload.get("year"),
            embedding_type=EmbeddingType(payload.get("embedding_type", "text")),
            access_type=AccessType(payload.get("access_type", "open")),
            provenance_url=payload.get("provenance_url"),
            version=payload.get("version"),
            author=payload.get("author"),
            chunk_index=payload.get("chunk_index"),
            chunk_total=payload.get("chunk_total"),
            created_at=datetime.fromisoformat(payload.get("created_at", datetime.now(timezone.utc).isoformat())),
            updated_at=datetime.fromisoformat(payload["updated_at"]) if payload.get("updated_at") else None
        )
        
        # Extract document data (exclude metadata fields)
        metadata_fields = [
            "title", "source", "domain", "year", "embedding_type", "access_type",
            "provenance_url", "version", "author", "chunk_index", "chunk_total",
            "created_at", "updated_at"
        ]
        document_payload = {
            k: v for k, v in payload.items()
            if k not in metadata_fields
        }
        
        return cls(
            id=point.get("id", ""),
            vector=single_vector,
            text_embedding=text_embedding,
            image_embedding=image_embedding,
            payload=document_payload,
            metadata=metadata
        )

