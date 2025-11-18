"""
Knowledge Ingestion Pipeline

Handles:
- Document chunking
- Embedding generation
- Upserting into Qdrant
- Idempotent delta-ingestion
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timezone
from pathlib import Path

from .qdrant_storage import QdrantStorage
from .schema import KnowledgeBaseMetadata, KnowledgeBaseSchema, EmbeddingType, AccessType
from .schema_validator import SchemaValidator

# Optional imports for compliance features
try:
    from src.compliance.license_validator import LicenseValidator
    from src.compliance.audit_logger import AuditLogger, AuditEventType, AuditLevel
    COMPLIANCE_AVAILABLE = True
except ImportError:
    COMPLIANCE_AVAILABLE = False
    logger.warning("Compliance modules not available. License validation and audit logging disabled.")

logger = logging.getLogger(__name__)


class KnowledgeIngestionPipeline:
    """
    Pipeline for ingesting knowledge base documents into Qdrant
    
    Features:
    - Document chunking
    - Embedding generation
    - Upserting into Qdrant
    - Idempotent delta-ingestion
    - Version tracking
    """
    
    def __init__(
        self,
        qdrant_storage: QdrantStorage,
        text_embedding_generator: Optional[Callable] = None,
        image_embedding_generator: Optional[Callable] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        validate_schema: bool = True,
        enforce_open_access: bool = True,
        license_validator: Optional[LicenseValidator] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize knowledge ingestion pipeline
        
        Args:
            qdrant_storage: QdrantStorage instance
            text_embedding_generator: Optional function to generate text embeddings
            image_embedding_generator: Optional function to generate image embeddings
            chunk_size: Size of text chunks (in characters)
            chunk_overlap: Overlap between chunks (in characters)
            validate_schema: Whether to validate documents against schema standard
            enforce_open_access: Whether to enforce open-access-only policy
            license_validator: Optional license validator instance
            audit_logger: Optional audit logger instance
        """
        self.qdrant_storage = qdrant_storage
        self.text_embedding_generator = text_embedding_generator
        self.image_embedding_generator = image_embedding_generator
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.validate_schema = validate_schema
        self.enforce_open_access = enforce_open_access and COMPLIANCE_AVAILABLE
        self.validator = SchemaValidator() if validate_schema else None
        
        # Initialize compliance components
        if COMPLIANCE_AVAILABLE:
            self.license_validator = license_validator or LicenseValidator(strict_mode=enforce_open_access)
            self.audit_logger = audit_logger
        else:
            self.license_validator = None
            self.audit_logger = None
        
        logger.info(f"Knowledge ingestion pipeline initialized (open_access={self.enforce_open_access})")
    
    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces
        
        Args:
            text: Input text to chunk
            chunk_size: Size of chunks (default: self.chunk_size)
            chunk_overlap: Overlap between chunks (default: self.chunk_overlap)
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    "start": start,
                    "end": end
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = end - chunk_overlap
        
        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    def generate_document_hash(self, document: Dict[str, Any]) -> str:
        """
        Generate hash for document to detect changes
        
        Args:
            document: Document dictionary
            
        Returns:
            SHA-256 hash of document
        """
        # Create hash from document content
        content = str(document.get("title", "")) + str(document.get("text", "")) + str(document.get("source", ""))
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()
    
    def ingest_document(
        self,
        document: Dict[str, Any],
        metadata: Optional[KnowledgeBaseMetadata] = None,
        force_update: bool = False
    ) -> List[str]:
        """
        Ingest a single document into Qdrant
        
        Args:
            document: Document dictionary with title, text, source, etc.
            metadata: Optional knowledge base metadata
            force_update: Force update even if document hasn't changed
            
        Returns:
            List of point IDs for ingested chunks
        """
        point_ids = []
        
        try:
            # Generate document hash
            doc_hash = self.generate_document_hash(document)
            
            # Check if document already exists (idempotent ingestion)
            if not force_update:
                try:
                    # Check for existing document with same hash
                    existing_docs = self.qdrant_storage.search_with_filters(
                        query_embedding=[0.0] * self.qdrant_storage.vector_size,  # Dummy embedding
                        filters={"doc_hash": doc_hash},
                        limit=1
                    )
                    if existing_docs:
                        logger.info(f"Document already exists (hash: {doc_hash[:8]}...), skipping")
                        return [existing_docs[0]["id"]]
                except Exception as dup_check_error:
                    # If duplicate check fails (e.g., index not created), log and continue
                    # This allows ingestion to proceed even if duplicate checking isn't available
                    error_msg = str(dup_check_error)
                    if "Index required" in error_msg or "doc_hash" in error_msg.lower():
                        logger.warning(
                            f"Duplicate check skipped (doc_hash index not available): {error_msg[:100]}. "
                            f"Continuing with ingestion. To enable duplicate checking, create an index for 'doc_hash'."
                        )
                    else:
                        # Re-raise if it's a different error
                        raise
            
            # Prepare metadata
            if not metadata:
                metadata = KnowledgeBaseMetadata(
                    title=document.get("title", ""),
                    source=document.get("source", ""),
                    domain=document.get("domain"),
                    year=document.get("year"),
                    embedding_type=EmbeddingType.TEXT,
                    access_type=AccessType.OPEN,
                    provenance_url=document.get("provenance_url"),
                    version=document.get("version", "1.0"),
                    author=document.get("author"),
                    created_at=datetime.now(timezone.utc)
                )
            
            # Get text content (handle both 'text' and 'content' fields)
            text = document.get("text", "") or document.get("content", "")
            
            # Validate provenance URL
            provenance_url = document.get("provenance_url") or metadata.provenance_url if metadata else None
            if self.license_validator:
                # Skip validation for user uploads (hygiaai.local) or if URL is None
                if provenance_url and not provenance_url.startswith("https://hygiaai.local/"):
                    is_valid, error = self.license_validator.validate_provenance_url(provenance_url)
                    if not is_valid:
                        raise ValueError(f"Invalid provenance URL: {error}")
            
            # Validate license and access type (enforce open-access-only)
            if self.enforce_open_access and self.license_validator:
                url = provenance_url or document.get("url")
                license_text = document.get("license") or document.get("license_text")
                is_allowed, error = self.license_validator.enforce_open_access_only(
                    document, url=url, license_text=license_text
                )
                if not is_allowed:
                    # Log failed validation
                    if self.audit_logger:
                        self.audit_logger.log_event(
                            event_type=AuditEventType.KNOWLEDGE_ACCESS_VALIDATION,
                            resource_type="knowledge_document",
                            resource_id=document.get("title", "unknown"),
                            action="access_validation",
                            result="denied",
                            details={
                                "reason": error,
                                "url": url,
                                "source": document.get("source", "unknown")
                            },
                            severity=AuditLevel.WARNING
                        )
                    raise ValueError(f"Access validation failed: {error}")
                
                # Log successful validation
                if self.audit_logger:
                    self.audit_logger.log_event(
                        event_type=AuditEventType.KNOWLEDGE_ACCESS_VALIDATION,
                        resource_type="knowledge_document",
                        resource_id=document.get("title", "unknown"),
                        action="access_validation",
                        result="success",
                        details={
                            "url": url,
                            "source": document.get("source", "unknown"),
                            "access_type": "open"
                        },
                        severity=AuditLevel.INFO
                    )
            
            # Validate metadata and document before ingestion
            if self.validator:
                # Validate metadata
                is_valid, errors = self.validator.validate_metadata(metadata.to_dict())
                if not is_valid:
                    raise ValueError(f"Invalid metadata: {errors}")
                
                # Validate document
                doc_for_validation = {
                    "text": text,
                    "title": document.get("title", "")
                }
                is_valid, errors = self.validator.validate_document(doc_for_validation)
                if not is_valid:
                    raise ValueError(f"Invalid document: {errors}")
            chunks = []
            if text:
                chunks = self.chunk_text(text)
            else:
                # Single chunk if no text
                chunks = [{"text": "", "chunk_index": 0, "start": 0, "end": 0}]
            
            # Validate chunking parameters
            if self.validator:
                is_valid, errors = self.validator.validate_chunking(self.chunk_size, self.chunk_overlap)
                if not is_valid:
                    logger.warning(f"Invalid chunking parameters: {errors}")
            
            # Update metadata with chunk info
            metadata.chunk_total = len(chunks)
            
            # Process each chunk
            for chunk in chunks:
                chunk_metadata = KnowledgeBaseMetadata(
                    title=metadata.title,
                    source=metadata.source,
                    domain=metadata.domain,
                    year=metadata.year,
                    embedding_type=metadata.embedding_type,
                    access_type=metadata.access_type,
                    provenance_url=metadata.provenance_url,
                    version=metadata.version,
                    author=metadata.author,
                    chunk_index=chunk["chunk_index"],
                    chunk_total=metadata.chunk_total,
                    created_at=metadata.created_at,
                    updated_at=datetime.now(timezone.utc)
                )
                
                # Prepare chunk data
                chunk_data = {
                    "text": chunk["text"],
                    "doc_hash": doc_hash,
                    "chunk_index": chunk["chunk_index"],
                    "chunk_start": chunk["start"],
                    "chunk_end": chunk["end"]
                }
                
                # Generate embeddings
                text_embedding = None
                if self.text_embedding_generator and chunk["text"]:
                    try:
                        text_embedding = self.text_embedding_generator(chunk["text"])
                        # Validate embedding
                        if self.validator:
                            is_valid, errors = self.validator.validate_embedding(
                                text_embedding, 
                                chunk_metadata.embedding_type
                            )
                            if not is_valid:
                                logger.error(f"Invalid embedding generated: {errors}")
                                raise ValueError(f"Invalid embedding: {errors}")
                    except Exception as e:
                        logger.error(f"Error generating text embedding: {e}")
                        raise
                
                image_embedding = None
                if self.image_embedding_generator and document.get("image_path"):
                    try:
                        image_embedding = self.image_embedding_generator(document["image_path"])
                        chunk_metadata.embedding_type = EmbeddingType.MULTIMODAL
                    except Exception as e:
                        logger.error(f"Error generating image embedding: {e}")
                
                # Store in Qdrant
                point_id = self.qdrant_storage.store_knowledge_base_document(
                    document_data=chunk_data,
                    text_embedding=text_embedding,
                    image_embedding=image_embedding,
                    metadata=chunk_metadata
                )
                point_ids.append(point_id)
            
            logger.info(f"Ingested document '{metadata.title}' with {len(chunks)} chunks")
            
            # Log successful ingestion
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type=AuditEventType.KNOWLEDGE_INGESTION,
                    resource_type="knowledge_document",
                    resource_id=metadata.title,
                    action="ingest",
                    result="success",
                    details={
                        "source": metadata.source,
                        "domain": metadata.domain,
                        "provenance_url": metadata.provenance_url,
                        "chunks": len(chunks),
                        "access_type": metadata.access_type.value if metadata.access_type else "open",
                        "year": metadata.year
                    },
                    severity=AuditLevel.INFO
                )
            
            return point_ids
            
        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            
            # Log failed ingestion
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type=AuditEventType.KNOWLEDGE_INGESTION_FAILED,
                    resource_type="knowledge_document",
                    resource_id=document.get("title", "unknown"),
                    action="ingest",
                    result="failure",
                    details={
                        "error": str(e),
                        "source": document.get("source", "unknown"),
                        "url": document.get("provenance_url") or document.get("url")
                    },
                    severity=AuditLevel.ERROR
                )
            
            raise
    
    def ingest_batch(
        self,
        documents: List[Dict[str, Any]],
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest multiple documents in batch
        
        Args:
            documents: List of document dictionaries
            force_update: Force update even if documents haven't changed
            
        Returns:
            Dictionary with ingestion statistics
        """
        stats = {
            "total": len(documents),
            "ingested": 0,
            "skipped": 0,
            "errors": 0,
            "point_ids": []
        }
        
        for doc in documents:
            try:
                point_ids = self.ingest_document(doc, force_update=force_update)
                if point_ids:
                    stats["ingested"] += 1
                    stats["point_ids"].extend(point_ids)
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error ingesting document: {e}")
                stats["errors"] += 1
        
        logger.info(f"Batch ingestion complete: {stats['ingested']} ingested, {stats['skipped']} skipped, {stats['errors']} errors")
        return stats
    
    def delta_ingest(
        self,
        documents: List[Dict[str, Any]],
        last_ingestion_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Delta ingestion - only ingest new or updated documents
        
        Args:
            documents: List of document dictionaries
            last_ingestion_time: Optional timestamp of last ingestion
            
        Returns:
            Dictionary with delta ingestion statistics
        """
        stats = {
            "total": len(documents),
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "errors": 0,
            "point_ids": []
        }
        
        for doc in documents:
            try:
                # Check if document is new or updated
                doc_hash = self.generate_document_hash(doc)
                doc_updated = doc.get("updated_at")
                
                if last_ingestion_time and doc_updated:
                    # Check if document was updated since last ingestion
                    if isinstance(doc_updated, str):
                        doc_updated = datetime.fromisoformat(doc_updated)
                    if doc_updated <= last_ingestion_time:
                        stats["unchanged"] += 1
                        continue
                
                # Check if document exists
                existing_docs = self.qdrant_storage.search_with_filters(
                    query_embedding=[0.0] * self.qdrant_storage.vector_size,
                    filters={"doc_hash": doc_hash},
                    limit=1
                )
                
                if existing_docs:
                    # Document exists - check if updated
                    stats["updated"] += 1
                    point_ids = self.ingest_document(doc, force_update=True)
                else:
                    # New document
                    stats["new"] += 1
                    point_ids = self.ingest_document(doc, force_update=False)
                
                stats["point_ids"].extend(point_ids)
                
            except Exception as e:
                logger.error(f"Error in delta ingestion: {e}")
                stats["errors"] += 1
        
        logger.info(f"Delta ingestion complete: {stats['new']} new, {stats['updated']} updated, {stats['unchanged']} unchanged, {stats['errors']} errors")
        return stats

