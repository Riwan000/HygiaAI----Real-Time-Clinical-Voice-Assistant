"""
EHR Integration Layer

Integrates EHR adapters with HygiaAI's internal data models and Qdrant storage.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .ehr_connector import EHRConnector, ConnectionConfig, EHRSystem
from .hl7_adapter import HL7Adapter, HL7Message
from .fhir_adapter import FHIRAdapter, FHIRResource
from src.storage import QdrantStorage
from src.models.case_models import Case, CaseMetadata, CaseModality

logger = logging.getLogger(__name__)


class EHRIntegration:
    """
    EHR Integration Service
    
    Features:
    - Import patient data from EHR systems
    - Export HygiaAI cases to EHR systems
    - Sync data between EHR and HygiaAI
    - Convert between EHR formats and internal models
    """
    
    def __init__(
        self,
        ehr_connector: EHRConnector,
        qdrant_storage: Optional[QdrantStorage] = None
    ):
        """
        Initialize EHR integration
        
        Args:
            ehr_connector: EHRConnector instance
            qdrant_storage: Optional QdrantStorage for storing imported data
        """
        self.connector = ehr_connector
        self.storage = qdrant_storage
        self.hl7_adapter = HL7Adapter()
        self.fhir_adapter = FHIRAdapter()
        
        logger.info("EHR integration initialized")
    
    def import_patient_from_hl7(self, hl7_message: str) -> Dict[str, Any]:
        """
        Import patient data from HL7 message
        
        Args:
            hl7_message: HL7 message string
            
        Returns:
            Dictionary with imported patient data in internal format
        """
        try:
            message = self.hl7_adapter.parse_message(hl7_message)
            internal_data = self.hl7_adapter.convert_to_internal_format(message)
            
            logger.info(f"Imported patient data from HL7: {internal_data.get('patient_id')}")
            return internal_data
        except Exception as e:
            logger.error(f"Error importing from HL7: {e}")
            raise
    
    def import_patient_from_fhir(self, fhir_json: str) -> Dict[str, Any]:
        """
        Import patient data from FHIR resource
        
        Args:
            fhir_json: FHIR JSON string
            
        Returns:
            Dictionary with imported patient data in internal format
        """
        try:
            resource = self.fhir_adapter.parse_resource(fhir_json)
            internal_data = self.fhir_adapter.convert_to_internal_format(resource)
            
            logger.info(f"Imported patient data from FHIR: {internal_data.get('resource_id')}")
            return internal_data
        except Exception as e:
            logger.error(f"Error importing from FHIR: {e}")
            raise
    
    def export_case_to_ehr(self, case: Case) -> bool:
        """
        Export HygiaAI case to EHR system
        
        Args:
            case: Case object to export
            
        Returns:
            True if export successful
        """
        try:
            # Convert case to EHR format
            case_data = {
                "patient_id": case.patient_id,
                "patient_name": case.metadata.get("patient_name", ""),
                "date_of_birth": case.metadata.get("date_of_birth", ""),
                "gender": case.metadata.get("gender", "unknown"),
                "diagnosis": case.metadata.diagnosis,
                "timestamp": case.metadata.timestamp.isoformat() if isinstance(case.metadata.timestamp, datetime) else str(case.metadata.timestamp),
                "observations": []
            }
            
            # Extract observations from modalities
            if "text" in case.modalities:
                text_mod = case.modalities["text"]
                if isinstance(text_mod.content, dict):
                    entities = text_mod.content.get("entities", [])
                    for entity in entities:
                        if entity.get("entity_type") == "vital":
                            case_data["observations"].append({
                                "code": entity.get("text", ""),
                                "value": entity.get("value", ""),
                                "units": entity.get("units", ""),
                                "timestamp": case_data["timestamp"]
                            })
            
            # Send to EHR based on system type
            if self.connector.config.system in [EHRSystem.EPIC, EHRSystem.CERNER, EHRSystem.ATHENAHEALTH]:
                # Use FHIR
                fhir_resources = self.connector.convert_case_to_fhir(case_data)
                for resource in fhir_resources:
                    if not self.connector.send_fhir_resource(resource):
                        logger.warning(f"Failed to send FHIR resource: {resource.resource_type.value}")
                        return False
                logger.info(f"Exported case {case.case_id} to EHR via FHIR")
                return True
            else:
                # Use HL7
                hl7_message = self.connector.convert_case_to_hl7(case_data)
                ack = self.connector.send_hl7_message(hl7_message)
                if ack:
                    logger.info(f"Exported case {case.case_id} to EHR via HL7")
                    return True
                else:
                    logger.warning(f"Failed to send HL7 message for case {case.case_id}")
                    return False
        except Exception as e:
            logger.error(f"Error exporting case to EHR: {e}")
            return False
    
    def sync_patient_data(
        self,
        patient_id: str,
        resource_type: str = "Patient"
    ) -> Optional[Dict[str, Any]]:
        """
        Sync patient data from EHR to HygiaAI
        
        Args:
            patient_id: Patient identifier
            resource_type: FHIR resource type to sync (default: Patient)
            
        Returns:
            Dictionary with synced patient data, None if failed
        """
        try:
            if not self.connector.is_connected():
                if not self.connector.connect():
                    logger.error("Failed to connect to EHR system")
                    return None
            
            # Get patient resource from EHR
            if self.connector.config.system in [EHRSystem.EPIC, EHRSystem.CERNER, EHRSystem.ATHENAHEALTH]:
                # Use FHIR
                resource = self.connector.get_fhir_resource(resource_type, patient_id)
                if resource:
                    internal_data = self.fhir_adapter.convert_to_internal_format(resource)
                    logger.info(f"Synced patient {patient_id} from EHR")
                    return internal_data
            else:
                # Use HL7 - would need to query EHR system
                logger.warning("HL7 patient query not implemented yet")
                return None
            
            return None
        except Exception as e:
            logger.error(f"Error syncing patient data: {e}")
            return None
    
    def store_imported_data(
        self,
        imported_data: Dict[str, Any],
        embedding: List[float]
    ) -> Optional[str]:
        """
        Store imported EHR data in Qdrant
        
        Args:
            imported_data: Imported patient data dictionary
            embedding: Vector embedding for the data
            
        Returns:
            Stored point ID if successful, None otherwise
        """
        if not self.storage:
            logger.warning("Qdrant storage not configured, cannot store imported data")
            return None
        
        try:
            # Prepare transcript data
            transcript_data = {
                "transcript": imported_data.get("transcript", ""),
                "diagnosis": imported_data.get("diagnosis"),
                "outcome": imported_data.get("outcome"),
                "medical_entities": imported_data.get("medical_entities", [])
            }
            
            # Prepare metadata
            metadata = {
                "session_id": f"ehr-import-{imported_data.get('patient_id', 'unknown')}",
                "patient_id": imported_data.get("patient_id"),
                "doctor_id": imported_data.get("doctor_id"),
                "timestamp": imported_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "modality": "text"
            }
            
            # Store in Qdrant
            point_id = self.storage.store_transcript(
                transcript_data=transcript_data,
                embedding=embedding,
                metadata=metadata
            )
            
            logger.info(f"Stored imported EHR data: {point_id}")
            return point_id
        except Exception as e:
            logger.error(f"Error storing imported data: {e}")
            return None

