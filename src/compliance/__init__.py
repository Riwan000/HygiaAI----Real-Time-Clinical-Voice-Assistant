"""
Privacy Compliance Module

Handles:
- Enhanced de-identification (HIPAA Safe Harbor method)
- Comprehensive audit logging
- Access control and authorization
- GDPR compliance (right to be forgotten, data portability)
- Breach detection and notification
- Compliance reporting
"""

from .audit_logger import AuditLogger, AuditEvent, AuditEventType, AuditLevel
from .access_control import AccessControl, AccessRole, Permission, AccessPolicy
from .gdpr_compliance import GDPRCompliance, DataSubjectRequest, RequestType
from .compliance_reporter import ComplianceReporter, ComplianceReport, ComplianceStatus
from .breach_detection import BreachDetector, BreachEvent, BreachSeverity
from .enhanced_deidentification import EnhancedDeIdentificationManager
from .license_validator import LicenseValidator, AccessType as LicenseAccessType

__all__ = [
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditLevel",
    "AccessControl",
    "AccessRole",
    "Permission",
    "AccessPolicy",
    "GDPRCompliance",
    "DataSubjectRequest",
    "RequestType",
    "ComplianceReporter",
    "ComplianceReport",
    "ComplianceStatus",
    "BreachDetector",
    "BreachEvent",
    "BreachSeverity",
    "EnhancedDeIdentificationManager",
    "LicenseValidator",
    "LicenseAccessType"
]

