"""
Audit Logging Module for HIPAA/GDPR Compliance

Provides comprehensive audit logging for all data access, modifications, and system events.
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    # Data access events
    DATA_ACCESS = "data_access"
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILURE = "login_failure"
    PASSWORD_CHANGE = "password_change"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGE = "config_change"
    
    # Compliance events
    DEIDENTIFICATION = "deidentification"
    ENCRYPTION = "encryption"
    DECRYPTION = "decryption"
    AUDIT_LOG_ACCESS = "audit_log_access"
    
    # GDPR events
    DATA_SUBJECT_REQUEST = "data_subject_request"
    DATA_DELETION_REQUEST = "data_deletion_request"
    DATA_PORTABILITY_REQUEST = "data_portability_request"
    
    # Breach events
    BREACH_DETECTED = "breach_detected"
    BREACH_NOTIFICATION = "breach_notification"
    
    # Knowledge ingestion events
    KNOWLEDGE_INGESTION = "knowledge_ingestion"
    KNOWLEDGE_INGESTION_FAILED = "knowledge_ingestion_failed"
    KNOWLEDGE_ACCESS_VALIDATION = "knowledge_access_validation"


class AuditLevel(Enum):
    """Audit severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    resource_type: Optional[str] = None  # e.g., "patient", "case", "transcript"
    resource_id: Optional[str] = None
    action: str = ""
    result: str = "success"  # success, failure, denied
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: AuditLevel = AuditLevel.INFO
    compliance_flags: List[str] = field(default_factory=list)  # e.g., ["HIPAA", "GDPR"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enum to value
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        # Convert datetime to ISO format
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    def calculate_hash(self) -> str:
        """Calculate hash for tamper detection"""
        # Create hash of event data (excluding hash itself)
        event_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()


class AuditLogger:
    """
    Comprehensive audit logger for HIPAA/GDPR compliance
    
    Features:
    - Immutable audit logs
    - Tamper detection via hashing
    - Encrypted log storage
    - Compliance reporting
    - Log retention policies
    """
    
    def __init__(
        self,
        log_directory: str = "logs/audit",
        enable_encryption: bool = True,
        encryption_key: Optional[str] = None,
        retention_days: int = 2555  # 7 years for HIPAA
    ):
        """
        Initialize audit logger
        
        Args:
            log_directory: Directory to store audit logs
            enable_encryption: Encrypt audit logs
            encryption_key: Optional encryption key
            retention_days: Log retention period in days
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        self.enable_encryption = enable_encryption
        self.retention_days = retention_days
        
        # Initialize encryption if enabled
        if enable_encryption:
            from src.storage.encryption import EncryptionManager
            self.encryption_manager = EncryptionManager(encryption_key)
        else:
            self.encryption_manager = None
        
        # Event counter for unique IDs
        self._event_counter = 0
        
        logger.info(f"Audit logger initialized: {log_directory}")
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: str = "",
        result: str = "success",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditLevel = AuditLevel.INFO,
        compliance_flags: Optional[List[str]] = None
    ) -> AuditEvent:
        """
        Log an audit event
        
        Args:
            event_type: Type of audit event
            user_id: User ID performing the action
            user_role: Role of the user
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            action: Action performed
            result: Result of action (success/failure/denied)
            ip_address: IP address of user
            user_agent: User agent string
            details: Additional event details
            severity: Severity level
            compliance_flags: Compliance standards applicable
            
        Returns:
            Created AuditEvent object
        """
        self._event_counter += 1
        event_id = f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._event_counter:06d}"
        
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            severity=severity,
            compliance_flags=compliance_flags or []
        )
        
        # Calculate hash for tamper detection
        event_hash = event.calculate_hash()
        event.details["_hash"] = event_hash
        
        # Write to log file
        self._write_event(event)
        
        # Log to standard logger as well
        log_message = f"Audit: {event_type.value} | User: {user_id} | Resource: {resource_type}/{resource_id} | Result: {result}"
        if severity == AuditLevel.CRITICAL:
            logger.critical(log_message)
        elif severity == AuditLevel.ERROR:
            logger.error(log_message)
        elif severity == AuditLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return event
    
    def _write_event(self, event: AuditEvent):
        """Write event to log file"""
        try:
            # Create daily log file
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            log_file = self.log_directory / f"audit-{date_str}.jsonl"
            
            # Prepare event data
            event_data = event.to_dict()
            event_json = json.dumps(event_data)
            
            # Encrypt if enabled
            if self.enable_encryption and self.encryption_manager:
                event_json = self.encryption_manager.encrypt(event_json)
                # Add encryption marker
                event_json = f"ENCRYPTED:{event_json}"
            
            # Append to log file (JSONL format)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event_json + "\n")
            
        except Exception as e:
            logger.error(f"Error writing audit event: {e}")
            # Fallback: log to standard logger
            logger.error(f"Failed audit event: {event.to_json()}")
    
    def query_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: Optional[str] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """
        Query audit events
        
        Args:
            start_date: Start date for query
            end_date: End date for query
            event_type: Filter by event type
            user_id: Filter by user ID
            resource_id: Filter by resource ID
            result: Filter by result (success/failure/denied)
            limit: Maximum number of events to return
            
        Returns:
            List of matching AuditEvent objects
        """
        events = []
        
        # Determine date range
        if not start_date:
            start_date = datetime.now(timezone.utc).replace(day=1)  # Start of month
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Iterate through date range
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only and len(events) < limit:
            date_str = current_date.strftime("%Y-%m-%d")
            log_file = self.log_directory / f"audit-{date_str}.jsonl"
            
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if len(events) >= limit:
                                break
                            
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Decrypt if encrypted
                            if line.startswith("ENCRYPTED:"):
                                encrypted_data = line.replace("ENCRYPTED:", "")
                                if self.enable_encryption and self.encryption_manager:
                                    try:
                                        line = self.encryption_manager.decrypt(encrypted_data)
                                    except Exception as e:
                                        logger.warning(f"Failed to decrypt audit log entry: {e}")
                                        continue
                            
                            # Parse JSON
                            try:
                                event_data = json.loads(line)
                                
                                # Convert timestamp
                                if isinstance(event_data.get("timestamp"), str):
                                    event_timestamp = datetime.fromisoformat(event_data["timestamp"].replace('Z', '+00:00'))
                                else:
                                    continue
                                
                                # Apply filters
                                if start_date and event_timestamp < start_date:
                                    continue
                                if end_date and event_timestamp > end_date:
                                    continue
                                if event_type and event_data.get("event_type") != event_type.value:
                                    continue
                                if user_id and event_data.get("user_id") != user_id:
                                    continue
                                if resource_id and event_data.get("resource_id") != resource_id:
                                    continue
                                if result and event_data.get("result") != result:
                                    continue
                                
                                # Reconstruct event
                                event = AuditEvent(
                                    event_id=event_data.get("event_id", ""),
                                    event_type=AuditEventType(event_data.get("event_type", "data_access")),
                                    timestamp=event_timestamp,
                                    user_id=event_data.get("user_id"),
                                    user_role=event_data.get("user_role"),
                                    resource_type=event_data.get("resource_type"),
                                    resource_id=event_data.get("resource_id"),
                                    action=event_data.get("action", ""),
                                    result=event_data.get("result", "success"),
                                    ip_address=event_data.get("ip_address"),
                                    user_agent=event_data.get("user_agent"),
                                    details=event_data.get("details", {}),
                                    severity=AuditLevel(event_data.get("severity", "info")),
                                    compliance_flags=event_data.get("compliance_flags", [])
                                )
                                
                                # Verify hash (tamper detection)
                                stored_hash = event.details.pop("_hash", None)
                                if stored_hash:
                                    calculated_hash = event.calculate_hash()
                                    if stored_hash != calculated_hash:
                                        logger.warning(f"Audit log tampering detected for event {event.event_id}")
                                        event.details["_tampered"] = True
                                
                                events.append(event)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse audit log entry: {e}")
                                continue
                except Exception as e:
                    logger.error(f"Error reading audit log file {log_file}: {e}")
            
            # Move to next day
            from datetime import timedelta
            current_date += timedelta(days=1)
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        compliance_standard: str = "HIPAA"  # HIPAA, GDPR, or both
    ) -> Dict[str, Any]:
        """
        Generate compliance report
        
        Args:
            start_date: Start date for report
            end_date: End date for report
            compliance_standard: Compliance standard (HIPAA, GDPR, or both)
            
        Returns:
            Compliance report dictionary
        """
        events = self.query_events(start_date=start_date, end_date=end_date)
        
        # Filter by compliance standard
        if compliance_standard.lower() == "hipaa":
            events = [e for e in events if "HIPAA" in e.compliance_flags or not e.compliance_flags]
        elif compliance_standard.lower() == "gdpr":
            events = [e for e in events if "GDPR" in e.compliance_flags or not e.compliance_flags]
        
        # Generate statistics
        total_events = len(events)
        event_types = {}
        user_activities = {}
        resource_access = {}
        failed_actions = 0
        denied_actions = 0
        
        for event in events:
            # Count by event type
            event_type = event.event_type.value
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Count by user
            if event.user_id:
                if event.user_id not in user_activities:
                    user_activities[event.user_id] = {"total": 0, "by_type": {}}
                user_activities[event.user_id]["total"] += 1
                user_activities[event.user_id]["by_type"][event_type] = user_activities[event.user_id]["by_type"].get(event_type, 0) + 1
            
            # Count by resource
            if event.resource_type:
                resource_key = f"{event.resource_type}/{event.resource_id or 'unknown'}"
                resource_access[resource_key] = resource_access.get(resource_key, 0) + 1
            
            # Count failures and denials
            if event.result == "failure":
                failed_actions += 1
            elif event.result == "denied":
                denied_actions += 1
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "compliance_standard": compliance_standard,
            "summary": {
                "total_events": total_events,
                "failed_actions": failed_actions,
                "denied_actions": denied_actions,
                "success_rate": (total_events - failed_actions - denied_actions) / total_events if total_events > 0 else 0
            },
            "event_types": event_types,
            "user_activities": user_activities,
            "resource_access": resource_access,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def cleanup_old_logs(self):
        """Clean up audit logs older than retention period"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            
            for log_file in self.log_directory.glob("audit-*.jsonl"):
                # Extract date from filename
                try:
                    date_str = log_file.stem.replace("audit-", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        logger.info(f"Deleted old audit log: {log_file}")
                except Exception as e:
                    logger.warning(f"Error processing log file {log_file}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")

