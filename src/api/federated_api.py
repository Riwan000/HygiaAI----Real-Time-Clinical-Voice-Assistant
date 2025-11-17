"""
Federated Learning API Endpoints

REST API endpoints for federated learning coordination and participation.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.federated.integration import FederatedMemoryIntegration
from src.storage.qdrant_storage import QdrantStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/federated", tags=["Federated Learning"])


# Request/Response Models
class StartRoundRequest(BaseModel):
    min_clients: int = Field(2, ge=2, description="Minimum clients required")
    max_clients: Optional[int] = Field(None, description="Maximum clients allowed")


class StartRoundResponse(BaseModel):
    round_id: str
    status: str
    min_clients: int


class SubmitEmbeddingRequest(BaseModel):
    client_id: str
    embedding: List[float]
    weight: Optional[float] = None
    statistics: Optional[Dict[str, Any]] = None


class SubmitEmbeddingResponse(BaseModel):
    success: bool
    message: str


class AggregateRoundResponse(BaseModel):
    round_id: str
    success: bool
    aggregated_embedding: Optional[List[float]] = None
    aggregated_statistics: Optional[Dict[str, Any]] = None
    participating_clients: List[str] = []
    error: Optional[str] = None


class RoundStatusResponse(BaseModel):
    round_id: str
    status: str
    participating_clients: int
    min_clients: int
    created_at: str
    completed_at: Optional[str] = None


class FederatedStatisticsResponse(BaseModel):
    enabled: bool
    coordinator: Optional[Dict[str, Any]] = None
    client: Optional[Dict[str, Any]] = None
    sync: Optional[Dict[str, Any]] = None


# Global federated integration instance
_federated_integration: Optional[FederatedMemoryIntegration] = None


def get_federated_integration() -> FederatedMemoryIntegration:
    """Get or create federated integration instance"""
    global _federated_integration
    
    if _federated_integration is None:
        # Initialize with default Qdrant storage
        qdrant_storage = QdrantStorage(
            collection_name="hygiaai_transcripts",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        coordinator_url = os.getenv("FEDERATED_COORDINATOR_URL")
        client_id = os.getenv("FEDERATED_CLIENT_ID")
        
        _federated_integration = FederatedMemoryIntegration(
            qdrant_storage=qdrant_storage,
            coordinator_url=coordinator_url,
            client_id=client_id,
            enable_federated=True
        )
    
    return _federated_integration


@router.post("/rounds/start", response_model=StartRoundResponse)
async def start_aggregation_round(
    request: StartRoundRequest,
    integration: FederatedMemoryIntegration = Depends(get_federated_integration)
):
    """
    Start a new federated learning aggregation round
    
    Only available when acting as coordinator.
    """
    if not integration.enable_federated:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    round_id = integration.start_federated_round(min_clients=request.min_clients)
    
    if not round_id:
        raise HTTPException(status_code=500, detail="Failed to start aggregation round")
    
    return StartRoundResponse(
        round_id=round_id,
        status="collecting",
        min_clients=request.min_clients
    )


@router.post("/rounds/{round_id}/submit", response_model=SubmitEmbeddingResponse)
async def submit_embedding(
    round_id: str,
    request: SubmitEmbeddingRequest,
    integration: FederatedMemoryIntegration = Depends(get_federated_integration)
):
    """
    Submit embedding to an aggregation round
    
    Clients use this endpoint to contribute their local embeddings.
    """
    if not integration.enable_federated or not integration.coordinator:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    success = integration.coordinator.submit_embedding(
        round_id=round_id,
        client_id=request.client_id,
        embedding=request.embedding,
        weight=request.weight,
        statistics=request.statistics
    )
    
    if success:
        return SubmitEmbeddingResponse(
            success=True,
            message=f"Embedding submitted successfully to round {round_id}"
        )
    else:
        raise HTTPException(status_code=400, detail="Failed to submit embedding")


@router.post("/rounds/{round_id}/aggregate", response_model=AggregateRoundResponse)
async def aggregate_round(
    round_id: str,
    integration: FederatedMemoryIntegration = Depends(get_federated_integration)
):
    """
    Aggregate a federated learning round
    
    Performs secure aggregation of all submitted embeddings.
    """
    if not integration.enable_federated:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    result = integration.aggregate_round(round_id)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to aggregate round")
    
    return AggregateRoundResponse(**result)


@router.get("/rounds/{round_id}/status", response_model=RoundStatusResponse)
async def get_round_status(
    round_id: str,
    integration: FederatedMemoryIntegration = Depends(get_federated_integration)
):
    """Get status of an aggregation round"""
    if not integration.enable_federated or not integration.coordinator:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    round = integration.coordinator.get_round_status(round_id)
    
    if not round:
        raise HTTPException(status_code=404, detail=f"Round {round_id} not found")
    
    return RoundStatusResponse(
        round_id=round.round_id,
        status=round.status.value,
        participating_clients=len(round.participating_clients),
        min_clients=round.min_clients,
        created_at=round.created_at.isoformat(),
        completed_at=round.completed_at.isoformat() if round.completed_at else None
    )


@router.get("/statistics", response_model=FederatedStatisticsResponse)
async def get_federated_statistics(
    integration: FederatedMemoryIntegration = Depends(get_federated_integration)
):
    """Get federated learning statistics"""
    stats = integration.get_federated_statistics()
    return FederatedStatisticsResponse(**stats)


@router.post("/sync")
async def sync_with_global(
    integration: FederatedMemoryIntegration = Depends(get_federated_integration)
):
    """Synchronize local embeddings with global federated model"""
    if not integration.enable_federated:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    success = integration.sync_with_global_model()
    
    if success:
        return {"success": True, "message": "Synchronization completed"}
    else:
        raise HTTPException(status_code=500, detail="Synchronization failed")


@router.post("/participate/{round_id}")
async def participate_in_round(
    round_id: str,
    integration: FederatedMemoryIntegration = Depends(get_federated_integration)
):
    """Participate in a federated learning round (client-side)"""
    if not integration.enable_federated:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    success = integration.participate_in_federated_round(round_id)
    
    if success:
        return {"success": True, "message": f"Successfully participated in round {round_id}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to participate in round")

