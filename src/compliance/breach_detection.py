"""
Breach Detection Module

Detects and manages data breaches for HIPAA/GDPR compliance.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BreachSeverity(Enum):
    """Breach severity levels"""
    LOW = "low"  # Minimal risk
    MEDIUM = "medium"  # Moderate risk
    HIGH = "high"  # Significant risk
    CRITICAL = "critical"  # Severe risk requiring immediate action


@dataclass
class BreachEvent:
    """Data breach event"""
    breach_id: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    severity: BreachSeverity = BreachSeverity.MEDIUM
    breach_type: str = ""  # e.g., "unauthorized_access", "data_loss", "encryption_failure"
    description: str = ""
    affected_data_subjects: List[str] = field(default_factory=list)
    affected_data_types: List[str] = field(default_factory=list)
    detected_by: Optional[str] = None  # User/system that detected breach
    status: str = "detected"  # detected, investigating, contained, resolved
    containment_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None
    notification_sent: bool = False
    notification_time: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "breach_id": self.breach_id,
            "detected_at": self.detected_at.isoformat(),
            "severity": self.severity.value,
            "breach_type": self.breach_type,
            "description": self.description,
            "affected_data_subjects": self.affected_data_subjects,
            "affected_data_types": self.affected_data_types,
            "status": self.status,
            "notification_sent": self.notification_sent
        }
        
        if self.detected_by:
            data["detected_by"] = self.detected_by
        if self.containment_time:
            data["containment_time"] = self.containment_time.isoformat()
        if self.resolution_time:
            data["resolution_time"] = self.resolution_time.isoformat()
        if self.notification_time:
            data["notification_time"] = self.notification_time.isoformat()
        
        data["details"] = self.details
        return data


class BreachDetector:
    """
    Breach Detection and Management System
    
    Features:
    - Automated breach detection
    - Breach severity assessment
    - Notification management
    - Breach reporting
    """
    
    def __init__(
        self,
        audit_logger: Optional[Any] = None,
        notification_handler: Optional[Any] = None
    ):
        """
        Initialize breach detector
        
        Args:
            audit_logger: AuditLogger instance for monitoring
            notification_handler: Optional notification handler
        """
        self.audit_logger = audit_logger
        self.notification_handler = notification_handler
        self.breaches: Dict[str, BreachEvent] = {}
        self._breach_counter = 0
        
        logger.info("Breach detector initialized")
    
    def detect_breach(
        self,
        breach_type: str,
        description: str,
        severity: BreachSeverity = BreachSeverity.MEDIUM,
        affected_data_subjects: Optional[List[str]] = None,
        affected_data_types: Optional[List[str]] = None,
        detected_by: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> BreachEvent:
        """
        Detect and record a data breach
        
        Args:
            breach_type: Type of breach
            description: Breach description
            severity: Breach severity
            affected_data_subjects: List of affected data subjects
            affected_data_types: List of affected data types
            detected_by: Who detected the breach
            details: Additional breach details
            
        Returns:
            Created BreachEvent
        """
        self._breach_counter += 1
        breach_id = f"BREACH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._breach_counter:04d}"
        
        breach = BreachEvent(
            breach_id=breach_id,
            breach_type=breach_type,
            description=description,
            severity=severity,
            affected_data_subjects=affected_data_subjects or [],
            affected_data_types=affected_data_types or [],
            detected_by=detected_by,
            details=details or {}
        )
        
        self.breaches[breach_id] = breach
        
        # Log breach detection
        if self.audit_logger:
            from src.compliance.audit_logger import AuditEventType, AuditLevel
            self.audit_logger.log_event(
                event_type=AuditEventType.BREACH_DETECTED,
                user_id=detected_by or "system",
                resource_type="breach",
                resource_id=breach_id,
                action="detect_breach",
                result="detected",
                severity=AuditLevel.CRITICAL if severity == BreachSeverity.CRITICAL else AuditLevel.ERROR,
                details=breach.to_dict(),
                compliance_flags=["HIPAA", "GDPR"]
            )
        
        # Send notification for high/critical breaches
        if severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]:
            self._send_breach_notification(breach)
        
        logger.critical(f"Data breach detected: {breach_id} ({breach_type}, severity: {severity.value})")
        return breach
    
    def _send_breach_notification(self, breach: BreachEvent):
        """Send breach notification"""
        try:
            # In production, would send to compliance officers, data protection officer, etc.
            if self.notification_handler:
                self.notification_handler.send_breach_notification(breach)
            else:
                # Log notification requirement
                logger.critical(
                    f"BREACH NOTIFICATION REQUIRED: {breach.breach_id} - "
                    f"Type: {breach.breach_type}, Severity: {breach.severity.value}, "
                    f"Affected subjects: {len(breach.affected_data_subjects)}"
                )
            
            breach.notification_sent = True
            breach.notification_time = datetime.now(timezone.utc)
            
            # Log notification
            if self.audit_logger:
                from src.compliance.audit_logger import AuditEventType
                self.audit_logger.log_event(
                    event_type=AuditEventType.BREACH_NOTIFICATION,
                    user_id="system",
                    resource_type="breach",
                    resource_id=breach.breach_id,
                    action="send_notification",
                    result="sent",
                    compliance_flags=["HIPAA", "GDPR"]
                )
        except Exception as e:
            logger.error(f"Error sending breach notification: {e}")
    
    def contain_breach(self, breach_id: str) -> bool:
        """
        Mark breach as contained
        
        Args:
            breach_id: Breach ID
            
        Returns:
            True if successful
        """
        breach = self.breaches.get(breach_id)
        if not breach:
            return False
        
        breach.status = "contained"
        breach.containment_time = datetime.now(timezone.utc)
        
        logger.info(f"Breach {breach_id} marked as contained")
        return True
    
    def resolve_breach(self, breach_id: str, resolution_notes: str = "") -> bool:
        """
        Mark breach as resolved
        
        Args:
            breach_id: Breach ID
            resolution_notes: Optional resolution notes
            
        Returns:
            True if successful
        """
        breach = self.breaches.get(breach_id)
        if not breach:
            return False
        
        breach.status = "resolved"
        breach.resolution_time = datetime.now(timezone.utc)
        if resolution_notes:
            breach.details["resolution_notes"] = resolution_notes
        
        logger.info(f"Breach {breach_id} marked as resolved")
        return True
    
    def get_breach(self, breach_id: str) -> Optional[BreachEvent]:
        """Get breach by ID"""
        return self.breaches.get(breach_id)
    
    def list_breaches(
        self,
        status: Optional[str] = None,
        severity: Optional[BreachSeverity] = None
    ) -> List[BreachEvent]:
        """
        List breaches
        
        Args:
            status: Filter by status
            severity: Filter by severity
            
        Returns:
            List of matching breaches
        """
        breaches = list(self.breaches.values())
        
        if status:
            breaches = [b for b in breaches if b.status == status]
        if severity:
            breaches = [b for b in breaches if b.severity == severity]
        
        return breaches
    
    def monitor_for_breaches(self, audit_events: List[Any]) -> List[BreachEvent]:
        """
        Monitor audit events for potential breaches
        
        Args:
            audit_events: List of audit events to analyze
            
        Returns:
            List of detected breaches
        """
        detected_breaches = []
        
        # Check for unauthorized access patterns
        failed_access_attempts = {}
        for event in audit_events:
            if hasattr(event, 'result') and event.result == "denied":
                user_id = getattr(event, 'user_id', 'unknown')
                if user_id not in failed_access_attempts:
                    failed_access_attempts[user_id] = 0
                failed_access_attempts[user_id] += 1
        
        # Detect potential brute force attacks
        for user_id, count in failed_access_attempts.items():
            if count >= 5:  # Threshold for breach detection
                breach = self.detect_breach(
                    breach_type="unauthorized_access_attempt",
                    description=f"Multiple failed access attempts for user {user_id} ({count} attempts)",
                    severity=BreachSeverity.HIGH,
                    detected_by="automated_monitoring",
                    details={"failed_attempts": count, "user_id": user_id}
                )
                detected_breaches.append(breach)
        
        # Check for unusual data access patterns
        # (In production, would use more sophisticated anomaly detection)
        
        return detected_breaches

