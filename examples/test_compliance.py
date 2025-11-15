#!/usr/bin/env python3
"""
Test Privacy Compliance Features

Tests audit logging, access control, GDPR compliance, and breach detection.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.compliance import (
    AuditLogger,
    AuditEventType,
    AuditLevel,
    AccessControl,
    AccessRole,
    Permission,
    GDPRCompliance,
    RequestType,
    ComplianceReporter,
    BreachDetector,
    BreachSeverity,
    EnhancedDeIdentificationManager
)
from src.storage.qdrant_storage import QdrantStorage

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test compliance features"""
    print("=" * 80)
    print("  Privacy Compliance Test")
    print("=" * 80)
    
    # Test 1: Enhanced De-identification
    print_section("Test 1: Enhanced De-identification")
    deid_manager = EnhancedDeIdentificationManager(method="safe_harbor")
    
    test_text = """
    Patient John Doe (DOB: 01/15/1980, SSN: 123-45-6789) visited Dr. Smith
    at 123 Main Street, New York, NY 10001. Contact: john.doe@email.com, 
    Phone: 555-123-4567. Medical Record #MRN-12345.
    """
    
    print("Original text:")
    print(test_text)
    
    deidentified = deid_manager.deidentify_text(test_text)
    print("\nDe-identified text:")
    print(deidentified)
    
    # Validate de-identification
    validation = deid_manager.validate_deidentification(test_text, deidentified)
    print(f"\nValidation:")
    print(f"  Valid: {validation['is_valid']}")
    print(f"  Remaining PHI: {validation['remaining_phi_types']}")
    print(f"  Recommendation: {validation['recommendation']}")
    
    # Test 2: Audit Logging
    print_section("Test 2: Audit Logging")
    audit_logger = AuditLogger(log_directory="logs/audit", enable_encryption=False)
    
    # Log some events
    event1 = audit_logger.log_event(
        event_type=AuditEventType.DATA_READ,
        user_id="doctor001",
        user_role="doctor",
        resource_type="patient",
        resource_id="PAT001",
        action="read_patient_data",
        result="success",
        compliance_flags=["HIPAA"]
    )
    print(f"✓ Logged event: {event1.event_id}")
    
    event2 = audit_logger.log_event(
        event_type=AuditEventType.DATA_WRITE,
        user_id="doctor001",
        user_role="doctor",
        resource_type="case",
        resource_id="CASE001",
        action="create_case",
        result="success",
        compliance_flags=["HIPAA", "GDPR"]
    )
    print(f"✓ Logged event: {event2.event_id}")
    
    # Query events
    events = audit_logger.query_events(
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        limit=10
    )
    print(f"\n✓ Queried {len(events)} audit events")
    
    # Generate compliance report
    report = audit_logger.generate_compliance_report(
        start_date=datetime.now(timezone.utc) - timedelta(days=7),
        end_date=datetime.now(timezone.utc),
        compliance_standard="HIPAA"
    )
    print(f"\n✓ Generated compliance report:")
    print(f"  Total events: {report['summary']['total_events']}")
    print(f"  Success rate: {report['summary']['success_rate']:.2%}")
    
    # Test 3: Access Control
    print_section("Test 3: Access Control")
    access_control = AccessControl()
    
    # Assign roles
    access_control.assign_role("doctor001", AccessRole.DOCTOR)
    access_control.assign_role("nurse001", AccessRole.NURSE)
    access_control.assign_role("researcher001", AccessRole.RESEARCHER)
    print("✓ Assigned roles to users")
    
    # Check permissions
    can_read = access_control.check_permission("doctor001", Permission.READ_PATIENT_DATA)
    print(f"✓ Doctor can read patient data: {can_read}")
    
    can_manage = access_control.check_permission("doctor001", Permission.MANAGE_USERS)
    print(f"✓ Doctor can manage users: {can_manage}")
    
    can_research = access_control.check_permission("researcher001", Permission.ACCESS_DEIDENTIFIED_DATA)
    print(f"✓ Researcher can access de-identified data: {can_research}")
    
    # Test 4: GDPR Compliance
    print_section("Test 4: GDPR Compliance")
    storage = QdrantStorage(
        host="localhost",
        port=6333,
        enable_encryption=False,
        enable_deidentification=False
    )
    
    gdpr = GDPRCompliance(
        storage_backend=storage,
        audit_logger=audit_logger
    )
    
    # Submit data subject request
    request = gdpr.submit_data_subject_request(
        data_subject_id="PAT001",
        request_type=RequestType.ACCESS
    )
    print(f"✓ Submitted data subject request: {request.request_id}")
    
    # Process access request (would normally collect real data)
    try:
        access_data = gdpr.process_access_request(request.request_id)
        print(f"✓ Processed access request")
        print(f"  Data categories: {list(access_data.get('data_categories', {}).keys())}")
    except Exception as e:
        print(f"⚠ Access request processing: {e}")
    
    # Record consent
    gdpr.record_consent(
        data_subject_id="PAT001",
        consent_type="research",
        granted=True,
        purpose="Medical research"
    )
    print(f"✓ Recorded consent for PAT001")
    
    has_consent = gdpr.check_consent("PAT001", "research")
    print(f"✓ Consent check: {has_consent}")
    
    # Test 5: Compliance Reporting
    print_section("Test 5: Compliance Reporting")
    reporter = ComplianceReporter(
        audit_logger=audit_logger,
        access_control=access_control,
        gdpr_compliance=gdpr
    )
    
    hipaa_report = reporter.generate_hipaa_report(
        start_date=datetime.now(timezone.utc) - timedelta(days=30),
        end_date=datetime.now(timezone.utc)
    )
    print(f"✓ Generated HIPAA report: {hipaa_report.report_id}")
    print(f"  Status: {hipaa_report.status.value}")
    print(f"  Findings: {len(hipaa_report.findings)}")
    
    gdpr_report = reporter.generate_gdpr_report(
        start_date=datetime.now(timezone.utc) - timedelta(days=30),
        end_date=datetime.now(timezone.utc)
    )
    print(f"✓ Generated GDPR report: {gdpr_report.report_id}")
    print(f"  Status: {gdpr_report.status.value}")
    
    # Test 6: Breach Detection
    print_section("Test 6: Breach Detection")
    breach_detector = BreachDetector(audit_logger=audit_logger)
    
    breach = breach_detector.detect_breach(
        breach_type="unauthorized_access",
        description="Unauthorized access attempt detected",
        severity=BreachSeverity.HIGH,
        affected_data_subjects=["PAT001"],
        affected_data_types=["clinical_data"]
    )
    print(f"✓ Detected breach: {breach.breach_id}")
    print(f"  Type: {breach.breach_type}")
    print(f"  Severity: {breach.severity.value}")
    print(f"  Notification sent: {breach.notification_sent}")
    
    # Contain breach
    breach_detector.contain_breach(breach.breach_id)
    print(f"✓ Breach contained")
    
    # Resolve breach
    breach_detector.resolve_breach(breach.breach_id, "Access revoked, system secured")
    print(f"✓ Breach resolved")
    
    print("\n" + "=" * 80)
    print("  All Compliance Tests Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()

