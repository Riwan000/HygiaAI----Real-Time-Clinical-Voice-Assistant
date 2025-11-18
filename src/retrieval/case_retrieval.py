"""
Clinical Case Retrieval Module

Provides high-level interface for retrieving similar clinical cases from Qdrant.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from src.storage import QdrantStorage
from src.models import Case, CaseMetadata

# Lazy import embeddings to avoid blocking if transformers/torch have version issues
# Use TYPE_CHECKING for type hints to avoid runtime imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.embeddings import BioBERTEmbeddingGenerator, CLIPEmbeddingGenerator, MultimodalEmbeddingGenerator
else:
    # Runtime: use lazy imports
    BioBERTEmbeddingGenerator = None
    CLIPEmbeddingGenerator = None
    MultimodalEmbeddingGenerator = None

def _get_biobert_embedding_generator():
    """Lazy import BioBERTEmbeddingGenerator"""
    global BioBERTEmbeddingGenerator
    if BioBERTEmbeddingGenerator is None:
        from src.embeddings import BioBERTEmbeddingGenerator
    return BioBERTEmbeddingGenerator

def _get_clip_embedding_generator():
    """Lazy import CLIPEmbeddingGenerator"""
    global CLIPEmbeddingGenerator
    if CLIPEmbeddingGenerator is None:
        from src.embeddings import CLIPEmbeddingGenerator
    return CLIPEmbeddingGenerator

def _get_multimodal_embedding_generator():
    """Lazy import MultimodalEmbeddingGenerator"""
    global MultimodalEmbeddingGenerator
    if MultimodalEmbeddingGenerator is None:
        from src.embeddings import MultimodalEmbeddingGenerator
    return MultimodalEmbeddingGenerator

logger = logging.getLogger(__name__)


class RetrievalMode(Enum):
    """Retrieval modes"""
    SEMANTIC = "semantic"  # Pure semantic similarity
    KEYWORD = "keyword"  # Pure keyword/filter-based
    HYBRID = "hybrid"  # Combined semantic + keyword


@dataclass
class RetrievalOptions:
    """Options for case retrieval"""
    limit: int = 5
    score_threshold: Optional[float] = None
    mode: RetrievalMode = RetrievalMode.HYBRID
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    
    # Filter options
    patient_id: Optional[str] = None
    age_group: Optional[str] = None
    age_range: Optional[Dict[str, int]] = None  # {"gte": 30, "lte": 50}
    region: Optional[str] = None
    comorbidities: Optional[List[str]] = None
    diagnosis: Optional[str] = None
    time_range: Optional[Dict[str, datetime]] = None  # {"gte": datetime, "lte": datetime}
    
    # Modality filters
    require_text: bool = False
    require_image: bool = False
    require_audio: bool = False
    
    # Entity filters
    entity_types: Optional[List[str]] = None  # ["symptom", "diagnosis", "medication"]
    entity_values: Optional[List[str]] = None  # ["fever", "cough"]
    
    # Knowledge base filters
    domain: Optional[str] = None
    source: Optional[str] = None
    year_range: Optional[Dict[str, int]] = None
    
    def to_filters(self) -> Dict[str, Any]:
        """Convert options to Qdrant filter dictionary"""
        filters = {}
        
        # Patient ID filter
        if self.patient_id:
            filters["patient_id"] = self.patient_id
        
        # Age filters
        if self.age_group:
            filters["age_group"] = self.age_group
        if self.age_range:
            filters["age"] = self.age_range
        
        # Region filter
        if self.region:
            filters["region"] = self.region
        
        # Comorbidities filter
        if self.comorbidities:
            filters["comorbidities"] = {"in": self.comorbidities}
        
        # Diagnosis filter
        if self.diagnosis:
            filters["diagnosis"] = self.diagnosis
        
        # Time range filter
        if self.time_range:
            if "gte" in self.time_range:
                filters["timestamp"] = {"gte": self.time_range["gte"].isoformat()}
            if "lte" in self.time_range:
                if "timestamp" in filters:
                    filters["timestamp"]["lte"] = self.time_range["lte"].isoformat()
                else:
                    filters["timestamp"] = {"lte": self.time_range["lte"].isoformat()}
        
        # Entity filters
        if self.entity_types:
            filters["medical_entities.entity_type"] = {"in": self.entity_types}
        if self.entity_values:
            filters["medical_entities.text"] = {"in": self.entity_values}
        
        # Knowledge base filters
        if self.domain:
            filters["domain"] = self.domain
        if self.source:
            filters["source"] = self.source
        if self.year_range:
            filters["year"] = self.year_range
        
        return filters


@dataclass
class RetrievalResult:
    """Result from case retrieval"""
    case_id: str
    score: float
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    combined_score: Optional[float] = None
    case_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[CaseMetadata] = None
    modalities: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "case_id": self.case_id,
            "score": self.score,
            "semantic_score": self.semantic_score,
            "keyword_score": self.keyword_score,
            "combined_score": self.combined_score,
            "case_data": self.case_data,
            "metadata": self.metadata.model_dump() if self.metadata else None,
            "modalities": self.modalities
        }


class CaseRetriever:
    """
    High-level interface for retrieving similar clinical cases from Qdrant
    
    Features:
    - Semantic search using embeddings
    - Keyword-based search with filters
    - Hybrid search (semantic + keyword)
    - Case ranking and filtering
    - Multi-modal case retrieval
    """
    
    def __init__(
        self,
        qdrant_storage: QdrantStorage,
        text_embedding_generator: Optional[BioBERTEmbeddingGenerator] = None,
        image_embedding_generator: Optional[CLIPEmbeddingGenerator] = None,
        multimodal_embedding_generator: Optional[MultimodalEmbeddingGenerator] = None
    ):
        """
        Initialize case retriever
        
        Args:
            qdrant_storage: QdrantStorage instance
            text_embedding_generator: Optional text embedding generator
            image_embedding_generator: Optional image embedding generator
            multimodal_embedding_generator: Optional multimodal embedding generator
        """
        self.storage = qdrant_storage
        # Use lazy imports to avoid blocking startup if transformers/torch have issues
        self.text_embedding_generator = text_embedding_generator or _get_biobert_embedding_generator()()
        self.image_embedding_generator = image_embedding_generator or _get_clip_embedding_generator()()
        self.multimodal_embedding_generator = multimodal_embedding_generator or _get_multimodal_embedding_generator()()
        
        logger.info("Case retriever initialized")
    
    def retrieve_similar_cases(
        self,
        query_text: Optional[str] = None,
        query_image_path: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        options: Optional[RetrievalOptions] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve similar clinical cases based on query
        
        Args:
            query_text: Optional query text
            query_image_path: Optional query image path
            query_embedding: Optional pre-computed query embedding
            options: Optional retrieval options
            
        Returns:
            List of retrieval results with similar cases
        """
        options = options or RetrievalOptions()
        
        # Convert options to filters
        filters = options.to_filters()
        
        # Optimize: Use scroll API when query is empty (with or without filters)
        # This is much faster than semantic search with dummy embeddings
        if not query_text and not query_image_path and not query_embedding:
            if filters:
                results = self._scroll_with_filters(filters, options)
            else:
                # No filters and no query - use scroll to get all cases
                results = self._scroll_with_filters({}, options)
        else:
            # Generate query embedding if not provided
            if query_embedding is None:
                if query_text and query_image_path:
                    # Multi-modal query
                    multimodal_result = self.multimodal_embedding_generator.generate_multimodal_embedding(
                        text=query_text,
                        image_path=query_image_path
                    )
                    query_embedding = multimodal_result.get("multimodal_embedding")
                elif query_text:
                    # Text-only query
                    query_embedding = self.text_embedding_generator.generate_embedding(query_text)
                elif query_image_path:
                    # Image-only query
                    query_embedding = self.image_embedding_generator.generate_embedding(query_image_path)
                else:
                    raise ValueError("Must provide query_text, query_image_path, or query_embedding")
            
            # Perform retrieval based on mode
            if options.mode == RetrievalMode.SEMANTIC:
                results = self._semantic_search(query_embedding, filters, options)
            elif options.mode == RetrievalMode.KEYWORD:
                results = self._keyword_search(filters, options)
            else:  # HYBRID
                results = self._hybrid_search(query_text or "", query_embedding, filters, options)
        
        # Format results
        formatted_results = self._format_results(results, options)
        
        logger.info(f"Retrieved {len(formatted_results)} similar cases")
        return formatted_results
    
    def _semantic_search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        options: RetrievalOptions
    ) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        results = self.storage.search_with_filters(
            query_embedding=query_embedding,
            filters=filters if filters else None,
            limit=options.limit,
            score_threshold=options.score_threshold
        )
        return results
    
    def _keyword_search(
        self,
        filters: Dict[str, Any],
        options: RetrievalOptions
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based search"""
        # Use dummy embedding for keyword-only search
        dummy_embedding = [0.0] * self.storage.vector_size
        results = self.storage.search_with_filters(
            query_embedding=dummy_embedding,
            filters=filters if filters else None,
            limit=options.limit,
            score_threshold=options.score_threshold
        )
        return results
    
    def _scroll_with_filters(
        self,
        filters: Dict[str, Any],
        options: RetrievalOptions
    ) -> List[Dict[str, Any]]:
        """Use Qdrant scroll API with filters for efficient retrieval when no query text"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
            from datetime import datetime, timezone
            
            # Extract timestamp and patient_id filters separately - we'll filter in Python
            # Timestamps are ISO strings and patient_id may not have an index
            timestamp_filter = None
            patient_id_filter = None
            filters_copy = filters.copy() if filters else {}
            if "timestamp" in filters_copy:
                timestamp_filter = filters_copy.pop("timestamp")
            if "patient_id" in filters_copy:
                patient_id_filter = filters_copy.pop("patient_id")
            filters = filters_copy
            
            # Build Qdrant filter from remaining filters (excluding timestamp)
            qdrant_filter = None
            conditions = []
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict):
                        # Range filter (for non-timestamp fields)
                        if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                            conditions.append(
                                FieldCondition(key=key, range=Range(**value))
                            )
                        elif "in" in value:
                            # In filter (for lists)
                            from qdrant_client.models import MatchAny
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
            
            # Use scroll API with filters (excluding timestamp and patient_id)
            # If no filters, scroll will return all cases
            scroll_result = self.storage.client.scroll(
                collection_name=self.storage.collection_name,
                scroll_filter=qdrant_filter if qdrant_filter else None,
                limit=min(options.limit, 1000),  # Cap at 1000 for performance
                with_payload=True,
                with_vectors=False
            )
            
            # Convert scroll results to search result format
            results = []
            for point in scroll_result[0]:  # scroll_result is (points, next_page_offset)
                results.append({
                    "id": point.id,
                    "score": None,  # No similarity score for scroll (no query to compare against)
                    "payload": point.payload or {}
                })
            
            # Apply time range filtering in Python (since timestamps are stored as ISO strings)
            if timestamp_filter and isinstance(timestamp_filter, dict):
                gte_time = timestamp_filter.get("gte")
                lte_time = timestamp_filter.get("lte")
                
                # Convert ISO strings or datetime objects to datetime for comparison
                if isinstance(gte_time, str):
                    try:
                        gte_time = datetime.fromisoformat(gte_time.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        gte_time = None
                elif isinstance(gte_time, datetime):
                    pass  # Already datetime
                else:
                    gte_time = None
                
                if isinstance(lte_time, str):
                    try:
                        lte_time = datetime.fromisoformat(lte_time.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        lte_time = None
                elif isinstance(lte_time, datetime):
                    pass  # Already datetime
                else:
                    lte_time = None
                
                if gte_time or lte_time:
                    filtered_results = []
                    for result in results:
                        payload = result.get("payload", {})
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
                                
                                # Check if timestamp is within range
                                matches = True
                                if gte_time and timestamp < gte_time:
                                    matches = False
                                if lte_time and timestamp > lte_time:
                                    matches = False
                                
                                if matches:
                                    filtered_results.append(result)
                            except Exception as e:
                                logger.debug(f"Error parsing timestamp {timestamp_str}: {e}")
                                continue
                    
                    results = filtered_results
            
            # Apply patient_id filtering in Python (since it may not have an index)
            if patient_id_filter:
                filtered_results = []
                # Normalize filter value (trim and lowercase for comparison)
                filter_value = str(patient_id_filter).strip().lower()
                
                for result in results:
                    payload = result.get("payload", {})
                    matched = False
                    
                    # Check patient_id in multiple possible locations (case-insensitive, trimmed)
                    locations_to_check = [
                        payload.get("patient_id"),
                        payload.get("case_metadata", {}).get("patient_id") if isinstance(payload.get("case_metadata"), dict) else None,
                        payload.get("case_data", {}).get("patient_id") if isinstance(payload.get("case_data"), dict) else None,
                    ]
                    
                    # Also check if patient_id is in the case_id (some cases have patient_id in case_id)
                    case_id = str(payload.get("case_id") or result.get("id", "")).lower()
                    if filter_value in case_id:
                        matched = True
                    
                    # Check all locations
                    for location_value in locations_to_check:
                        if location_value:
                            location_str = str(location_value).strip().lower()
                            if location_str == filter_value:
                                matched = True
                                break
                    
                    if matched:
                        filtered_results.append(result)
                
                logger.info(f"Filtered {len(filtered_results)} cases for patient_id: {patient_id_filter} (from {len(results)} total)")
                if filtered_results:
                    sample_ids = [str(r.get("payload", {}).get("patient_id", "N/A"))[:20] for r in filtered_results[:3]]
                    logger.debug(f"Sample patient_ids found: {sample_ids}")
                results = filtered_results[:options.limit]
            
            logger.info(f"Scrolled {len(results)} cases with filters")
            return results
            
        except Exception as e:
            logger.warning(f"Error using scroll API, falling back to keyword search: {e}")
            # Fallback to keyword search (which also filters timestamps in Python)
            return self._keyword_search(filters, options)
    
    def _hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        filters: Dict[str, Any],
        options: RetrievalOptions
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search (semantic + keyword)"""
        results = self.storage.hybrid_search(
            query_text=query_text,
            query_embedding=query_embedding,
            keyword_filters=filters if filters else None,
            limit=options.limit,
            score_threshold=options.score_threshold,
            semantic_weight=options.semantic_weight,
            keyword_weight=options.keyword_weight
        )
        return results
    
    def _format_results(
        self,
        results: List[Dict[str, Any]],
        options: RetrievalOptions
    ) -> List[RetrievalResult]:
        """Format raw results into RetrievalResult objects"""
        formatted = []
        
        for result in results:
            payload = result.get("payload", {})
            
            # Extract metadata
            metadata = None
            try:
                metadata = CaseMetadata(
                    timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.now().isoformat())),
                    age_group=payload.get("age_group"),
                    region=payload.get("region"),
                    comorbidities=payload.get("comorbidities", []),
                    diagnosis=payload.get("diagnosis"),
                    outcome=payload.get("outcome")
                )
            except Exception as e:
                logger.warning(f"Error parsing metadata: {e}")
            
            # Extract modalities
            modalities = {}
            if payload.get("transcript"):
                # Check for SOAP note in multiple possible locations
                soap_note = payload.get("soap_note") or payload.get("soap_notes")
                modalities["text"] = {
                    "transcript": payload.get("transcript"),
                    "entities": payload.get("medical_entities", []),
                    "soap": soap_note
                }
            if payload.get("image_path"):
                modalities["image"] = {
                    "image_path": payload.get("image_path"),
                    "image_type": payload.get("image_type")
                }
            if payload.get("audio_path"):
                modalities["audio"] = {
                    "audio_path": payload.get("audio_path"),
                    "audio_type": payload.get("audio_type")
                }
            
            # Create retrieval result
            # Handle None scores (from scroll API when no query)
            raw_score = result.get("score")
            score = raw_score if raw_score is not None else 0.0
            
            retrieval_result = RetrievalResult(
                case_id=result.get("id", ""),
                score=score,
                semantic_score=result.get("semantic_score"),
                keyword_score=result.get("keyword_score"),
                combined_score=result.get("combined_score"),
                case_data=payload,
                metadata=metadata,
                modalities=modalities
            )
            
            formatted.append(retrieval_result)
        
        return formatted
    
    def retrieve_by_entity_type(
        self,
        entity_type: str,
        entity_value: Optional[str] = None,
        options: Optional[RetrievalOptions] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve cases by entity type (e.g., symptom, diagnosis)
        
        Args:
            entity_type: Type of medical entity (symptom, diagnosis, medication, etc.)
            entity_value: Optional specific entity value
            options: Optional retrieval options
            
        Returns:
            List of retrieval results
        """
        options = options or RetrievalOptions()
        
        # Build filters
        filters = options.to_filters()
        filters["medical_entities.entity_type"] = entity_type
        if entity_value:
            filters["medical_entities.text"] = entity_value
        
        # Perform search
        dummy_embedding = [0.0] * self.storage.vector_size
        results = self.storage.search_with_filters(
            query_embedding=dummy_embedding,
            filters=filters,
            limit=options.limit,
            score_threshold=options.score_threshold
        )
        
        return self._format_results(results, options)
    
    def retrieve_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        query_text: Optional[str] = None,
        options: Optional[RetrievalOptions] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve cases within a time range
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            query_text: Optional query text for semantic search
            options: Optional retrieval options
            
        Returns:
            List of retrieval results
        """
        options = options or RetrievalOptions()
        options.time_range = {"gte": start_time, "lte": end_time}
        
        # Generate query embedding if text provided
        query_embedding = None
        if query_text:
            query_embedding = self.text_embedding_generator.generate_embedding(query_text)
        
        return self.retrieve_similar_cases(
            query_text=query_text,
            query_embedding=query_embedding,
            options=options
        )
    
    def retrieve_by_demographics(
        self,
        age_group: Optional[str] = None,
        age_range: Optional[Dict[str, int]] = None,
        region: Optional[str] = None,
        comorbidities: Optional[List[str]] = None,
        query_text: Optional[str] = None,
        options: Optional[RetrievalOptions] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve cases by demographic filters
        
        Args:
            age_group: Optional age group (pediatric, adult, elderly)
            age_range: Optional age range ({"gte": 30, "lte": 50})
            region: Optional region/clinic ID
            comorbidities: Optional list of comorbidities
            query_text: Optional query text for semantic search
            options: Optional retrieval options
            
        Returns:
            List of retrieval results
        """
        options = options or RetrievalOptions()
        options.age_group = age_group
        options.age_range = age_range
        options.region = region
        options.comorbidities = comorbidities
        
        # Generate query embedding if text provided
        query_embedding = None
        if query_text:
            query_embedding = self.text_embedding_generator.generate_embedding(query_text)
        
        return self.retrieve_similar_cases(
            query_text=query_text,
            query_embedding=query_embedding,
            options=options
        )

