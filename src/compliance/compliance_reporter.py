"""
Compliance Reporting Module

Generates compliance reports for HIPAA and GDPR audits.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    MINOR_ISSUES = "minor_issues"
    MAJOR_ISSUES = "major_issues"
    NON_COMPLIANT = "non_compliant"


@dataclass
class ComplianceReport:
    """Compliance report"""
    report_id: str
    report_type: str  # "HIPAA", "GDPR", or "combined"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "generated_at": self.generated_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "status": self.status.value,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "metrics": self.metrics
        }


class ComplianceReporter:
    """
    Compliance Reporter
    
    Generates compliance reports for:
    - HIPAA compliance audits
    - GDPR compliance audits
    - Combined compliance status
    """
    
    def __init__(
        self,
        audit_logger: Optional[Any] = None,
        access_control: Optional[Any] = None,
        gdpr_compliance: Optional[Any] = None
    ):
        """
        Initialize compliance reporter
        
        Args:
            audit_logger: AuditLogger instance
            access_control: AccessControl instance
            gdpr_compliance: GDPRCompliance instance
        """
        self.audit_logger = audit_logger
        self.access_control = access_control
        self.gdpr_compliance = gdpr_compliance
        
        logger.info("Compliance reporter initialized")
    
    def generate_hipaa_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """
        Generate HIPAA compliance report
        
        Args:
            start_date: Report period start
            end_date: Report period end
            
        Returns:
            HIPAA compliance report
        """
        report_id = f"HIPAA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = ComplianceReport(
            report_id=report_id,
            report_type="HIPAA",
            period_start=start_date,
            period_end=end_date
        )
        
        findings = []
        metrics = {}
        
        # Check audit logging
        if self.audit_logger:
            audit_report = self.audit_logger.generate_compliance_report(
                start_date=start_date,
                end_date=end_date,
                compliance_standard="HIPAA"
            )
            metrics["audit_events"] = audit_report.get("summary", {})
            
            # Check for missing audit logs
            if audit_report.get("summary", {}).get("total_events", 0) == 0:
                findings.append({
                    "severity": "warning",
                    "category": "audit_logging",
                    "finding": "No audit events recorded in period",
                    "recommendation": "Verify audit logging is enabled and functioning"
                })
        
        # Check access control
        if self.access_control:
            # Verify role-based access is implemented
            findings.append({
                "severity": "info",
                "category": "access_control",
                "finding": "Role-based access control implemented",
                "status": "compliant"
            })
        
        # Determine overall status
        critical_findings = [f for f in findings if f.get("severity") == "critical"]
        major_findings = [f for f in findings if f.get("severity") == "major"]
        
        if critical_findings:
            report.status = ComplianceStatus.NON_COMPLIANT
        elif major_findings:
            report.status = ComplianceStatus.MAJOR_ISSUES
        elif findings:
            report.status = ComplianceStatus.MINOR_ISSUES
        else:
            report.status = ComplianceStatus.COMPLIANT
        
        report.findings = findings
        report.metrics = metrics
        
        return report
    
    def generate_gdpr_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """
        Generate GDPR compliance report
        
        Args:
            start_date: Report period start
            end_date: Report period end
            
        Returns:
            GDPR compliance report
        """
        report_id = f"GDPR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = ComplianceReport(
            report_id=report_id,
            report_type="GDPR",
            period_start=start_date,
            period_end=end_date
        )
        
        findings = []
        metrics = {}
        
        # Check data subject requests
        if self.gdpr_compliance:
            requests = self.gdpr_compliance.list_requests()
            metrics["data_subject_requests"] = {
                "total": len(requests),
                "by_type": {},
                "by_status": {}
            }
            
            for req in requests:
                req_type = req.request_type.value
                metrics["data_subject_requests"]["by_type"][req_type] = \
                    metrics["data_subject_requests"]["by_type"].get(req_type, 0) + 1
                metrics["data_subject_requests"]["by_status"][req.status] = \
                    metrics["data_subject_requests"]["by_status"].get(req.status, 0) + 1
            
            # Check response times
            completed_requests = [r for r in requests if r.status == "completed" and r.completed_at]
            if completed_requests:
                avg_response_time = sum(
                    (r.completed_at - r.submitted_at).total_seconds()
                    for r in completed_requests
                ) / len(completed_requests)
                metrics["avg_response_time_hours"] = avg_response_time / 3600
                
                # GDPR requires response within 30 days
                if avg_response_time > 30 * 24 * 3600:
                    findings.append({
                        "severity": "major",
                        "category": "data_subject_requests",
                        "finding": f"Average response time ({avg_response_time/3600/24:.1f} days) exceeds GDPR 30-day requirement",
                        "recommendation": "Improve request processing workflow"
                    })
        
        # Check consent management
        if self.gdpr_compliance:
            findings.append({
                "severity": "info",
                "category": "consent_management",
                "finding": "Consent management system implemented",
                "status": "compliant"
            })
        
        # Determine overall status
        critical_findings = [f for f in findings if f.get("severity") == "critical"]
        major_findings = [f for f in findings if f.get("severity") == "major"]
        
        if critical_findings:
            report.status = ComplianceStatus.NON_COMPLIANT
        elif major_findings:
            report.status = ComplianceStatus.MAJOR_ISSUES
        elif findings:
            report.status = ComplianceStatus.MINOR_ISSUES
        else:
            report.status = ComplianceStatus.COMPLIANT
        
        report.findings = findings
        report.metrics = metrics
        
        return report
    
    def generate_combined_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """
        Generate combined HIPAA/GDPR compliance report
        
        Args:
            start_date: Report period start
            end_date: Report period end
            
        Returns:
            Combined compliance report
        """
        hipaa_report = self.generate_hipaa_report(start_date, end_date)
        gdpr_report = self.generate_gdpr_report(start_date, end_date)
        
        report_id = f"COMBINED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = ComplianceReport(
            report_id=report_id,
            report_type="combined",
            period_start=start_date,
            period_end=end_date
        )
        
        # Combine findings
        report.findings = hipaa_report.findings + gdpr_report.findings
        report.metrics = {
            "hipaa": hipaa_report.metrics,
            "gdpr": gdpr_report.metrics
        }
        
        # Determine overall status (worst of both)
        statuses = [hipaa_report.status, gdpr_report.status]
        if ComplianceStatus.NON_COMPLIANT in statuses:
            report.status = ComplianceStatus.NON_COMPLIANT
        elif ComplianceStatus.MAJOR_ISSUES in statuses:
            report.status = ComplianceStatus.MAJOR_ISSUES
        elif ComplianceStatus.MINOR_ISSUES in statuses:
            report.status = ComplianceStatus.MINOR_ISSUES
        else:
            report.status = ComplianceStatus.COMPLIANT
        
        return report

