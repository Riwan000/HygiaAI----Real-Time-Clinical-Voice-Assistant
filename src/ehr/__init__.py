"""
EHR Integration Module

Handles:
- HL7 message parsing and generation
- FHIR resource creation and retrieval
- EHR system adapters
- Data exchange and interoperability
"""

from .hl7_adapter import HL7Adapter, HL7Message, HL7MessageType
from .fhir_adapter import FHIRAdapter, FHIRResource, FHIRResourceType
from .ehr_connector import EHRConnector, EHRSystem, ConnectionConfig
from .integration import EHRIntegration

__all__ = [
    "HL7Adapter",
    "HL7Message",
    "HL7MessageType",
    "FHIRAdapter",
    "FHIRResource",
    "FHIRResourceType",
    "EHRConnector",
    "EHRSystem",
    "ConnectionConfig",
    "EHRIntegration"
]

