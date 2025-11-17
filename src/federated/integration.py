"""
Federated Architecture Integration

Integrates federated learning architecture with existing HygiaAI components:
- QdrantStorage integration
- API layer integration
- Clinical memory system integration
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.storage.qdrant_storage import QdrantStorage
from src.embeddings import BioBERTEmbeddingGenerator
from .coordinator import FederatedCoordinator, AggregationConfig
from .client import FederatedClient, ClientConfig
from .sync import FederatedSync, SyncConfig
from .secure_aggregator import AggregationMethod, PrivacyLevel

logger = logging.getLogger(__name__)


class FederatedMemoryIntegration:
    """
    Integration layer for federated memory architecture
    
    Connects federated learning components with existing HygiaAI infrastructure.
    """
    
    def __init__(
        self,
        qdrant_storage: QdrantStorage,
        coordinator_url: Optional[str] = None,
        client_id: Optional[str] = None,
        enable_federated: bool = True,
        aggregation_config: Optional[AggregationConfig] = None
    ):
        """
        Initialize federated memory integration
        
        Args:
            qdrant_storage: Local QdrantStorage instance
            coordinator_url: Optional coordinator URL (if acting as client)
            client_id: Optional client ID (if acting as client)
            enable_federated: Enable federated learning features
            aggregation_config: Optional aggregation configuration
        """
        self.qdrant_storage = qdrant_storage
        self.enable_federated = enable_federated
        
        if enable_federated:
            # Initialize coordinator (if acting as server)
            self.coordinator = FederatedCoordinator(
                aggregation_config=aggregation_config or AggregationConfig(
                    method=AggregationMethod.FEDERATED_AVERAGING,
                    privacy_level=PrivacyLevel.ENHANCED
                )
            )
            
            # Initialize client (if acting as client)
            if coordinator_url and client_id:
                self.client = FederatedClient(
                    client_id=client_id,
                    coordinator_url=coordinator_url
                )
                self.sync = FederatedSync(
                    client_id=client_id,
                    local_storage=qdrant_storage,
                    coordinator=self.coordinator
                )
            else:
                self.client = None
                self.sync = None
            
            logger.info("Federated memory integration initialized")
        else:
            self.coordinator = None
            self.client = None
            self.sync = None
            logger.info("Federated learning disabled")
    
    def collect_local_embeddings(
        self,
        collection_name: str = "hygiaai_transcripts",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect embeddings from local Qdrant for federated learning
        
        Args:
            collection_name: Collection to collect from
            limit: Optional limit on number of embeddings
            
        Returns:
            List of embedding data
        """
        try:
            # Scroll through collection to get embeddings
            result = self.qdrant_storage.client.scroll(
                collection_name=collection_name,
                limit=limit or 1000
            )
            
            embeddings = []
            for point in result[0]:
                # Handle both single vector and named vectors
                if isinstance(point.vector, list):
                    embedding = point.vector
                elif isinstance(point.vector, dict):
                    embedding = point.vector.get("text", [])
                else:
                    embedding = []
                
                embeddings.append({
                    "id": point.id,
                    "embedding": embedding,
                    "metadata": point.payload or {}
                })
            
            logger.info(f"Collected {len(embeddings)} embeddings from {collection_name}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error collecting local embeddings: {e}")
            return []
    
    def participate_in_federated_round(
        self,
        round_id: str
    ) -> bool:
        """
        Participate in a federated learning round
        
        Args:
            round_id: Aggregation round ID
            
        Returns:
            True if participation successful
        """
        if not self.enable_federated or not self.client:
            logger.warning("Federated learning not enabled or client not initialized")
            return False
        
        try:
            # Collect local embeddings
            embeddings = self.collect_local_embeddings()
            
            if not embeddings:
                logger.warning("No local embeddings to contribute")
                return False
            
            # Prepare aggregated embedding
            prepared = self.client.prepare_aggregated_embedding()
            if not prepared:
                return False
            
            # Submit to round
            success = self.client.submit_to_round(
                round_id=round_id,
                embedding=prepared["embedding"],
                weight=prepared["weight"],
                statistics=prepared["statistics"]
            )
            
            if success:
                logger.info(f"Successfully participated in round {round_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error participating in federated round: {e}")
            return False
    
    def start_federated_round(
        self,
        min_clients: int = 2
    ) -> Optional[str]:
        """
        Start a new federated learning round (as coordinator)
        
        Args:
            min_clients: Minimum clients required
            
        Returns:
            Round ID if successful
        """
        if not self.enable_federated or not self.coordinator:
            logger.warning("Federated learning not enabled or coordinator not initialized")
            return None
        
        try:
            round_id = self.coordinator.start_aggregation_round(min_clients=min_clients)
            logger.info(f"Started federated round {round_id}")
            return round_id
        except Exception as e:
            logger.error(f"Error starting federated round: {e}")
            return None
    
    def aggregate_round(self, round_id: str) -> Optional[Dict[str, Any]]:
        """
        Aggregate a federated learning round (as coordinator)
        
        Args:
            round_id: Round ID to aggregate
            
        Returns:
            Aggregation result if successful
        """
        if not self.enable_federated or not self.coordinator:
            logger.warning("Federated learning not enabled or coordinator not initialized")
            return None
        
        try:
            result = self.coordinator.aggregate_round(round_id)
            
            if result.success:
                logger.info(f"Round {round_id} aggregated successfully")
                
                # Optionally store aggregated embedding in local Qdrant
                if result.aggregated_embedding:
                    self._store_aggregated_embedding(
                        result.aggregated_embedding,
                        result.aggregated_statistics
                    )
                
                return {
                    "round_id": result.round_id,
                    "success": True,
                    "aggregated_embedding": result.aggregated_embedding,
                    "aggregated_statistics": result.aggregated_statistics,
                    "participating_clients": result.participating_clients
                }
            else:
                logger.error(f"Round {round_id} aggregation failed: {result.error}")
                return {
                    "round_id": result.round_id,
                    "success": False,
                    "error": result.error
                }
                
        except Exception as e:
            logger.error(f"Error aggregating round: {e}")
            return None
    
    def _store_aggregated_embedding(
        self,
        embedding: List[float],
        statistics: Optional[Dict[str, Any]] = None
    ):
        """Store aggregated embedding in local Qdrant"""
        try:
            from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
            
            metadata = KnowledgeBaseMetadata(
                title="Federated Global Model",
                source="federated_aggregation",
                domain="federated_learning",
                year=datetime.now(timezone.utc).year,
                embedding_type=EmbeddingType.TEXT,
                access_type=AccessType.OPEN,
                provenance_url="https://hygiaai.internal/federated/global",
                author="FederatedCoordinator",
                version="1.0"
            )
            
            self.qdrant_storage.store_knowledge_base_document(
                document_data={
                    "text": "Federated aggregated embedding",
                    "aggregated": True,
                    "statistics": statistics or {}
                },
                text_embedding=embedding,
                metadata=metadata
            )
            
            logger.info("Stored aggregated embedding in local Qdrant")
            
        except Exception as e:
            logger.error(f"Error storing aggregated embedding: {e}")
    
    def sync_with_global_model(self) -> bool:
        """
        Synchronize with global federated model
        
        Returns:
            True if sync successful
        """
        if not self.enable_federated or not self.sync:
            logger.warning("Federated sync not available")
            return False
        
        try:
            result = self.sync.sync_to_global()
            return result.success
        except Exception as e:
            logger.error(f"Error syncing with global model: {e}")
            return False
    
    def get_federated_statistics(self) -> Dict[str, Any]:
        """Get federated learning statistics"""
        stats = {
            "enabled": self.enable_federated
        }
        
        if self.enable_federated:
            if self.coordinator:
                stats["coordinator"] = self.coordinator.get_statistics()
            
            if self.client:
                stats["client"] = self.client.get_statistics()
            
            if self.sync:
                stats["sync"] = self.sync.get_statistics()
        
        return stats

