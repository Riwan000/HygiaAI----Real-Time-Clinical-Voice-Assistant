"""
EHR Connector for Common EHR Systems

Provides unified interface for connecting to various EHR systems
using HL7 and FHIR standards.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .hl7_adapter import HL7Adapter, HL7Message
from .fhir_adapter import FHIRAdapter, FHIRResource

logger = logging.getLogger(__name__)


class EHRSystem(Enum):
    """Supported EHR systems"""
    EPIC = "epic"
    CERNER = "cerner"
    ALLSCRIPTS = "allscripts"
    ATHENAHEALTH = "athenahealth"
    NEXTGEN = "nextgen"
    ECLINICALWORKS = "eclinicalworks"
    GENERIC_HL7 = "generic_hl7"
    GENERIC_FHIR = "generic_fhir"


@dataclass
class ConnectionConfig:
    """EHR connection configuration"""
    system: EHRSystem
    host: str
    port: int = 443
    use_ssl: bool = True
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    fhir_base_url: Optional[str] = None
    hl7_endpoint: Optional[str] = None
    timeout: int = 30
    additional_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_config is None:
            self.additional_config = {}


class EHRConnector:
    """
    Unified EHR Connector
    
    Features:
    - Connect to various EHR systems
    - Send/receive HL7 messages
    - Send/receive FHIR resources
    - Convert between EHR formats and internal format
    - Handle authentication and connection management
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize EHR connector
        
        Args:
            config: Connection configuration
        """
        self.config = config
        self.hl7_adapter = HL7Adapter()
        self.fhir_adapter = FHIRAdapter()
        self._connected = False
        
        logger.info(f"EHR connector initialized for {config.system.value}")
    
    def connect(self) -> bool:
        """
        Establish connection to EHR system
        
        Returns:
            True if connection successful
        """
        try:
            # System-specific connection logic would go here
            # For now, we'll simulate connection
            
            if self.config.system in [EHRSystem.EPIC, EHRSystem.CERNER, EHRSystem.ATHENAHEALTH]:
                # These typically use FHIR
                if not self.config.fhir_base_url:
                    logger.error(f"FHIR base URL required for {self.config.system.value}")
                    return False
                # In production, would validate FHIR endpoint
                self._connected = True
                logger.info(f"Connected to {self.config.system.value} via FHIR")
            
            elif self.config.system in [EHRSystem.ALLSCRIPTS, EHRSystem.NEXTGEN, EHRSystem.ECLINICALWORKS]:
                # These typically use HL7
                if not self.config.hl7_endpoint:
                    logger.error(f"HL7 endpoint required for {self.config.system.value}")
                    return False
                # In production, would validate HL7 endpoint
                self._connected = True
                logger.info(f"Connected to {self.config.system.value} via HL7")
            
            else:
                # Generic connection
                self._connected = True
                logger.info(f"Connected to {self.config.system.value}")
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to EHR: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from EHR system"""
        self._connected = False
        logger.info("Disconnected from EHR system")
    
    def is_connected(self) -> bool:
        """Check if connected to EHR system"""
        return self._connected
    
    def send_hl7_message(self, message: HL7Message) -> Optional[HL7Message]:
        """
        Send HL7 message to EHR system
        
        Args:
            message: HL7Message to send
            
        Returns:
            Acknowledgment message if received, None otherwise
        """
        if not self._connected:
            logger.error("Not connected to EHR system")
            return None
        
        try:
            # In production, would send via MLLP or HTTP
            # For now, simulate sending and return acknowledgment
            logger.info(f"Sending HL7 message: {message.message_type.value}")
            
            # Create acknowledgment
            ack = self.hl7_adapter.create_acknowledgment(message, acknowledgment_code="AA")
            return ack
        except Exception as e:
            logger.error(f"Error sending HL7 message: {e}")
            return None
    
    def receive_hl7_message(self) -> Optional[HL7Message]:
        """
        Receive HL7 message from EHR system
        
        Returns:
            Received HL7Message if available, None otherwise
        """
        if not self._connected:
            logger.error("Not connected to EHR system")
            return None
        
        # In production, would listen for incoming messages
        # For now, return None (no messages available)
        return None
    
    def send_fhir_resource(self, resource: FHIRResource) -> bool:
        """
        Send FHIR resource to EHR system
        
        Args:
            resource: FHIRResource to send
            
        Returns:
            True if successful
        """
        if not self._connected:
            logger.error("Not connected to EHR system")
            return False
        
        try:
            # In production, would POST to FHIR endpoint
            # POST {fhir_base_url}/{resourceType}
            logger.info(f"Sending FHIR resource: {resource.resource_type.value}")
            
            # Simulate successful send
            return True
        except Exception as e:
            logger.error(f"Error sending FHIR resource: {e}")
            return False
    
    def get_fhir_resource(
        self,
        resource_type: str,
        resource_id: str
    ) -> Optional[FHIRResource]:
        """
        Get FHIR resource from EHR system
        
        Args:
            resource_type: FHIR resource type (e.g., "Patient", "Observation")
            resource_id: Resource ID
            
        Returns:
            FHIRResource if found, None otherwise
        """
        if not self._connected:
            logger.error("Not connected to EHR system")
            return None
        
        try:
            # In production, would GET from FHIR endpoint
            # GET {fhir_base_url}/{resourceType}/{id}
            logger.info(f"Getting FHIR resource: {resource_type}/{resource_id}")
            
            # Simulate resource retrieval
            return None
        except Exception as e:
            logger.error(f"Error getting FHIR resource: {e}")
            return None
    
    def search_fhir_resources(
        self,
        resource_type: str,
        search_params: Dict[str, Any]
    ) -> List[FHIRResource]:
        """
        Search FHIR resources
        
        Args:
            resource_type: FHIR resource type
            search_params: Search parameters (e.g., {"patient": "Patient/123"})
            
        Returns:
            List of matching FHIRResource objects
        """
        if not self._connected:
            logger.error("Not connected to EHR system")
            return []
        
        try:
            # In production, would GET from FHIR endpoint with search parameters
            # GET {fhir_base_url}/{resourceType}?{search_params}
            logger.info(f"Searching FHIR resources: {resource_type} with params {search_params}")
            
            # Simulate search
            return []
        except Exception as e:
            logger.error(f"Error searching FHIR resources: {e}")
            return []
    
    def convert_case_to_hl7(self, case_data: Dict[str, Any]) -> HL7Message:
        """
        Convert internal case data to HL7 message
        
        Args:
            case_data: Internal case data dictionary
            
        Returns:
            HL7Message object
        """
        # Extract patient information
        patient_id = case_data.get("patient_id", "")
        patient_name = case_data.get("patient_name", "Unknown")
        date_of_birth = case_data.get("date_of_birth", "")
        gender = case_data.get("gender", "U")
        
        # Extract diagnosis
        diagnosis = case_data.get("diagnosis")
        
        # Extract timestamp
        timestamp_str = case_data.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        # Create ADT message for admission/registration
        message = self.hl7_adapter.create_admit_message(
            patient_id=patient_id,
            patient_name=patient_name,
            date_of_birth=date_of_birth.replace("-", ""),
            gender=gender,
            admission_date=timestamp,
            diagnosis=diagnosis
        )
        
        return message
    
    def convert_case_to_fhir(self, case_data: Dict[str, Any]) -> List[FHIRResource]:
        """
        Convert internal case data to FHIR resources
        
        Args:
            case_data: Internal case data dictionary
            
        Returns:
            List of FHIRResource objects
        """
        resources = []
        
        # Extract patient information
        patient_id = case_data.get("patient_id", "")
        patient_name = case_data.get("patient_name", "Unknown")
        date_of_birth = case_data.get("date_of_birth", "")
        gender = case_data.get("gender", "unknown")
        
        # Create Patient resource
        if patient_id and date_of_birth:
            patient = self.fhir_adapter.create_patient(
                patient_id=patient_id,
                name=patient_name,
                date_of_birth=date_of_birth,
                gender=gender
            )
            resources.append(patient)
        
        # Extract diagnosis/condition
        diagnosis = case_data.get("diagnosis")
        if diagnosis:
            timestamp_str = case_data.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except Exception:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            condition = self.fhir_adapter.create_condition(
                patient_id=patient_id,
                condition_code=diagnosis,  # Would map to SNOMED CT in production
                condition_name=diagnosis,
                onset_date=timestamp
            )
            resources.append(condition)
        
        # Extract observations
        observations = case_data.get("observations", [])
        for obs in observations:
            timestamp_str = obs.get("timestamp") or case_data.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except Exception:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            observation = self.fhir_adapter.create_observation(
                patient_id=patient_id,
                observation_code=obs.get("code", ""),
                observation_value=float(obs.get("value", 0)),
                observation_date=timestamp,
                units=obs.get("units")
            )
            resources.append(observation)
        
        return resources

