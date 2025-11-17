"""
Federated Coordinator

Central server component that coordinates federated learning rounds,
aggregates embeddings from multiple clinics, and manages the global model.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from .secure_aggregator import SecureAggregator, AggregationConfig, AggregationMethod, PrivacyLevel

logger = logging.getLogger(__name__)


class AggregationRoundStatus(Enum):
    """Status of an aggregation round"""
    PENDING = "pending"
    COLLECTING = "collecting"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AggregationRound:
    """Represents a single aggregation round"""
    round_id: str
    status: AggregationRoundStatus = AggregationRoundStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    min_clients: int = 2
    max_clients: Optional[int] = None
    participating_clients: Set[str] = field(default_factory=set)
    client_embeddings: Dict[str, List[float]] = field(default_factory=dict)
    client_weights: Dict[str, float] = field(default_factory=dict)
    client_statistics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    aggregated_embedding: Optional[List[float]] = None
    aggregated_statistics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class AggregationResult:
    """Result of an aggregation round"""
    round_id: str
    success: bool
    aggregated_embedding: Optional[List[float]] = None
    aggregated_statistics: Optional[Dict[str, Any]] = None
    participating_clients: List[str] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FederatedCoordinator:
    """
    Central coordinator for federated learning
    
    Manages aggregation rounds, collects embeddings from clients,
    and performs secure aggregation.
    """
    
    def __init__(
        self,
        aggregation_config: Optional[AggregationConfig] = None,
        min_clients: int = 2,
        max_clients: Optional[int] = None
    ):
        """
        Initialize federated coordinator
        
        Args:
            aggregation_config: Configuration for secure aggregation
            min_clients: Minimum number of clients required for aggregation
            max_clients: Maximum number of clients allowed (None for unlimited)
        """
        self.aggregator = SecureAggregator(aggregation_config)
        self.min_clients = min_clients
        self.max_clients = max_clients
        self.active_rounds: Dict[str, AggregationRound] = {}
        self.completed_rounds: List[AggregationRound] = []
        self.registered_clients: Set[str] = set()
        
        logger.info(f"Federated coordinator initialized (min_clients={min_clients}, max_clients={max_clients})")
    
    def start_aggregation_round(
        self,
        round_id: Optional[str] = None,
        min_clients: Optional[int] = None
    ) -> str:
        """
        Start a new aggregation round
        
        Args:
            round_id: Optional round ID (generated if not provided)
            min_clients: Optional minimum clients (uses default if not provided)
            
        Returns:
            Round ID
        """
        if round_id is None:
            round_id = str(uuid.uuid4())
        
        if round_id in self.active_rounds:
            raise ValueError(f"Aggregation round {round_id} already exists")
        
        round_min_clients = min_clients or self.min_clients
        
        aggregation_round = AggregationRound(
            round_id=round_id,
            status=AggregationRoundStatus.COLLECTING,
            min_clients=round_min_clients,
            max_clients=self.max_clients,
            started_at=datetime.now(timezone.utc)
        )
        
        self.active_rounds[round_id] = aggregation_round
        logger.info(f"Started aggregation round {round_id} (min_clients={round_min_clients})")
        
        return round_id
    
    def register_client(self, client_id: str) -> bool:
        """
        Register a client for participation
        
        Args:
            client_id: Unique client identifier
            
        Returns:
            True if registered successfully
        """
        if self.max_clients and len(self.registered_clients) >= self.max_clients:
            logger.warning(f"Maximum clients reached ({self.max_clients}), cannot register {client_id}")
            return False
        
        self.registered_clients.add(client_id)
        logger.info(f"Registered client: {client_id}")
        return True
    
    def submit_embedding(
        self,
        round_id: str,
        client_id: str,
        embedding: List[float],
        weight: Optional[float] = None,
        statistics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Submit embedding from a client
        
        Args:
            round_id: Aggregation round ID
            client_id: Client identifier
            embedding: Embedding vector
            weight: Optional weight for this client's contribution
            statistics: Optional statistics from this client
            
        Returns:
            True if submission accepted
        """
        if round_id not in self.active_rounds:
            logger.error(f"Aggregation round {round_id} not found")
            return False
        
        round = self.active_rounds[round_id]
        
        if round.status != AggregationRoundStatus.COLLECTING:
            logger.error(f"Round {round_id} is not accepting submissions (status: {round.status})")
            return False
        
        if round.max_clients and len(round.participating_clients) >= round.max_clients:
            logger.warning(f"Round {round_id} has reached maximum clients")
            return False
        
        # Add client to round
        round.participating_clients.add(client_id)
        round.client_embeddings[client_id] = embedding
        
        if weight is not None:
            round.client_weights[client_id] = weight
        
        if statistics:
            round.client_statistics[client_id] = statistics
        
        logger.info(f"Received embedding from client {client_id} for round {round_id} ({len(round.participating_clients)}/{round.min_clients} clients)")
        
        return True
    
    def aggregate_round(self, round_id: str) -> AggregationResult:
        """
        Perform aggregation for a round
        
        Args:
            round_id: Aggregation round ID
            
        Returns:
            Aggregation result
        """
        if round_id not in self.active_rounds:
            raise ValueError(f"Aggregation round {round_id} not found")
        
        round = self.active_rounds[round_id]
        
        if round.status != AggregationRoundStatus.COLLECTING:
            raise ValueError(f"Round {round_id} is not in collecting status")
        
        if len(round.participating_clients) < round.min_clients:
            error_msg = f"Insufficient clients: {len(round.participating_clients)} < {round.min_clients}"
            round.status = AggregationRoundStatus.FAILED
            round.error = error_msg
            logger.error(f"Round {round_id} failed: {error_msg}")
            return AggregationResult(
                round_id=round_id,
                success=False,
                error=error_msg
            )
        
        try:
            round.status = AggregationRoundStatus.AGGREGATING
            
            # Aggregate embeddings
            aggregated_embedding = self.aggregator.aggregate_embeddings(
                client_embeddings=round.client_embeddings,
                client_weights=round.client_weights if round.client_weights else None
            )
            
            # Aggregate statistics if available
            aggregated_statistics = None
            if round.client_statistics:
                aggregated_statistics = self.aggregator.aggregate_statistics(
                    round.client_statistics
                )
            
            round.aggregated_embedding = aggregated_embedding
            round.aggregated_statistics = aggregated_statistics
            round.status = AggregationRoundStatus.COMPLETED
            round.completed_at = datetime.now(timezone.utc)
            
            # Move to completed rounds
            self.completed_rounds.append(round)
            del self.active_rounds[round_id]
            
            logger.info(f"Round {round_id} completed successfully ({len(round.participating_clients)} clients)")
            
            return AggregationResult(
                round_id=round_id,
                success=True,
                aggregated_embedding=aggregated_embedding,
                aggregated_statistics=aggregated_statistics,
                participating_clients=list(round.participating_clients)
            )
            
        except Exception as e:
            error_msg = f"Aggregation failed: {str(e)}"
            round.status = AggregationRoundStatus.FAILED
            round.error = error_msg
            logger.error(f"Round {round_id} failed: {error_msg}")
            return AggregationResult(
                round_id=round_id,
                success=False,
                error=error_msg
            )
    
    def get_round_status(self, round_id: str) -> Optional[AggregationRound]:
        """Get status of an aggregation round"""
        if round_id in self.active_rounds:
            return self.active_rounds[round_id]
        
        # Check completed rounds
        for round in self.completed_rounds:
            if round.round_id == round_id:
                return round
        
        return None
    
    def list_active_rounds(self) -> List[str]:
        """List all active aggregation round IDs"""
        return list(self.active_rounds.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get coordinator statistics"""
        return {
            "registered_clients": len(self.registered_clients),
            "active_rounds": len(self.active_rounds),
            "completed_rounds": len(self.completed_rounds),
            "aggregation_method": self.aggregator.config.method.value,
            "privacy_level": self.aggregator.config.privacy_level.value
        }

