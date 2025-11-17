"""
Secure Aggregation for Federated Learning

Implements privacy-preserving aggregation methods for combining embeddings
from multiple clinics without exposing individual clinic data.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AggregationMethod(Enum):
    """Aggregation methods for federated learning"""
    FEDERATED_AVERAGING = "fedavg"
    SECURE_AGGREGATION = "secure_agg"
    DIFFERENTIAL_PRIVACY = "dp"
    WEIGHTED_AVERAGING = "weighted_avg"
    MEDIAN_AGGREGATION = "median"


class PrivacyLevel(Enum):
    """Privacy levels for aggregation"""
    BASIC = "basic"  # Standard federated averaging
    ENHANCED = "enhanced"  # With differential privacy
    STRICT = "strict"  # With secure multi-party computation


@dataclass
class AggregationConfig:
    """Configuration for secure aggregation"""
    method: AggregationMethod = AggregationMethod.FEDERATED_AVERAGING
    privacy_level: PrivacyLevel = PrivacyLevel.BASIC
    epsilon: float = 1.0  # Differential privacy epsilon
    delta: float = 1e-5  # Differential privacy delta
    clip_norm: float = 1.0  # Gradient clipping norm
    noise_scale: float = 0.01  # Noise scale for differential privacy
    min_clients: int = 2  # Minimum clients required for aggregation


class SecureAggregator:
    """
    Secure aggregator for federated learning
    
    Aggregates embeddings from multiple clinics while preserving privacy.
    Supports various aggregation methods and privacy levels.
    """
    
    def __init__(self, config: Optional[AggregationConfig] = None):
        """
        Initialize secure aggregator
        
        Args:
            config: Aggregation configuration
        """
        self.config = config or AggregationConfig()
        logger.info(f"Secure aggregator initialized: {self.config.method.value}, privacy: {self.config.privacy_level.value}")
    
    def aggregate_embeddings(
        self,
        client_embeddings: Dict[str, List[float]],
        client_weights: Optional[Dict[str, float]] = None
    ) -> List[float]:
        """
        Aggregate embeddings from multiple clients
        
        Args:
            client_embeddings: Dictionary mapping client_id to embedding vector
            client_weights: Optional weights for each client (for weighted averaging)
            
        Returns:
            Aggregated embedding vector
        """
        if not client_embeddings:
            raise ValueError("No client embeddings provided")
        
        if len(client_embeddings) < self.config.min_clients:
            raise ValueError(f"Minimum {self.config.min_clients} clients required, got {len(client_embeddings)}")
        
        # Convert to numpy arrays
        embeddings_dict = {
            client_id: np.array(emb, dtype=np.float32)
            for client_id, emb in client_embeddings.items()
        }
        
        # Validate all embeddings have same dimension
        dims = [emb.shape[0] for emb in embeddings_dict.values()]
        if len(set(dims)) > 1:
            raise ValueError(f"Inconsistent embedding dimensions: {dims}")
        
        # Apply aggregation method
        if self.config.method == AggregationMethod.FEDERATED_AVERAGING:
            aggregated = self._federated_averaging(embeddings_dict, client_weights)
        elif self.config.method == AggregationMethod.WEIGHTED_AVERAGING:
            aggregated = self._weighted_averaging(embeddings_dict, client_weights)
        elif self.config.method == AggregationMethod.MEDIAN_AGGREGATION:
            aggregated = self._median_aggregation(embeddings_dict)
        elif self.config.method == AggregationMethod.SECURE_AGGREGATION:
            aggregated = self._secure_aggregation(embeddings_dict, client_weights)
        elif self.config.method == AggregationMethod.DIFFERENTIAL_PRIVACY:
            aggregated = self._differential_privacy_aggregation(embeddings_dict, client_weights)
        else:
            raise ValueError(f"Unknown aggregation method: {self.config.method}")
        
        # Apply privacy enhancements if needed
        if self.config.privacy_level == PrivacyLevel.ENHANCED:
            aggregated = self._add_differential_privacy_noise(aggregated)
        elif self.config.privacy_level == PrivacyLevel.STRICT:
            aggregated = self._secure_multi_party_aggregation(embeddings_dict, client_weights)
        
        return aggregated.tolist()
    
    def _federated_averaging(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """Standard federated averaging"""
        if weights:
            # Weighted average
            total_weight = sum(weights.values())
            weighted_sum = sum(
                embeddings[client_id] * weights[client_id]
                for client_id in embeddings.keys()
            )
            return weighted_sum / total_weight
        else:
            # Simple average
            return np.mean(list(embeddings.values()), axis=0)
    
    def _weighted_averaging(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """Weighted averaging (requires weights)"""
        if not weights:
            # Fall back to equal weights
            weights = {client_id: 1.0 for client_id in embeddings.keys()}
        
        total_weight = sum(weights.values())
        weighted_sum = sum(
            embeddings[client_id] * weights[client_id]
            for client_id in embeddings.keys()
        )
        return weighted_sum / total_weight
    
    def _median_aggregation(
        self,
        embeddings: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Median aggregation (robust to outliers)"""
        embedding_matrix = np.array(list(embeddings.values()))
        return np.median(embedding_matrix, axis=0)
    
    def _secure_aggregation(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Secure aggregation using secret sharing
        
        Note: This is a simplified version. Full implementation would use
        secure multi-party computation protocols.
        """
        # For now, use federated averaging with additional privacy measures
        aggregated = self._federated_averaging(embeddings, weights)
        
        # Add minimal noise for privacy (simplified)
        noise = np.random.normal(0, self.config.noise_scale, aggregated.shape)
        return aggregated + noise
    
    def _differential_privacy_aggregation(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """Differential privacy aggregation"""
        # First, clip embeddings to bound sensitivity
        clipped_embeddings = {
            client_id: self._clip_embedding(emb)
            for client_id, emb in embeddings.items()
        }
        
        # Aggregate
        aggregated = self._federated_averaging(clipped_embeddings, weights)
        
        # Add differential privacy noise
        return self._add_differential_privacy_noise(aggregated)
    
    def _clip_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Clip embedding to bound L2 norm"""
        norm = np.linalg.norm(embedding)
        if norm > self.config.clip_norm:
            return embedding * (self.config.clip_norm / norm)
        return embedding
    
    def _add_differential_privacy_noise(self, aggregated: np.ndarray) -> np.ndarray:
        """Add Gaussian noise for differential privacy"""
        # Calculate noise scale based on epsilon and delta
        sensitivity = 2 * self.config.clip_norm  # L2 sensitivity
        noise_scale = sensitivity / self.config.epsilon
        
        noise = np.random.normal(0, noise_scale, aggregated.shape)
        return aggregated + noise
    
    def _secure_multi_party_aggregation(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Secure multi-party computation aggregation
        
        Note: This is a placeholder. Full implementation would use
        libraries like PySyft or implement secure aggregation protocols.
        """
        # For now, use differential privacy as a proxy
        logger.warning("Secure MPC not fully implemented, using differential privacy")
        return self._differential_privacy_aggregation(embeddings, weights)
    
    def aggregate_statistics(
        self,
        client_statistics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate statistics from multiple clients
        
        Args:
            client_statistics: Dictionary mapping client_id to statistics dict
            
        Returns:
            Aggregated statistics
        """
        aggregated = {}
        
        # Aggregate numeric statistics
        numeric_keys = set()
        for stats in client_statistics.values():
            numeric_keys.update(k for k, v in stats.items() if isinstance(v, (int, float)))
        
        for key in numeric_keys:
            values = [stats.get(key, 0) for stats in client_statistics.values()]
            aggregated[key] = {
                "mean": np.mean(values),
                "median": np.median(values),
                "min": np.min(values),
                "max": np.max(values),
                "count": len(values)
            }
        
        # Aggregate categorical statistics (counts)
        categorical_keys = set()
        for stats in client_statistics.values():
            categorical_keys.update(k for k, v in stats.items() if isinstance(v, (str, list)))
        
        for key in categorical_keys:
            # Count occurrences
            counts = {}
            for stats in client_statistics.values():
                value = stats.get(key)
                if isinstance(value, list):
                    for item in value:
                        counts[item] = counts.get(item, 0) + 1
                elif value:
                    counts[value] = counts.get(value, 0) + 1
            aggregated[key] = counts
        
        return aggregated

