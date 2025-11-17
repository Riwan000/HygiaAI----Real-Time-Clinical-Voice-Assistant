"""
Federated Memory Architecture

Enables privacy-preserving knowledge sharing across multiple clinics without
exposing raw patient data. Uses federated learning techniques to aggregate
embeddings and knowledge patterns.

Components:
- FederatedCoordinator: Central server for aggregation
- FederatedClient: Clinic-side client for participation
- SecureAggregator: Privacy-preserving aggregation protocols
- FederatedSync: Synchronization and coordination
"""

from .coordinator import FederatedCoordinator, AggregationRound, AggregationResult
from .client import FederatedClient, ClientConfig, ParticipationStatus
from .secure_aggregator import SecureAggregator, AggregationMethod, PrivacyLevel
from .sync import FederatedSync, SyncStatus, SyncConfig

__all__ = [
    "FederatedCoordinator",
    "AggregationRound",
    "AggregationResult",
    "FederatedClient",
    "ClientConfig",
    "ParticipationStatus",
    "SecureAggregator",
    "AggregationMethod",
    "PrivacyLevel",
    "FederatedSync",
    "SyncStatus",
    "SyncConfig",
]

