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
from src.embeddings import BioBERTEmbeddingGenerator, CLIPEmbeddingGenerator, MultimodalEmbeddingGenerator
from src.models import Case, CaseMetadata

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
        self.text_embedding_generator = text_embedding_generator or BioBERTEmbeddingGenerator()
        self.image_embedding_generator = image_embedding_generator or CLIPEmbeddingGenerator()
        self.multimodal_embedding_generator = multimodal_embedding_generator or MultimodalEmbeddingGenerator()
        
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
        
        # Convert options to filters
        filters = options.to_filters()
        
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
                modalities["text"] = {
                    "transcript": payload.get("transcript"),
                    "entities": payload.get("medical_entities", []),
                    "soap": payload.get("soap_notes")
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
            retrieval_result = RetrievalResult(
                case_id=result.get("id", ""),
                score=result.get("score", 0.0),
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

