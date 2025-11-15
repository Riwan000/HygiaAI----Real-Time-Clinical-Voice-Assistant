"""
FHIR Adapter for EHR Integration

Supports FHIR R4 resource creation, parsing, and exchange.
Handles Patient, Observation, Condition, Encounter, and DocumentReference resources.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Optional FHIR library
try:
    from fhir.resources.patient import Patient
    from fhir.resources.observation import Observation
    from fhir.resources.condition import Condition
    from fhir.resources.encounter import Encounter
    from fhir.resources.documentreference import DocumentReference
    from fhir.resources.humanname import HumanName
    from fhir.resources.identifier import Identifier
    from fhir.resources.codeableconcept import CodeableConcept
    from fhir.resources.coding import Coding
    from fhir.resources.reference import Reference
    from fhir.resources.period import Period
    from fhir.resources.quantity import Quantity
    FHIR_LIB_AVAILABLE = True
except ImportError:
    FHIR_LIB_AVAILABLE = False
    logger.warning(
        "fhir.resources library not available. Install with: pip install fhir.resources"
    )


class FHIRResourceType(Enum):
    """FHIR resource types"""
    PATIENT = "Patient"
    OBSERVATION = "Observation"
    CONDITION = "Condition"
    ENCOUNTER = "Encounter"
    DOCUMENT_REFERENCE = "DocumentReference"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    MEDICATION_REQUEST = "MedicationRequest"


@dataclass
class FHIRResource:
    """FHIR resource structure"""
    resource_type: FHIRResourceType
    id: Optional[str] = None
    resource_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    raw_json: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert to FHIR JSON format"""
        if self.raw_json:
            return self.raw_json
        
        resource_dict = {
            "resourceType": self.resource_type.value,
            **self.data
        }
        
        if self.id:
            resource_dict["id"] = self.id
        
        return json.dumps(resource_dict, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "FHIRResource":
        """Parse FHIR JSON format"""
        try:
            data = json.loads(json_str)
            resource_type_str = data.get("resourceType", "")
            
            try:
                resource_type = FHIRResourceType(resource_type_str)
            except ValueError:
                raise ValueError(f"Unknown FHIR resource type: {resource_type_str}")
            
            resource_id = data.get("id")
            
            # Remove resourceType and id from data
            resource_data = {k: v for k, v in data.items() if k not in ["resourceType", "id"]}
            
            return cls(
                resource_type=resource_type,
                id=resource_id,
                resource_id=resource_id,
                data=resource_data,
                raw_json=json_str
            )
        except Exception as e:
            logger.error(f"Error parsing FHIR JSON: {e}")
            raise


class FHIRAdapter:
    """
    FHIR Adapter for EHR Integration
    
    Features:
    - Create FHIR R4 resources
    - Parse FHIR JSON
    - Convert between FHIR and internal data models
    - Support for common resources (Patient, Observation, Condition, Encounter)
    """
    
    def __init__(self):
        """Initialize FHIR adapter"""
        if not FHIR_LIB_AVAILABLE:
            logger.warning(
                "fhir.resources library not available. Basic JSON handling will work, "
                "but advanced validation may be limited. Install with: pip install fhir.resources"
            )
        logger.info("FHIR adapter initialized")
    
    def create_patient(
        self,
        patient_id: str,
        name: str,
        date_of_birth: str,
        gender: str,
        identifiers: Optional[List[Dict[str, str]]] = None
    ) -> FHIRResource:
        """
        Create FHIR Patient resource
        
        Args:
            patient_id: Patient identifier
            name: Patient full name
            date_of_birth: Date of birth (YYYY-MM-DD)
            gender: Gender (male/female/other/unknown)
            identifiers: Optional list of identifier dictionaries
            
        Returns:
            FHIRResource Patient object
        """
        # Parse name
        name_parts = name.split()
        given_names = name_parts[:-1] if len(name_parts) > 1 else name_parts
        family_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        patient_data = {
            "name": [{
                "use": "official",
                "family": family_name,
                "given": given_names
            }],
            "gender": gender.lower(),
            "birthDate": date_of_birth,
        }
        
        # Add identifiers
        if identifiers:
            patient_data["identifier"] = identifiers
        else:
            patient_data["identifier"] = [{
                "use": "usual",
                "system": "http://hospital.example.org/patients",
                "value": patient_id
            }]
        
        return FHIRResource(
            resource_type=FHIRResourceType.PATIENT,
            id=patient_id,
            resource_id=patient_id,
            data=patient_data
        )
    
    def create_observation(
        self,
        patient_id: str,
        observation_code: str,
        observation_value: float,
        observation_date: datetime,
        code_system: str = "http://loinc.org",
        units: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> FHIRResource:
        """
        Create FHIR Observation resource
        
        Args:
            patient_id: Patient identifier
            observation_code: Observation code (e.g., LOINC code)
            observation_value: Observation value
            observation_date: Observation date/time
            code_system: Code system (default: LOINC)
            units: Optional units
            display_name: Optional display name for the code
            
        Returns:
            FHIRResource Observation object
        """
        observation_data = {
            "status": "final",
            "code": {
                "coding": [{
                    "system": code_system,
                    "code": observation_code,
                    "display": display_name or observation_code
                }]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": observation_date.isoformat(),
            "valueQuantity": {
                "value": observation_value,
                "unit": units or "",
                "system": "http://unitsofmeasure.org",
                "code": units or ""
            }
        }
        
        return FHIRResource(
            resource_type=FHIRResourceType.OBSERVATION,
            data=observation_data
        )
    
    def create_condition(
        self,
        patient_id: str,
        condition_code: str,
        condition_name: str,
        onset_date: datetime,
        code_system: str = "http://snomed.info/sct",
        status: str = "active"
    ) -> FHIRResource:
        """
        Create FHIR Condition resource
        
        Args:
            patient_id: Patient identifier
            condition_code: Condition code (e.g., SNOMED CT)
            condition_name: Condition name/display
            onset_date: Onset date/time
            code_system: Code system (default: SNOMED CT)
            status: Condition status (active/inactive/resolved)
            
        Returns:
            FHIRResource Condition object
        """
        condition_data = {
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": status,
                    "display": status.capitalize()
                }]
            },
            "code": {
                "coding": [{
                    "system": code_system,
                    "code": condition_code,
                    "display": condition_name
                }]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "onsetDateTime": onset_date.isoformat()
        }
        
        return FHIRResource(
            resource_type=FHIRResourceType.CONDITION,
            data=condition_data
        )
    
    def create_encounter(
        self,
        patient_id: str,
        encounter_type: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        status: str = "finished"
    ) -> FHIRResource:
        """
        Create FHIR Encounter resource
        
        Args:
            patient_id: Patient identifier
            encounter_type: Encounter type (e.g., "ambulatory", "emergency", "inpatient")
            start_date: Encounter start date/time
            end_date: Optional encounter end date/time
            status: Encounter status (planned/arrived/triaged/in-progress/onleave/finished/cancelled)
            
        Returns:
            FHIRResource Encounter object
        """
        encounter_data = {
            "status": status,
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": encounter_type,
                "display": encounter_type.capitalize()
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "period": {
                "start": start_date.isoformat()
            }
        }
        
        if end_date:
            encounter_data["period"]["end"] = end_date.isoformat()
        
        return FHIRResource(
            resource_type=FHIRResourceType.ENCOUNTER,
            data=encounter_data
        )
    
    def parse_resource(self, json_str: str) -> FHIRResource:
        """
        Parse FHIR JSON resource
        
        Args:
            json_str: FHIR JSON string
            
        Returns:
            Parsed FHIRResource object
        """
        return FHIRResource.from_json(json_str)
    
    def convert_to_internal_format(self, resource: FHIRResource) -> Dict[str, Any]:
        """
        Convert FHIR resource to internal data format
        
        Args:
            resource: FHIRResource object
            
        Returns:
            Dictionary in internal format
        """
        result = {
            "resource_type": resource.resource_type.value,
            "resource_id": resource.id or resource.resource_id,
            "data": resource.data
        }
        
        # Extract common fields based on resource type
        if resource.resource_type == FHIRResourceType.PATIENT:
            data = resource.data
            result["patient_id"] = resource.id
            if "name" in data and len(data["name"]) > 0:
                name_obj = data["name"][0]
                given = name_obj.get("given", [])
                family = name_obj.get("family", "")
                result["patient_name"] = " ".join(given + [family]) if family else " ".join(given)
            result["date_of_birth"] = data.get("birthDate")
            result["gender"] = data.get("gender")
        
        elif resource.resource_type == FHIRResourceType.OBSERVATION:
            data = resource.data
            result["observation_code"] = data.get("code", {}).get("coding", [{}])[0].get("code") if data.get("code") else None
            result["observation_value"] = data.get("valueQuantity", {}).get("value") if data.get("valueQuantity") else None
            result["units"] = data.get("valueQuantity", {}).get("unit") if data.get("valueQuantity") else None
            result["timestamp"] = data.get("effectiveDateTime")
            # Extract patient reference
            subject = data.get("subject", {})
            if isinstance(subject, dict) and "reference" in subject:
                ref = subject["reference"]
                if ref.startswith("Patient/"):
                    result["patient_id"] = ref.replace("Patient/", "")
        
        elif resource.resource_type == FHIRResourceType.CONDITION:
            data = resource.data
            result["condition_code"] = data.get("code", {}).get("coding", [{}])[0].get("code") if data.get("code") else None
            result["condition_name"] = data.get("code", {}).get("coding", [{}])[0].get("display") if data.get("code") else None
            result["status"] = data.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") if data.get("clinicalStatus") else None
            result["onset_date"] = data.get("onsetDateTime")
            # Extract patient reference
            subject = data.get("subject", {})
            if isinstance(subject, dict) and "reference" in subject:
                ref = subject["reference"]
                if ref.startswith("Patient/"):
                    result["patient_id"] = ref.replace("Patient/", "")
        
        elif resource.resource_type == FHIRResourceType.ENCOUNTER:
            data = resource.data
            result["encounter_type"] = data.get("class", {}).get("code") if data.get("class") else None
            result["status"] = data.get("status")
            period = data.get("period", {})
            result["start_date"] = period.get("start")
            result["end_date"] = period.get("end")
            # Extract patient reference
            subject = data.get("subject", {})
            if isinstance(subject, dict) and "reference" in subject:
                ref = subject["reference"]
                if ref.startswith("Patient/"):
                    result["patient_id"] = ref.replace("Patient/", "")
        
        return result

