"""
Federated Client

Client-side component for participating in federated learning.
Each clinic runs a client that contributes embeddings to the global model.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ParticipationStatus(Enum):
    """Status of client participation"""
    IDLE = "idle"
    REGISTERED = "registered"
    COLLECTING = "collecting"
    SUBMITTED = "submitted"
    ERROR = "error"


@dataclass
class ClientConfig:
    """Configuration for federated client"""
    client_id: str
    coordinator_url: str
    auto_register: bool = True
    auto_submit: bool = True
    min_round_interval: int = 3600  # Minimum seconds between rounds
    max_embedding_age: int = 86400  # Maximum age of embeddings to submit (seconds)


class FederatedClient:
    """
    Federated learning client
    
    Represents a clinic participating in federated learning.
    Collects local embeddings and submits them to the coordinator.
    """
    
    def __init__(
        self,
        client_id: str,
        coordinator_url: str,
        config: Optional[ClientConfig] = None
    ):
        """
        Initialize federated client
        
        Args:
            client_id: Unique identifier for this client/clinic
            coordinator_url: URL of the federated coordinator
            config: Optional client configuration
        """
        self.client_id = client_id
        self.coordinator_url = coordinator_url
        self.config = config or ClientConfig(
            client_id=client_id,
            coordinator_url=coordinator_url
        )
        
        self.status = ParticipationStatus.IDLE
        self.registered = False
        self.current_round_id: Optional[str] = None
        self.local_embeddings: List[Dict[str, Any]] = []
        self.submission_history: List[Dict[str, Any]] = []
        
        logger.info(f"Federated client initialized: {client_id}")
    
    def register(self) -> bool:
        """
        Register with the coordinator
        
        Returns:
            True if registration successful
        """
        # In a real implementation, this would make an HTTP request to the coordinator
        # For now, we'll simulate it
        try:
            # TODO: Implement actual HTTP registration
            # response = requests.post(f"{self.coordinator_url}/register", json={"client_id": self.client_id})
            # self.registered = response.status_code == 200
            
            self.registered = True
            self.status = ParticipationStatus.REGISTERED
            logger.info(f"Client {self.client_id} registered with coordinator")
            return True
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            self.status = ParticipationStatus.ERROR
            return False
    
    def collect_local_embeddings(
        self,
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Collect local embeddings for submission
        
        Args:
            embeddings: List of embedding vectors
            metadata: Optional metadata for each embedding
            
        Returns:
            Number of embeddings collected
        """
        collected = 0
        current_time = datetime.now(timezone.utc)
        
        for i, embedding in enumerate(embeddings):
            embedding_data = {
                "embedding": embedding,
                "collected_at": current_time,
                "metadata": metadata[i] if metadata and i < len(metadata) else {}
            }
            self.local_embeddings.append(embedding_data)
            collected += 1
        
        logger.info(f"Collected {collected} local embeddings")
        return collected
    
    def prepare_aggregated_embedding(self) -> Optional[Dict[str, Any]]:
        """
        Prepare aggregated embedding from local embeddings
        
        Returns:
            Dictionary with aggregated embedding and statistics
        """
        if not self.local_embeddings:
            logger.warning("No local embeddings to aggregate")
            return None
        
        import numpy as np
        
        # Aggregate embeddings (simple average for now)
        embeddings = [emb["embedding"] for emb in self.local_embeddings]
        aggregated = np.mean(embeddings, axis=0).tolist()
        
        # Calculate statistics
        statistics = {
            "num_embeddings": len(embeddings),
            "embedding_dim": len(embeddings[0]) if embeddings else 0,
            "collection_timespan": self._calculate_timespan(),
            "metadata_summary": self._summarize_metadata()
        }
        
        # Calculate weight (based on number of embeddings)
        weight = len(embeddings)
        
        return {
            "embedding": aggregated,
            "weight": weight,
            "statistics": statistics
        }
    
    def submit_to_round(
        self,
        round_id: str,
        embedding: Optional[List[float]] = None,
        weight: Optional[float] = None,
        statistics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Submit embedding to an aggregation round
        
        Args:
            round_id: Aggregation round ID
            embedding: Optional embedding (will use aggregated if not provided)
            weight: Optional weight
            statistics: Optional statistics
            
        Returns:
            True if submission successful
        """
        if not self.registered:
            logger.error("Client not registered")
            return False
        
        try:
            # Prepare submission data
            if embedding is None:
                prepared = self.prepare_aggregated_embedding()
                if not prepared:
                    return False
                embedding = prepared["embedding"]
                weight = weight or prepared.get("weight")
                statistics = statistics or prepared.get("statistics")
            
            # In a real implementation, this would make an HTTP request
            # TODO: Implement actual HTTP submission
            # response = requests.post(
            #     f"{self.coordinator_url}/rounds/{round_id}/submit",
            #     json={
            #         "client_id": self.client_id,
            #         "embedding": embedding,
            #         "weight": weight,
            #         "statistics": statistics
            #     }
            # )
            # success = response.status_code == 200
            
            # For now, simulate success
            success = True
            
            if success:
                self.status = ParticipationStatus.SUBMITTED
                self.current_round_id = round_id
                self.submission_history.append({
                    "round_id": round_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "embedding_size": len(embedding) if embedding else 0
                })
                logger.info(f"Submitted embedding to round {round_id}")
            else:
                self.status = ParticipationStatus.ERROR
                logger.error(f"Submission to round {round_id} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Submission error: {e}")
            self.status = ParticipationStatus.ERROR
            return False
    
    def _calculate_timespan(self) -> Optional[float]:
        """Calculate timespan of collected embeddings"""
        if len(self.local_embeddings) < 2:
            return None
        
        times = [emb["collected_at"] for emb in self.local_embeddings]
        if isinstance(times[0], str):
            times = [datetime.fromisoformat(t) for t in times]
        
        timespan = (max(times) - min(times)).total_seconds()
        return timespan
    
    def _summarize_metadata(self) -> Dict[str, Any]:
        """Summarize metadata from collected embeddings"""
        if not self.local_embeddings:
            return {}
        
        # Collect all metadata keys
        all_keys = set()
        for emb in self.local_embeddings:
            all_keys.update(emb.get("metadata", {}).keys())
        
        summary = {}
        for key in all_keys:
            values = [emb.get("metadata", {}).get(key) for emb in self.local_embeddings]
            summary[key] = {
                "count": len([v for v in values if v is not None]),
                "unique_values": len(set([v for v in values if v is not None]))
            }
        
        return summary
    
    def clear_local_embeddings(self):
        """Clear collected local embeddings"""
        count = len(self.local_embeddings)
        self.local_embeddings.clear()
        logger.info(f"Cleared {count} local embeddings")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "client_id": self.client_id,
            "status": self.status.value,
            "registered": self.registered,
            "current_round": self.current_round_id,
            "local_embeddings": len(self.local_embeddings),
            "submissions": len(self.submission_history)
        }

