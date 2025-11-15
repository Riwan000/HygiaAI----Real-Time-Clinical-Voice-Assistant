"""
FastAPI endpoints for compliance features

Provides REST API endpoints for:
- Audit log access
- Access control
- GDPR data subject requests
- Compliance reporting
- Breach management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from src.compliance import (
    AuditLogger,
    AuditEventType,
    AccessControl,
    AccessRole,
    Permission,
    GDPRCompliance,
    RequestType,
    ComplianceReporter,
    BreachDetector,
    BreachSeverity
)

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


# Request/Response models
class AuditQueryRequest(BaseModel):
    """Request model for audit log query"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    event_type: Optional[str] = None
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    limit: int = Field(100, ge=1, le=10000)


class DataSubjectRequestModel(BaseModel):
    """Request model for GDPR data subject request"""
    data_subject_id: str
    request_type: str  # "access", "portability", "deletion"
    requested_data_types: Optional[List[str]] = None


class ComplianceReportRequest(BaseModel):
    """Request model for compliance report"""
    report_type: str = "combined"  # "HIPAA", "GDPR", or "combined"
    start_date: str
    end_date: str


# Dependency injection
_audit_logger: Optional[AuditLogger] = None
_access_control: Optional[AccessControl] = None
_gdpr_compliance: Optional[GDPRCompliance] = None
_compliance_reporter: Optional[ComplianceReporter] = None
_breach_detector: Optional[BreachDetector] = None


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_directory="logs/audit")
    return _audit_logger


def get_access_control() -> AccessControl:
    """Get access control instance"""
    global _access_control
    if _access_control is None:
        _access_control = AccessControl()
    return _access_control


def get_gdpr_compliance() -> GDPRCompliance:
    """Get GDPR compliance instance"""
    global _gdpr_compliance
    if _gdpr_compliance is None:
        from src.storage.qdrant_storage import QdrantStorage
        storage = QdrantStorage(enable_encryption=False, enable_deidentification=False)
        _gdpr_compliance = GDPRCompliance(
            storage_backend=storage,
            audit_logger=get_audit_logger()
        )
    return _gdpr_compliance


def get_compliance_reporter() -> ComplianceReporter:
    """Get compliance reporter instance"""
    global _compliance_reporter
    if _compliance_reporter is None:
        _compliance_reporter = ComplianceReporter(
            audit_logger=get_audit_logger(),
            access_control=get_access_control(),
            gdpr_compliance=get_gdpr_compliance()
        )
    return _compliance_reporter


def get_breach_detector() -> BreachDetector:
    """Get breach detector instance"""
    global _breach_detector
    if _breach_detector is None:
        _breach_detector = BreachDetector(audit_logger=get_audit_logger())
    return _breach_detector


@router.post("/audit/query")
async def query_audit_logs(
    request: AuditQueryRequest,
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Query audit logs"""
    try:
        start_date = None
        end_date = None
        
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        event_type = None
        if request.event_type:
            try:
                event_type = AuditEventType(request.event_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")
        
        events = audit_logger.query_events(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            user_id=request.user_id,
            resource_id=request.resource_id,
            limit=request.limit
        )
        
        return {
            "events": [e.to_dict() for e in events],
            "count": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/log")
async def log_audit_event(
    event_type: str = Body(...),
    user_id: Optional[str] = Body(None),
    resource_type: Optional[str] = Body(None),
    resource_id: Optional[str] = Body(None),
    action: str = Body(""),
    result: str = Body("success"),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Log an audit event"""
    try:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
        
        event = audit_logger.log_event(
            event_type=event_type_enum,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result
        )
        
        return {"event_id": event.event_id, "status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/access/check")
async def check_permission(
    user_id: str = Body(...),
    permission: str = Body(...),
    resource_id: Optional[str] = Body(None),
    access_control: AccessControl = Depends(get_access_control)
):
    """Check user permission"""
    try:
        try:
            permission_enum = Permission(permission)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid permission: {permission}")
        
        has_permission = access_control.check_permission(
            user_id=user_id,
            permission=permission_enum,
            resource_id=resource_id
        )
        
        return {
            "user_id": user_id,
            "permission": permission,
            "granted": has_permission
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gdpr/request")
async def submit_data_subject_request(
    request: DataSubjectRequestModel,
    gdpr: GDPRCompliance = Depends(get_gdpr_compliance)
):
    """Submit GDPR data subject request"""
    try:
        try:
            request_type_enum = RequestType(request.request_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid request type: {request.request_type}")
        
        dsr = gdpr.submit_data_subject_request(
            data_subject_id=request.data_subject_id,
            request_type=request_type_enum,
            requested_data_types=request.requested_data_types
        )
        
        return {"request_id": dsr.request_id, "status": dsr.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gdpr/process/{request_id}")
async def process_data_subject_request(
    request_id: str,
    confirm_deletion: bool = Body(False),
    gdpr: GDPRCompliance = Depends(get_gdpr_compliance)
):
    """Process GDPR data subject request"""
    try:
        request = gdpr.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.request_type == RequestType.ACCESS:
            result = gdpr.process_access_request(request_id)
        elif request.request_type == RequestType.PORTABILITY:
            result = gdpr.process_portability_request(request_id)
        elif request.request_type == RequestType.DELETION:
            if not confirm_deletion:
                raise HTTPException(status_code=400, detail="Deletion requires explicit confirmation")
            result = gdpr.process_deletion_request(request_id, confirm_deletion=True)
        else:
            raise HTTPException(status_code=400, detail=f"Request type {request.request_type.value} not yet implemented")
        
        return {"request_id": request_id, "status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report/generate")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    reporter: ComplianceReporter = Depends(get_compliance_reporter)
):
    """Generate compliance report"""
    try:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        if request.report_type == "HIPAA":
            report = reporter.generate_hipaa_report(start_date, end_date)
        elif request.report_type == "GDPR":
            report = reporter.generate_gdpr_report(start_date, end_date)
        else:
            report = reporter.generate_combined_report(start_date, end_date)
        
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breach/detect")
async def detect_breach(
    breach_type: str = Body(...),
    description: str = Body(...),
    severity: str = Body("medium"),
    affected_data_subjects: Optional[List[str]] = Body(None),
    detector: BreachDetector = Depends(get_breach_detector)
):
    """Detect and record a data breach"""
    try:
        try:
            severity_enum = BreachSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        breach = detector.detect_breach(
            breach_type=breach_type,
            description=description,
            severity=severity_enum,
            affected_data_subjects=affected_data_subjects or []
        )
        
        return {"breach_id": breach.breach_id, "status": breach.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breach/list")
async def list_breaches(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    detector: BreachDetector = Depends(get_breach_detector)
):
    """List data breaches"""
    try:
        severity_enum = None
        if severity:
            try:
                severity_enum = BreachSeverity(severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        breaches = detector.list_breaches(status=status, severity=severity_enum)
        
        return {
            "breaches": [b.to_dict() for b in breaches],
            "count": len(breaches)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

