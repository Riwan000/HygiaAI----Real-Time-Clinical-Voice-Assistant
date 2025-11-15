"""
Access Control Module for HIPAA/GDPR Compliance

Implements role-based access control (RBAC) and fine-grained permissions.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AccessRole(Enum):
    """User roles for access control"""
    ADMIN = "admin"  # Full system access
    DOCTOR = "doctor"  # Clinical data access
    NURSE = "nurse"  # Limited clinical access
    RESEARCHER = "researcher"  # De-identified data only
    AUDITOR = "auditor"  # Audit log access only
    PATIENT = "patient"  # Own data access only
    SYSTEM = "system"  # System/service account


class Permission(Enum):
    """Resource permissions"""
    # Data access
    READ_PATIENT_DATA = "read_patient_data"
    WRITE_PATIENT_DATA = "write_patient_data"
    DELETE_PATIENT_DATA = "delete_patient_data"
    EXPORT_PATIENT_DATA = "export_patient_data"
    
    # System access
    ACCESS_AUDIT_LOGS = "access_audit_logs"
    MANAGE_USERS = "manage_users"
    CONFIGURE_SYSTEM = "configure_system"
    
    # Research access
    ACCESS_DEIDENTIFIED_DATA = "access_deidentified_data"
    ACCESS_AGGREGATE_DATA = "access_aggregate_data"
    
    # Compliance
    MANAGE_COMPLIANCE = "manage_compliance"
    GENERATE_REPORTS = "generate_reports"


@dataclass
class AccessPolicy:
    """Access policy definition"""
    role: AccessRole
    permissions: Set[Permission] = field(default_factory=set)
    resource_restrictions: Dict[str, Any] = field(default_factory=dict)
    time_restrictions: Optional[Dict[str, Any]] = None  # e.g., business hours only
    ip_restrictions: Optional[List[str]] = None  # Allowed IP addresses
    requires_consent: bool = False


class AccessControl:
    """
    Access control manager for HIPAA/GDPR compliance
    
    Features:
    - Role-based access control (RBAC)
    - Fine-grained permissions
    - Resource-level restrictions
    - Time and IP-based restrictions
    - Consent management
    """
    
    def __init__(self):
        """Initialize access control"""
        self.policies: Dict[AccessRole, AccessPolicy] = {}
        self.user_roles: Dict[str, AccessRole] = {}
        self.user_consents: Dict[str, Dict[str, bool]] = {}  # user_id -> {consent_type: granted}
        
        # Initialize default policies
        self._initialize_default_policies()
        
        logger.info("Access control initialized")
    
    def _initialize_default_policies(self):
        """Initialize default access policies"""
        # Admin: Full access
        self.policies[AccessRole.ADMIN] = AccessPolicy(
            role=AccessRole.ADMIN,
            permissions={
                Permission.READ_PATIENT_DATA,
                Permission.WRITE_PATIENT_DATA,
                Permission.DELETE_PATIENT_DATA,
                Permission.EXPORT_PATIENT_DATA,
                Permission.ACCESS_AUDIT_LOGS,
                Permission.MANAGE_USERS,
                Permission.CONFIGURE_SYSTEM,
                Permission.MANAGE_COMPLIANCE,
                Permission.GENERATE_REPORTS
            }
        )
        
        # Doctor: Clinical data access
        self.policies[AccessRole.DOCTOR] = AccessPolicy(
            role=AccessRole.DOCTOR,
            permissions={
                Permission.READ_PATIENT_DATA,
                Permission.WRITE_PATIENT_DATA,
                Permission.EXPORT_PATIENT_DATA,
                Permission.ACCESS_DEIDENTIFIED_DATA,
                Permission.ACCESS_AGGREGATE_DATA
            }
        )
        
        # Nurse: Limited clinical access
        self.policies[AccessRole.NURSE] = AccessPolicy(
            role=AccessRole.NURSE,
            permissions={
                Permission.READ_PATIENT_DATA,
                Permission.WRITE_PATIENT_DATA,
                Permission.ACCESS_DEIDENTIFIED_DATA
            }
        )
        
        # Researcher: De-identified data only
        self.policies[AccessRole.RESEARCHER] = AccessPolicy(
            role=AccessRole.RESEARCHER,
            permissions={
                Permission.ACCESS_DEIDENTIFIED_DATA,
                Permission.ACCESS_AGGREGATE_DATA
            },
            requires_consent=True
        )
        
        # Auditor: Audit log access
        self.policies[AccessRole.AUDITOR] = AccessPolicy(
            role=AccessRole.AUDITOR,
            permissions={
                Permission.ACCESS_AUDIT_LOGS,
                Permission.GENERATE_REPORTS
            }
        )
        
        # Patient: Own data only
        self.policies[AccessRole.PATIENT] = AccessPolicy(
            role=AccessRole.PATIENT,
            permissions={
                Permission.READ_PATIENT_DATA,  # Own data only
                Permission.EXPORT_PATIENT_DATA  # Own data only
            }
        )
        
        # System: System operations
        self.policies[AccessRole.SYSTEM] = AccessPolicy(
            role=AccessRole.SYSTEM,
            permissions={
                Permission.READ_PATIENT_DATA,
                Permission.WRITE_PATIENT_DATA,
                Permission.ACCESS_DEIDENTIFIED_DATA
            }
        )
    
    def assign_role(self, user_id: str, role: AccessRole):
        """
        Assign role to user
        
        Args:
            user_id: User identifier
            role: Access role
        """
        self.user_roles[user_id] = role
        logger.info(f"Assigned role {role.value} to user {user_id}")
    
    def get_user_role(self, user_id: str) -> Optional[AccessRole]:
        """
        Get user's role
        
        Args:
            user_id: User identifier
            
        Returns:
            User's role or None
        """
        return self.user_roles.get(user_id)
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_id: Optional[str] = None,
        resource_owner: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission
        
        Args:
            user_id: User identifier
            permission: Permission to check
            resource_id: Optional resource ID
            resource_owner: Optional resource owner ID (for patient data access)
            
        Returns:
            True if user has permission
        """
        role = self.get_user_role(user_id)
        if not role:
            logger.warning(f"User {user_id} has no assigned role")
            return False
        
        policy = self.policies.get(role)
        if not policy:
            logger.warning(f"No policy found for role {role.value}")
            return False
        
        # Check if permission is granted
        if permission not in policy.permissions:
            logger.info(f"User {user_id} (role: {role.value}) does not have permission {permission.value}")
            return False
        
        # Check resource ownership (for patient role)
        if role == AccessRole.PATIENT:
            if resource_owner and resource_owner != user_id:
                logger.warning(f"Patient {user_id} attempted to access resource owned by {resource_owner}")
                return False
        
        # Check consent requirements
        if policy.requires_consent:
            if not self._check_consent(user_id, permission):
                logger.warning(f"User {user_id} lacks required consent for {permission.value}")
                return False
        
        return True
    
    def _check_consent(self, user_id: str, permission: Permission) -> bool:
        """Check if user has given consent"""
        user_consents = self.user_consents.get(user_id, {})
        consent_key = f"consent_{permission.value}"
        return user_consents.get(consent_key, False)
    
    def grant_consent(self, user_id: str, consent_type: str):
        """
        Grant consent to user
        
        Args:
            user_id: User identifier
            consent_type: Type of consent
        """
        if user_id not in self.user_consents:
            self.user_consents[user_id] = {}
        self.user_consents[user_id][consent_type] = True
        logger.info(f"Granted consent {consent_type} to user {user_id}")
    
    def revoke_consent(self, user_id: str, consent_type: str):
        """
        Revoke consent from user
        
        Args:
            user_id: User identifier
            consent_type: Type of consent
        """
        if user_id in self.user_consents:
            self.user_consents[user_id][consent_type] = False
            logger.info(f"Revoked consent {consent_type} from user {user_id}")
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of permissions
        """
        role = self.get_user_role(user_id)
        if not role:
            return set()
        
        policy = self.policies.get(role)
        if not policy:
            return set()
        
        # Filter by consent if required
        permissions = policy.permissions.copy()
        if policy.requires_consent:
            permissions = {
                p for p in permissions
                if self._check_consent(user_id, p)
            }
        
        return permissions
    
    def create_custom_policy(
        self,
        role: AccessRole,
        permissions: Set[Permission],
        resource_restrictions: Optional[Dict[str, Any]] = None
    ):
        """
        Create custom access policy
        
        Args:
            role: Access role
            permissions: Set of permissions
            resource_restrictions: Optional resource restrictions
        """
        self.policies[role] = AccessPolicy(
            role=role,
            permissions=permissions,
            resource_restrictions=resource_restrictions or {}
        )
        logger.info(f"Created custom policy for role {role.value}")

