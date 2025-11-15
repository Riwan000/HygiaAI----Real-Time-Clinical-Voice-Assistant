"""
FastAPI endpoints for EHR integration

Provides REST API endpoints for:
- EHR connection management
- Import/export patient data
- HL7/FHIR message handling
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.ehr import (
    EHRConnector,
    ConnectionConfig,
    EHRSystem,
    EHRIntegration,
    HL7Adapter,
    FHIRAdapter
)
from src.storage import QdrantStorage

router = APIRouter(prefix="/api/ehr", tags=["ehr"])


# Request/Response models
class EHRConnectionRequest(BaseModel):
    """Request model for EHR connection"""
    system: str = Field(..., description="EHR system name (epic, cerner, etc.)")
    host: str = Field(..., description="EHR system host")
    port: int = Field(443, description="EHR system port")
    use_ssl: bool = Field(True, description="Use SSL/TLS")
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    fhir_base_url: Optional[str] = None
    hl7_endpoint: Optional[str] = None


class HL7MessageRequest(BaseModel):
    """Request model for HL7 message"""
    message: str = Field(..., description="HL7 message string")


class FHIRResourceRequest(BaseModel):
    """Request model for FHIR resource"""
    resource_json: str = Field(..., description="FHIR resource JSON string")


class ExportCaseRequest(BaseModel):
    """Request model for exporting case to EHR"""
    case_id: str = Field(..., description="Case ID to export")


# Dependency injection
def get_qdrant_storage() -> QdrantStorage:
    """Get Qdrant storage instance"""
    return QdrantStorage(
        host="localhost",
        port=6333,
        enable_encryption=False,
        enable_deidentification=False
    )


# Store active connections (in production, use proper session management)
_active_connections: Dict[str, EHRConnector] = {}


@router.post("/connect")
async def connect_ehr(request: EHRConnectionRequest):
    """Connect to EHR system"""
    try:
        # Map system string to enum
        system_map = {
            "epic": EHRSystem.EPIC,
            "cerner": EHRSystem.CERNER,
            "allscripts": EHRSystem.ALLSCRIPTS,
            "athenahealth": EHRSystem.ATHENAHEALTH,
            "nextgen": EHRSystem.NEXTGEN,
            "eclinicalworks": EHRSystem.ECLINICALWORKS,
            "generic_hl7": EHRSystem.GENERIC_HL7,
            "generic_fhir": EHRSystem.GENERIC_FHIR
        }
        
        system = system_map.get(request.system.lower())
        if not system:
            raise HTTPException(status_code=400, detail=f"Unknown EHR system: {request.system}")
        
        config = ConnectionConfig(
            system=system,
            host=request.host,
            port=request.port,
            use_ssl=request.use_ssl,
            api_key=request.api_key,
            username=request.username,
            password=request.password,
            client_id=request.client_id,
            client_secret=request.client_secret,
            fhir_base_url=request.fhir_base_url,
            hl7_endpoint=request.hl7_endpoint
        )
        
        connector = EHRConnector(config)
        if connector.connect():
            connection_id = f"{system.value}-{request.host}"
            _active_connections[connection_id] = connector
            return {
                "connection_id": connection_id,
                "status": "connected",
                "system": system.value
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to EHR system")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect/{connection_id}")
async def disconnect_ehr(connection_id: str):
    """Disconnect from EHR system"""
    if connection_id in _active_connections:
        _active_connections[connection_id].disconnect()
        del _active_connections[connection_id]
        return {"status": "disconnected"}
    else:
        raise HTTPException(status_code=404, detail="Connection not found")


@router.post("/import/hl7")
async def import_hl7_message(
    request: HL7MessageRequest,
    storage: QdrantStorage = Depends(get_qdrant_storage)
):
    """Import patient data from HL7 message"""
    try:
        hl7_adapter = HL7Adapter()
        integration = EHRIntegration(
            ehr_connector=None,  # Not needed for import
            qdrant_storage=storage
        )
        
        imported_data = integration.import_patient_from_hl7(request.message)
        
        # Generate embedding (would use actual embedding generator in production)
        from src.embeddings.text_embeddings import TextEmbeddingGenerator
        embedding_gen = TextEmbeddingGenerator()
        transcript = imported_data.get("transcript", "")
        if not transcript:
            transcript = f"Patient {imported_data.get('patient_name', 'Unknown')} - {imported_data.get('diagnosis', '')}"
        embedding = embedding_gen.generate_embedding(transcript)
        
        # Store in Qdrant
        point_id = integration.store_imported_data(imported_data, embedding)
        
        return {
            "status": "imported",
            "point_id": point_id,
            "patient_id": imported_data.get("patient_id"),
            "data": imported_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/fhir")
async def import_fhir_resource(
    request: FHIRResourceRequest,
    storage: QdrantStorage = Depends(get_qdrant_storage)
):
    """Import patient data from FHIR resource"""
    try:
        fhir_adapter = FHIRAdapter()
        integration = EHRIntegration(
            ehr_connector=None,  # Not needed for import
            qdrant_storage=storage
        )
        
        imported_data = integration.import_patient_from_fhir(request.resource_json)
        
        # Generate embedding
        from src.embeddings.text_embeddings import TextEmbeddingGenerator
        embedding_gen = TextEmbeddingGenerator()
        transcript = imported_data.get("data", {}).get("text", "")
        if not transcript:
            patient_name = imported_data.get("patient_name", "Unknown")
            condition = imported_data.get("condition_name", "")
            transcript = f"Patient {patient_name} - {condition}"
        embedding = embedding_gen.generate_embedding(transcript)
        
        # Store in Qdrant
        point_id = integration.store_imported_data(imported_data, embedding)
        
        return {
            "status": "imported",
            "point_id": point_id,
            "resource_id": imported_data.get("resource_id"),
            "data": imported_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{connection_id}")
async def export_case_to_ehr(
    connection_id: str,
    request: ExportCaseRequest,
    storage: QdrantStorage = Depends(get_qdrant_storage)
):
    """Export case to EHR system"""
    try:
        if connection_id not in _active_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connector = _active_connections[connection_id]
        
        # Get case from Qdrant (simplified - would need proper case retrieval)
        # For now, create a mock case
        from src.models.case_models import Case, CaseMetadata, CaseModality
        from datetime import datetime, timezone
        
        # In production, would retrieve actual case from Qdrant
        case = Case(
            case_id=request.case_id,
            patient_id="patient-123",
            modalities={},
            metadata=CaseMetadata(
                timestamp=datetime.now(timezone.utc),
                diagnosis="pneumonia"
            )
        )
        
        integration = EHRIntegration(
            ehr_connector=connector,
            qdrant_storage=storage
        )
        
        success = integration.export_case_to_ehr(case)
        
        if success:
            return {
                "status": "exported",
                "case_id": request.case_id,
                "connection_id": connection_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to export case to EHR")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections")
async def list_connections():
    """List active EHR connections"""
    connections = []
    for conn_id, connector in _active_connections.items():
        connections.append({
            "connection_id": conn_id,
            "system": connector.config.system.value,
            "host": connector.config.host,
            "connected": connector.is_connected()
        })
    return {"connections": connections}

