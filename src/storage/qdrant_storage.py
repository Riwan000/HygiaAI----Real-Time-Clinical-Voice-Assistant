"""
Qdrant Storage Module

Handles:
- Qdrant vector database connection
- Transcript storage with embeddings
- Similarity search and retrieval
- HIPAA-compliant data handling
"""

import os
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
        MatchAny,
        Range,
        CollectionStatus,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Qdrant client not available. Install with: pip install qdrant-client")

# DEEPGRAM_API_KEY not needed for Qdrant storage
from .schema import (
    TranscriptSchema,
    StorageMetadata,
    ModalityType,
    KnowledgeBaseSchema,
    KnowledgeBaseMetadata,
    EmbeddingType,
    AccessType,
)
from .encryption import EncryptionManager, DeIdentificationManager

logger = logging.getLogger(__name__)


class QdrantStorage:
    """
    Qdrant vector database storage manager
    
    Features:
    - Vector storage and retrieval
    - Similarity search
    - Payload filtering
    - Collection management
    - HIPAA-compliant data handling
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = "hygiaai_transcripts",
        vector_size: int = 768,  # Default embedding size (BioBERT = 768)
        encryption_key: Optional[str] = None,
        enable_encryption: bool = True,
        enable_deidentification: bool = True
    ):
        """
        Initialize Qdrant storage
        
        Args:
            host: Qdrant host (default: localhost) - used if url is not provided
            port: Qdrant port (default: 6333) - used if url is not provided
            url: Qdrant Cloud URL (e.g., "https://xxx.cloud.qdrant.io:6333") - takes precedence over host/port
            api_key: Optional Qdrant API key for authentication (required for cloud)
            collection_name: Name of the collection
            vector_size: Size of embedding vectors
            encryption_key: Optional encryption key
            enable_encryption: Enable encryption for sensitive data
            enable_deidentification: Enable de-identification of PHI
        """
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "Qdrant client not available. Install with: pip install qdrant-client"
            )
        
        # Prefer URL (for cloud) over host/port (for local)
        self.url = url or os.getenv("QDRANT_URL")
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize Qdrant client
        # Use URL for cloud, host/port for local
        client_kwargs = {}
        if self.url:
            # Cloud connection with URL
            client_kwargs["url"] = self.url
            if self.api_key:
                client_kwargs["api_key"] = self.api_key
        else:
            # Local connection with host/port
            client_kwargs["host"] = self.host
            client_kwargs["port"] = self.port
            if self.api_key:
                client_kwargs["api_key"] = self.api_key
        
        self.client = QdrantClient(**client_kwargs)
        
        # Initialize encryption and de-identification
        self.encryption_manager = EncryptionManager(encryption_key) if enable_encryption else None
        self.deidentification_manager = DeIdentificationManager() if enable_deidentification else None
        self.enable_encryption = enable_encryption
        self.enable_deidentification = enable_deidentification
        
        # Create collection if it doesn't exist
        self._ensure_collection()
        
        if self.url:
            logger.info(f"Qdrant storage initialized (Cloud): {self.url}/{self.collection_name}")
        else:
            logger.info(f"Qdrant storage initialized (Local): {self.host}:{self.port}/{self.collection_name}")
    
    def _ensure_collection(self):
        """Ensure collection exists, create if it doesn't"""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name} with vector_size={self.vector_size}")
                
                # Create index for doc_hash if this is a knowledge base collection
                # This allows efficient duplicate checking during ingestion
                if "knowledge" in self.collection_name.lower():
                    try:
                        from qdrant_client.models import PayloadSchemaType
                        self.client.create_payload_index(
                            collection_name=self.collection_name,
                            field_name="doc_hash",
                            field_schema=PayloadSchemaType.KEYWORD
                        )
                        logger.info(f"Created payload index for 'doc_hash' in {self.collection_name}")
                    except Exception as index_error:
                        logger.warning(f"Could not create doc_hash index (may already exist): {index_error}")
            else:
                # Check if existing collection has correct vector size
                collection_info = self.client.get_collection(self.collection_name)
                existing_size = collection_info.config.params.vectors.size if hasattr(collection_info.config.params, 'vectors') else None
                if existing_size != self.vector_size:
                    logger.warning(
                        f"Collection {self.collection_name} exists with vector_size={existing_size}, "
                        f"but expected {self.vector_size}. Please recreate the collection or use matching size."
                    )
                else:
                    logger.info(f"Collection already exists: {self.collection_name} with vector_size={self.vector_size}")
                
                # Ensure doc_hash index exists for knowledge base collections
                if "knowledge" in self.collection_name.lower():
                    try:
                        from qdrant_client.models import PayloadSchemaType
                        # Try to create index (will fail silently if it already exists)
                        try:
                            self.client.create_payload_index(
                                collection_name=self.collection_name,
                                field_name="doc_hash",
                                field_schema=PayloadSchemaType.KEYWORD
                            )
                            logger.info(f"Created payload index for 'doc_hash' in {self.collection_name}")
                        except Exception:
                            # Index likely already exists, which is fine
                            pass
                    except Exception as index_error:
                        logger.debug(f"Could not create doc_hash index: {index_error}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def store_transcript(
        self,
        transcript_data: Dict[str, Any],
        embedding: List[float],
        metadata: Optional[Union[StorageMetadata, Dict[str, Any]]] = None
    ) -> str:
        """
        Store transcript in Qdrant
        
        Args:
            transcript_data: Processed transcript data
            embedding: Vector embedding of the transcript
            metadata: Optional storage metadata
            
        Returns:
            Point ID of stored transcript
        """
        # Generate unique ID
        point_id = str(uuid.uuid4())
        
        # Prepare metadata
        if not metadata:
            metadata = StorageMetadata(
                session_id=transcript_data.get("session_id", ""),
                patient_id=transcript_data.get("metadata", {}).get("patient_id"),
                doctor_id=transcript_data.get("metadata", {}).get("doctor_id"),
                timestamp=datetime.fromisoformat(transcript_data.get("timestamp", datetime.now(timezone.utc).isoformat())),
                modality=ModalityType.TEXT,
                confidence=transcript_data.get("confidence"),
                speaker=transcript_data.get("speaker"),
                processed_at=datetime.fromisoformat(transcript_data.get("processed_at", datetime.now(timezone.utc).isoformat()))
            )
        elif isinstance(metadata, dict):
            # Convert dict to StorageMetadata
            metadata = StorageMetadata(
                session_id=metadata.get("session_id", ""),
                patient_id=metadata.get("patient_id"),
                doctor_id=metadata.get("doctor_id"),
                timestamp=datetime.fromisoformat(metadata.get("timestamp", datetime.now(timezone.utc).isoformat())) if isinstance(metadata.get("timestamp"), str) else metadata.get("timestamp", datetime.now(timezone.utc)),
                modality=ModalityType(metadata.get("modality", "text")),
                confidence=metadata.get("confidence"),
                speaker=metadata.get("speaker"),
                processed_at=datetime.fromisoformat(metadata["processed_at"]) if isinstance(metadata.get("processed_at"), str) else metadata.get("processed_at")
            )
        
        # De-identify if enabled
        if self.enable_deidentification and self.deidentification_manager:
            # De-identify patient and doctor IDs
            if metadata.patient_id:
                metadata.patient_id = self.deidentification_manager.hash_patient_id(metadata.patient_id)
            if metadata.doctor_id:
                metadata.doctor_id = self.deidentification_manager.hash_patient_id(metadata.doctor_id)
            
            # De-identify transcript text
            if "transcript" in transcript_data and transcript_data["transcript"]:
                transcript_data["transcript"] = self.deidentification_manager.deidentify_text(
                    transcript_data["transcript"]
                )
        
        # Encrypt sensitive fields if enabled
        if self.enable_encryption and self.encryption_manager:
            fields_to_encrypt = ["transcript", "original_transcript", "patient_id", "doctor_id"]
            transcript_data = self.encryption_manager.encrypt_dict(transcript_data, fields_to_encrypt)
        
        # Create schema
        schema = TranscriptSchema(
            id=point_id,
            vector=embedding,
            payload=transcript_data,
            metadata=metadata
        )
        
        # Convert to Qdrant point
        point_dict = schema.to_qdrant_point()
        
        # Store in Qdrant
        try:
            point = PointStruct(
                id=point_dict["id"],
                vector=point_dict["vector"],
                payload=point_dict["payload"]
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Stored transcript: {point_id}")
            return point_id
        except Exception as e:
            logger.error(f"Error storing transcript: {e}")
            raise
    
    def search_by_entity_type(
        self,
        entity_type: str,
        query_embedding: Optional[List[float]] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for transcripts containing specific entity types
        
        Args:
            entity_type: Type of medical entity to search for (e.g., "symptom", "diagnosis")
            query_embedding: Optional query vector embedding for similarity search
            limit: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of transcripts containing the specified entity type
        """
        # Build filter for entity type
        filters = {
            "medical_entities.entity_type": entity_type
        }
        
        if query_embedding:
            return self.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters
            )
        else:
            # Text-based search (if no embedding provided)
            return self.search_similar(
                query_embedding=[0.0] * self.vector_size,  # Dummy embedding
                limit=limit,
                score_threshold=score_threshold,
                filters=filters
            )
    
    def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar transcripts
        
        Args:
            query_embedding: Query vector embedding
            limit: Number of results to return
            score_threshold: Minimum similarity score
            filters: Optional payload filters (supports nested fields like "medical_entities.entity_type")
            
        Returns:
            List of similar transcripts with scores
        """
        try:
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    # Handle nested fields (e.g., "medical_entities.entity_type")
                    if "." in key:
                        # For nested fields, we need to check if any entity in the array matches
                        # This is a simplified approach - in production, you might want more sophisticated filtering
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    else:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=qdrant_filter
            )
            
            # Process results
            similar_transcripts = []
            for result in results:
                schema = TranscriptSchema.from_qdrant_point({
                    "id": result.id,
                    "vector": result.vector,
                    "payload": result.payload
                })
                
                # Decrypt if enabled
                if self.enable_encryption and self.encryption_manager:
                    fields_to_decrypt = ["transcript", "original_transcript", "patient_id", "doctor_id"]
                    schema.payload = self.encryption_manager.decrypt_dict(schema.payload, fields_to_decrypt)
                
                similar_transcripts.append({
                    "id": result.id,
                    "score": result.score,
                    "transcript": schema.payload.get("transcript", ""),
                    "metadata": schema.metadata.to_dict() if schema.metadata else {},
                    "payload": schema.payload
                })
            
            logger.info(f"Found {len(similar_transcripts)} similar transcripts")
            return similar_transcripts
            
        except Exception as e:
            logger.error(f"Error searching similar transcripts: {e}")
            raise
    
    def get_transcript(self, point_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transcript by ID
        
        Args:
            point_id: Point ID
            
        Returns:
            Transcript data or None if not found
        """
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            
            if not points:
                return None
            
            point = points[0]
            schema = TranscriptSchema.from_qdrant_point({
                "id": point.id,
                "vector": point.vector,
                "payload": point.payload
            })
            
            # Decrypt if enabled
            if self.enable_encryption and self.encryption_manager:
                fields_to_decrypt = ["transcript", "original_transcript", "patient_id", "doctor_id"]
                schema.payload = self.encryption_manager.decrypt_dict(schema.payload, fields_to_decrypt)
            
            return {
                "id": point.id,
                "transcript": schema.payload.get("transcript", ""),
                "metadata": schema.metadata.to_dict() if schema.metadata else {},
                "payload": schema.payload
            }
            
        except Exception as e:
            logger.error(f"Error retrieving transcript: {e}")
            return None
    
    def delete_transcript(self, point_id: str) -> bool:
        """
        Delete transcript by ID
        
        Args:
            point_id: Point ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            logger.info(f"Deleted transcript: {point_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting transcript: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information
        
        Returns:
            Dictionary with collection info
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vector_size": collection_info.config.params.vectors.size if hasattr(collection_info.config.params, 'vectors') else None,
                "points_count": collection_info.points_count,
                "status": collection_info.status.value if hasattr(collection_info.status, 'value') else str(collection_info.status)
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def store_knowledge_base_document(
        self,
        document_data: Dict[str, Any],
        text_embedding: Optional[List[float]] = None,
        image_embedding: Optional[List[float]] = None,
        metadata: Optional[KnowledgeBaseMetadata] = None
    ) -> str:
        """
        Store knowledge base document in Qdrant with multi-vector embeddings
        
        Args:
            document_data: Document content and data
            text_embedding: Optional text embedding vector
            image_embedding: Optional image embedding vector
            metadata: Optional knowledge base metadata
            
        Returns:
            Point ID of stored document
        """
        # Generate unique ID
        point_id = str(uuid.uuid4())
        
        # Prepare metadata
        if not metadata:
            metadata = KnowledgeBaseMetadata(
                title=document_data.get("title", ""),
                source=document_data.get("source", ""),
                domain=document_data.get("domain"),
                year=document_data.get("year"),
                embedding_type=EmbeddingType.MULTIMODAL if (text_embedding and image_embedding) else EmbeddingType.TEXT,
                access_type=AccessType.OPEN,
                provenance_url=document_data.get("provenance_url"),
                version=document_data.get("version"),
                author=document_data.get("author"),
                chunk_index=document_data.get("chunk_index"),
                chunk_total=document_data.get("chunk_total"),
            )
        
        # Create schema
        schema = KnowledgeBaseSchema(
            id=point_id,
            text_embedding=text_embedding,
            image_embedding=image_embedding,
            payload=document_data,
            metadata=metadata
        )
        
        # Convert to Qdrant point
        point_dict = schema.to_qdrant_point()
        
        # Store in Qdrant
        try:
            # Handle multi-vector embeddings
            if isinstance(point_dict["vector"], dict):
                # Multi-vector: use named vectors
                point = PointStruct(
                    id=point_dict["id"],
                    vector=point_dict["vector"],
                    payload=point_dict["payload"]
                )
            else:
                # Single vector
                point = PointStruct(
                    id=point_dict["id"],
                    vector=point_dict["vector"],
                    payload=point_dict["payload"]
                )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Stored knowledge base document: {point_id}")
            return point_id
        except Exception as e:
            logger.error(f"Error storing knowledge base document: {e}")
            raise
    
    def store_multimodal_embedding(
        self,
        data: Dict[str, Any],
        text_embedding: List[float],
        image_embedding: Optional[List[float]] = None,
        metadata: Optional[StorageMetadata] = None
    ) -> str:
        """
        Store multi-vector embeddings (text + image) in Qdrant
        
        Args:
            data: Data payload
            text_embedding: Text embedding vector
            image_embedding: Optional image embedding vector
            metadata: Optional storage metadata
            
        Returns:
            Point ID of stored embedding
        """
        # Generate unique ID
        point_id = str(uuid.uuid4())
        
        # Prepare payload
        payload = data.copy()
        if metadata:
            payload.update(metadata.to_dict())
        
        # Store in Qdrant
        try:
            if image_embedding:
                # Multi-vector: use named vectors
                point = PointStruct(
                    id=point_id,
                    vector={
                        "text": text_embedding,
                        "image": image_embedding
                    },
                    payload=payload
                )
            else:
                # Single vector (text only)
                point = PointStruct(
                    id=point_id,
                    vector=text_embedding,
                    payload=payload
                )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Stored multi-modal embedding: {point_id}")
            return point_id
        except Exception as e:
            logger.error(f"Error storing multi-modal embedding: {e}")
            raise
    
    def search_with_filters(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        vector_name: Optional[str] = None  # For multi-vector: "text" or "image"
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with comprehensive filtering support
        
        Supports filtering by:
        - age, region, timestamp, comorbidity (for transcripts)
        - domain, year, source, access_type (for knowledge base)
        - Any custom payload fields
        
        Args:
            query_embedding: Query vector embedding
            filters: Dictionary of filter conditions
            limit: Number of results to return
            score_threshold: Minimum similarity score
            vector_name: Optional vector name for multi-vector search ("text" or "image")
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Build filter conditions
            qdrant_filter = None
            # Extract timestamp and patient_id filters separately - filter in Python
            # Timestamps are ISO strings and patient_id may not have an index
            timestamp_filter = None
            patient_id_filter = None
            filters_copy = filters.copy() if filters else {}
            if "timestamp" in filters_copy:
                timestamp_filter = filters_copy.pop("timestamp")
            if "patient_id" in filters_copy:
                patient_id_filter = filters_copy.pop("patient_id")
            filters = filters_copy
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    # Handle range filters (e.g., age, year) - NOT timestamp (handled separately)
                    if isinstance(value, dict):
                        if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                            # Range filter for numeric fields
                            range_filter = {}
                            for op in ["gte", "lte", "gt", "lt"]:
                                if op in value:
                                    val = value[op]
                                    # Convert to number if needed
                                    if isinstance(val, str):
                                        try:
                                            val = float(val)
                                        except (ValueError, TypeError):
                                            pass  # Keep original value
                                    range_filter[op] = val
                            conditions.append(
                                FieldCondition(key=key, range=Range(**range_filter))
                            )
                        elif "in" in value:
                            # In filter (for lists) - use MatchAny
                            conditions.append(
                                FieldCondition(key=key, match=MatchAny(any=value["in"]))
                            )
                    else:
                        # Exact match
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # Search with optional vector name for multi-vector
            # Get more results if we need to filter by timestamp or patient_id in Python
            needs_python_filtering = timestamp_filter or patient_id_filter
            search_params = {
                "collection_name": self.collection_name,
                "query_vector": (vector_name, query_embedding) if vector_name else query_embedding,
                "limit": limit * 2 if needs_python_filtering else limit,
                "score_threshold": score_threshold,
                "query_filter": qdrant_filter
            }
            
            results = self.client.search(**search_params)
            
            # Process results
            matching_documents = []
            for result in results:
                matching_documents.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                    "vector": result.vector if hasattr(result, 'vector') else None
                })
            
            # Apply timestamp filtering in Python (since timestamps are stored as ISO strings)
            if timestamp_filter and isinstance(timestamp_filter, dict):
                gte_time = timestamp_filter.get("gte")
                lte_time = timestamp_filter.get("lte")
                gt_time = timestamp_filter.get("gt")
                lt_time = timestamp_filter.get("lt")
                
                # Convert ISO strings or datetime objects to datetime for comparison
                def parse_time(val):
                    if isinstance(val, str):
                        try:
                            return datetime.fromisoformat(val.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            return None
                    elif isinstance(val, datetime):
                        return val
                    elif isinstance(val, (int, float)):
                        return datetime.fromtimestamp(val, tz=timezone.utc)
                    return None
                
                gte_dt = parse_time(gte_time)
                lte_dt = parse_time(lte_time)
                gt_dt = parse_time(gt_time)
                lt_dt = parse_time(lt_time)
                
                if gte_dt or lte_dt or gt_dt or lt_dt:
                    filtered_documents = []
                    for doc in matching_documents:
                        payload = doc.get("payload", {})
                        timestamp_str = payload.get("timestamp")
                        if timestamp_str:
                            try:
                                # Parse timestamp from payload
                                if isinstance(timestamp_str, str):
                                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                elif isinstance(timestamp_str, (int, float)):
                                    timestamp = datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
                                else:
                                    continue
                                
                                # Check if timestamp matches filter criteria
                                matches = True
                                if gte_dt and timestamp < gte_dt:
                                    matches = False
                                if lte_dt and timestamp > lte_dt:
                                    matches = False
                                if gt_dt and timestamp <= gt_dt:
                                    matches = False
                                if lt_dt and timestamp >= lt_dt:
                                    matches = False
                                
                                if matches:
                                    filtered_documents.append(doc)
                            except Exception as e:
                                logger.debug(f"Error parsing timestamp {timestamp_str}: {e}")
                                continue
                        else:
                            # If no timestamp, exclude from results when timestamp filter is active
                            pass
                    
                    matching_documents = filtered_documents
            
            # Apply patient_id filtering in Python (since it may not have an index)
            if patient_id_filter:
                filtered_documents = []
                for doc in matching_documents:
                    payload = doc.get("payload", {})
                    # Check patient_id in multiple possible locations
                    payload_patient_id = payload.get("patient_id")
                    
                    # Check in case_metadata dict
                    metadata_patient_id = None
                    case_metadata = payload.get("case_metadata")
                    if isinstance(case_metadata, dict):
                        metadata_patient_id = case_metadata.get("patient_id")
                    
                    # Check in case_data dict
                    case_data_patient_id = None
                    case_data = payload.get("case_data")
                    if isinstance(case_data, dict):
                        case_data_patient_id = case_data.get("patient_id")
                    
                    # Also check if patient_id is in the case_id
                    case_id_contains_patient = False
                    case_id = payload.get("case_id") or str(doc.get("id", ""))
                    if patient_id_filter in case_id:
                        case_id_contains_patient = True
                    
                    # Match if any of these match
                    if (payload_patient_id == patient_id_filter or 
                        metadata_patient_id == patient_id_filter or 
                        case_data_patient_id == patient_id_filter or
                        case_id_contains_patient):
                        filtered_documents.append(doc)
                
                logger.info(f"Filtered {len(filtered_documents)} documents for patient_id: {patient_id_filter} (from {len(matching_documents)} total)")
                matching_documents = filtered_documents[:limit]  # Apply limit after filtering
            
            logger.info(f"Found {len(matching_documents)} matching documents")
            return matching_documents
            
        except Exception as e:
            logger.error(f"Error searching with filters: {e}")
            raise
    
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        keyword_filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic similarity and keyword filtering
        
        Args:
            query_text: Query text for keyword matching
            query_embedding: Query vector embedding for semantic search
            keyword_filters: Optional keyword-based filters
            limit: Number of results to return
            score_threshold: Minimum similarity score
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            
        Returns:
            List of matching documents with combined scores
        """
        try:
            # Semantic search
            semantic_results = self.search_with_filters(
                query_embedding=query_embedding,
                filters=keyword_filters,
                limit=limit * 2,  # Get more results for re-ranking
                score_threshold=score_threshold
            )
            
            # Keyword matching (simple text matching in payload)
            keyword_matches = {}
            if query_text:
                query_words = set(query_text.lower().split())
                for result in semantic_results:
                    payload_text = str(result.get("payload", {})).lower()
                    match_count = sum(1 for word in query_words if word in payload_text)
                    keyword_score = match_count / len(query_words) if query_words else 0
                    keyword_matches[result["id"]] = keyword_score
            
            # Combine scores
            combined_results = []
            for result in semantic_results:
                semantic_score = result.get("score", 0.0)
                keyword_score = keyword_matches.get(result["id"], 0.0)
                combined_score = (semantic_weight * semantic_score) + (keyword_weight * keyword_score)
                
                combined_results.append({
                    **result,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score,
                    "combined_score": combined_score
                })
            
            # Sort by combined score and limit
            combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
            combined_results = combined_results[:limit]
            
            logger.info(f"Hybrid search found {len(combined_results)} results")
            return combined_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise


class TranscriptStorage:
    """
    High-level transcript storage interface
    
    Provides simplified API for storing and retrieving transcripts
    """
    
    def __init__(
        self,
        qdrant_storage: Optional[QdrantStorage] = None,
        embedding_model: Optional[Any] = None  # Will be integrated with embedding model later
    ):
        """
        Initialize transcript storage
        
        Args:
            qdrant_storage: Optional QdrantStorage instance
            embedding_model: Optional embedding model for generating vectors
        """
        self.qdrant_storage = qdrant_storage or QdrantStorage()
        self.embedding_model = embedding_model
        logger.info("Transcript storage initialized")
    
    def store(
        self,
        transcript_data: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store transcript
        
        Args:
            transcript_data: Processed transcript data
            embedding: Optional embedding vector (if None, will be generated)
            
        Returns:
            Point ID of stored transcript
        """
        # Generate embedding if not provided
        if embedding is None:
            if self.embedding_model:
                # Use embedding model to generate vector
                text = transcript_data.get("transcript", "")
                embedding = self.embedding_model.encode(text)
            else:
                # Placeholder: use zero vector (will be replaced with actual embedding)
                embedding = [0.0] * self.qdrant_storage.vector_size
                logger.warning("No embedding model provided. Using zero vector.")
        
        return self.qdrant_storage.store_transcript(transcript_data, embedding)
    
    def search(
        self,
        query_text: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar transcripts
        
        Args:
            query_text: Query text
            limit: Number of results
            filters: Optional filters
            
        Returns:
            List of similar transcripts
        """
        # Generate query embedding
        if self.embedding_model:
            query_embedding = self.embedding_model.encode(query_text)
        else:
            # Placeholder: use zero vector
            query_embedding = [0.0] * self.qdrant_storage.vector_size
            logger.warning("No embedding model provided. Using zero vector for search.")
        
        return self.qdrant_storage.search_similar(query_embedding, limit=limit, filters=filters)
    
    def get(self, point_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transcript by ID
        
        Args:
            point_id: Point ID
            
        Returns:
            Transcript data or None
        """
        return self.qdrant_storage.get_transcript(point_id)
    
    def delete(self, point_id: str) -> bool:
        """
        Delete transcript by ID
        
        Args:
            point_id: Point ID
            
        Returns:
            True if deleted
        """
        return self.qdrant_storage.delete_transcript(point_id)

