"""
GDPR Compliance Module

Implements GDPR-specific requirements:
- Right to be forgotten (data deletion)
- Right to data portability
- Right to access
- Consent management
- Data processing records
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """GDPR data subject request types"""
    ACCESS = "access"  # Right to access
    PORTABILITY = "portability"  # Right to data portability
    DELETION = "deletion"  # Right to be forgotten
    RECTIFICATION = "rectification"  # Right to rectification
    RESTRICTION = "restriction"  # Right to restriction of processing
    OBJECTION = "objection"  # Right to object


@dataclass
class DataSubjectRequest:
    """GDPR data subject request"""
    request_id: str
    request_type: RequestType
    data_subject_id: str  # Patient/user ID
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, in_progress, completed, rejected
    requested_data_types: List[str] = field(default_factory=list)
    response_data: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "request_id": self.request_id,
            "request_type": self.request_type.value,
            "data_subject_id": self.data_subject_id,
            "submitted_at": self.submitted_at.isoformat(),
            "status": self.status,
            "requested_data_types": self.requested_data_types,
            "notes": self.notes
        }
        
        if self.response_data:
            data["response_data"] = self.response_data
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        
        return data


class GDPRCompliance:
    """
    GDPR Compliance Manager
    
    Features:
    - Data subject request handling
    - Right to be forgotten (data deletion)
    - Right to data portability
    - Consent management
    - Data processing records
    - Breach notification
    """
    
    def __init__(
        self,
        storage_backend: Optional[Any] = None,  # QdrantStorage or similar
        audit_logger: Optional[Any] = None  # AuditLogger
    ):
        """
        Initialize GDPR compliance manager
        
        Args:
            storage_backend: Storage backend for data operations
            audit_logger: Audit logger for compliance tracking
        """
        self.storage = storage_backend
        self.audit_logger = audit_logger
        self.requests: Dict[str, DataSubjectRequest] = {}
        self.consents: Dict[str, Dict[str, Any]] = {}  # data_subject_id -> consent records
        
        logger.info("GDPR compliance manager initialized")
    
    def submit_data_subject_request(
        self,
        data_subject_id: str,
        request_type: RequestType,
        requested_data_types: Optional[List[str]] = None
    ) -> DataSubjectRequest:
        """
        Submit data subject request
        
        Args:
            data_subject_id: Data subject (patient/user) identifier
            request_type: Type of request
            requested_data_types: Optional list of data types requested
            
        Returns:
            Created DataSubjectRequest
        """
        request_id = f"DSR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{data_subject_id[:8]}"
        
        request = DataSubjectRequest(
            request_id=request_id,
            request_type=request_type,
            data_subject_id=data_subject_id,
            requested_data_types=requested_data_types or []
        )
        
        self.requests[request_id] = request
        
        # Log request
        if self.audit_logger:
            from src.compliance.audit_logger import AuditEventType
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_SUBJECT_REQUEST,
                user_id=data_subject_id,
                resource_type="data_subject_request",
                resource_id=request_id,
                action=f"submit_{request_type.value}",
                result="success",
                compliance_flags=["GDPR"]
            )
        
        logger.info(f"Data subject request submitted: {request_id} ({request_type.value})")
        return request
    
    def process_access_request(self, request_id: str) -> Dict[str, Any]:
        """
        Process right to access request
        
        Args:
            request_id: Request ID
            
        Returns:
            Dictionary with all data about the data subject
        """
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        if request.request_type != RequestType.ACCESS:
            raise ValueError(f"Request {request_id} is not an access request")
        
        request.status = "in_progress"
        
        # Collect all data about the data subject
        data_subject_id = request.data_subject_id
        collected_data = {
            "data_subject_id": data_subject_id,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "data_categories": {}
        }
        
        # Query storage for all data related to this subject
        if self.storage:
            try:
                # Search for all cases/transcripts for this patient
                dummy_embedding = [0.0] * (self.storage.vector_size if hasattr(self.storage, 'vector_size') else 768)
                results = self.storage.search_with_filters(
                    query_embedding=dummy_embedding,
                    filters={"patient_id": data_subject_id},
                    limit=10000
                )
                
                collected_data["data_categories"]["clinical_cases"] = [
                    {
                        "case_id": r.get("id"),
                        "timestamp": r.get("payload", {}).get("timestamp"),
                        "data_types": list(r.get("payload", {}).keys())
                    }
                    for r in results
                ]
            except Exception as e:
                logger.error(f"Error collecting data for access request: {e}")
                collected_data["error"] = str(e)
        
        # Add consent records
        if data_subject_id in self.consents:
            collected_data["data_categories"]["consents"] = self.consents[data_subject_id]
        
        request.response_data = collected_data
        request.status = "completed"
        request.completed_at = datetime.now(timezone.utc)
        
        # Log completion
        if self.audit_logger:
            from src.compliance.audit_logger import AuditEventType
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_SUBJECT_REQUEST,
                user_id=data_subject_id,
                resource_type="data_subject_request",
                resource_id=request_id,
                action="complete_access_request",
                result="success",
                compliance_flags=["GDPR"]
            )
        
        return collected_data
    
    def process_portability_request(self, request_id: str) -> Dict[str, Any]:
        """
        Process right to data portability request
        
        Args:
            request_id: Request ID
            
        Returns:
            Machine-readable data export (JSON)
        """
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        if request.request_type != RequestType.PORTABILITY:
            raise ValueError(f"Request {request_id} is not a portability request")
        
        request.status = "in_progress"
        
        # Get access data first
        access_data = self.process_access_request(request_id)
        
        # Format for portability (machine-readable, structured)
        portable_data = {
            "export_format": "JSON",
            "export_date": datetime.now(timezone.utc).isoformat(),
            "data_subject_id": request.data_subject_id,
            "data": access_data["data_categories"]
        }
        
        request.response_data = portable_data
        request.status = "completed"
        request.completed_at = datetime.now(timezone.utc)
        
        # Log completion
        if self.audit_logger:
            from src.compliance.audit_logger import AuditEventType
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_PORTABILITY_REQUEST,
                user_id=request.data_subject_id,
                resource_type="data_subject_request",
                resource_id=request_id,
                action="complete_portability_request",
                result="success",
                compliance_flags=["GDPR"]
            )
        
        return portable_data
    
    def process_deletion_request(
        self,
        request_id: str,
        confirm_deletion: bool = False
    ) -> Dict[str, Any]:
        """
        Process right to be forgotten (deletion) request
        
        Args:
            request_id: Request ID
            confirm_deletion: Must be True to actually delete data
            
        Returns:
            Deletion report
        """
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        if request.request_type != RequestType.DELETION:
            raise ValueError(f"Request {request_id} is not a deletion request")
        
        if not confirm_deletion:
            raise ValueError("Deletion requires explicit confirmation")
        
        request.status = "in_progress"
        
        data_subject_id = request.data_subject_id
        deletion_report = {
            "data_subject_id": data_subject_id,
            "deletion_started_at": datetime.now(timezone.utc).isoformat(),
            "deleted_resources": [],
            "errors": []
        }
        
        # Delete all data related to this subject
        if self.storage:
            try:
                # Search for all cases/transcripts
                dummy_embedding = [0.0] * (self.storage.vector_size if hasattr(self.storage, 'vector_size') else 768)
                results = self.storage.search_with_filters(
                    query_embedding=dummy_embedding,
                    filters={"patient_id": data_subject_id},
                    limit=10000
                )
                
                # Delete each resource
                for result in results:
                    resource_id = result.get("id")
                    try:
                        # Delete from storage
                        if hasattr(self.storage, 'delete_transcript'):
                            self.storage.delete_transcript(resource_id)
                        elif hasattr(self.storage, 'client'):
                            self.storage.client.delete(
                                collection_name=self.storage.collection_name,
                                points_selector=[resource_id]
                            )
                        deletion_report["deleted_resources"].append(resource_id)
                    except Exception as e:
                        deletion_report["errors"].append({
                            "resource_id": resource_id,
                            "error": str(e)
                        })
            except Exception as e:
                logger.error(f"Error deleting data: {e}")
                deletion_report["errors"].append({"error": str(e)})
        
        # Remove consent records
        if data_subject_id in self.consents:
            del self.consents[data_subject_id]
        
        request.response_data = deletion_report
        request.status = "completed"
        request.completed_at = datetime.now(timezone.utc)
        
        # Log deletion
        if self.audit_logger:
            from src.compliance.audit_logger import AuditEventType, AuditLevel
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_DELETION_REQUEST,
                user_id=data_subject_id,
                resource_type="data_subject_request",
                resource_id=request_id,
                action="complete_deletion_request",
                result="success",
                severity=AuditLevel.WARNING,
                compliance_flags=["GDPR"]
            )
        
        logger.warning(f"Data deletion completed for subject {data_subject_id}: {len(deletion_report['deleted_resources'])} resources deleted")
        return deletion_report
    
    def record_consent(
        self,
        data_subject_id: str,
        consent_type: str,
        granted: bool,
        purpose: str = "",
        expires_at: Optional[datetime] = None
    ):
        """
        Record data subject consent
        
        Args:
            data_subject_id: Data subject identifier
            consent_type: Type of consent
            granted: Whether consent is granted
            purpose: Purpose of consent
            expires_at: Optional expiration date
        """
        if data_subject_id not in self.consents:
            self.consents[data_subject_id] = {}
        
        self.consents[data_subject_id][consent_type] = {
            "granted": granted,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "purpose": purpose,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
        
        logger.info(f"Recorded consent {consent_type} for subject {data_subject_id}: {granted}")
    
    def check_consent(
        self,
        data_subject_id: str,
        consent_type: str
    ) -> bool:
        """
        Check if data subject has given consent
        
        Args:
            data_subject_id: Data subject identifier
            consent_type: Type of consent
            
        Returns:
            True if consent is granted and valid
        """
        if data_subject_id not in self.consents:
            return False
        
        consent_record = self.consents[data_subject_id].get(consent_type)
        if not consent_record:
            return False
        
        if not consent_record.get("granted", False):
            return False
        
        # Check expiration
        expires_at = consent_record.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > expiry:
                    return False
            except Exception:
                pass
        
        return True
    
    def get_request(self, request_id: str) -> Optional[DataSubjectRequest]:
        """Get data subject request by ID"""
        return self.requests.get(request_id)
    
    def list_requests(
        self,
        data_subject_id: Optional[str] = None,
        request_type: Optional[RequestType] = None,
        status: Optional[str] = None
    ) -> List[DataSubjectRequest]:
        """
        List data subject requests
        
        Args:
            data_subject_id: Filter by data subject ID
            request_type: Filter by request type
            status: Filter by status
            
        Returns:
            List of matching requests
        """
        requests = list(self.requests.values())
        
        if data_subject_id:
            requests = [r for r in requests if r.data_subject_id == data_subject_id]
        if request_type:
            requests = [r for r in requests if r.request_type == request_type]
        if status:
            requests = [r for r in requests if r.status == status]
        
        return requests

