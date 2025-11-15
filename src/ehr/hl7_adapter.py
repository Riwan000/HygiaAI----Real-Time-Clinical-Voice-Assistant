"""
HL7 Adapter for EHR Integration

Supports HL7 v2.x message parsing and generation for common EHR systems.
Handles ADT (Admit/Discharge/Transfer), ORU (Observation Result), and MDM (Medical Document) messages.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re

logger = logging.getLogger(__name__)

# Optional HL7 library
try:
    import hl7
    HL7_LIB_AVAILABLE = True
except ImportError:
    HL7_LIB_AVAILABLE = False
    logger.warning("hl7 library not available. Install with: pip install hl7")


class HL7MessageType(Enum):
    """HL7 message types"""
    ADT_A01 = "ADT^A01"  # Admit patient
    ADT_A03 = "ADT^A03"  # Discharge patient
    ADT_A04 = "ADT^A04"  # Register patient
    ADT_A08 = "ADT^A08"  # Update patient information
    ORU_R01 = "ORU^R01"  # Observation result
    MDM_T02 = "MDM^T02"  # Document notification
    ACK = "ACK"  # Acknowledgment


@dataclass
class HL7Message:
    """HL7 message structure"""
    message_type: HL7MessageType
    message_control_id: str
    sending_application: str = ""
    sending_facility: str = ""
    receiving_application: str = ""
    receiving_facility: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    segments: List[Dict[str, Any]] = field(default_factory=list)
    raw_message: Optional[str] = None
    
    def to_hl7_string(self) -> str:
        """Convert to HL7 v2.x string format"""
        if self.raw_message:
            return self.raw_message
        
        lines = []
        
        # MSH segment (Message Header)
        msh = [
            "MSH",
            "^~\\&",  # Field separator, encoding characters
            self.sending_application,
            self.sending_facility,
            self.receiving_application,
            self.receiving_facility,
            self.timestamp.strftime("%Y%m%d%H%M%S"),
            "",
            self.message_type.value,
            self.message_control_id,
            "P",  # Processing ID
            "2.5"  # Version ID
        ]
        lines.append("|".join(msh))
        
        # Add other segments
        for segment in self.segments:
            if isinstance(segment, dict):
                segment_type = segment.get("type", "")
                fields = segment.get("fields", [])
                segment_line = "|".join([segment_type] + [str(f) for f in fields])
                lines.append(segment_line)
        
        return "\r".join(lines) + "\r"
    
    @classmethod
    def from_hl7_string(cls, message: str) -> "HL7Message":
        """Parse HL7 v2.x string format"""
        if HL7_LIB_AVAILABLE:
            return cls._parse_with_library(message)
        else:
            return cls._parse_manual(message)
    
    @classmethod
    def _parse_with_library(cls, message: str) -> "HL7Message":
        """Parse using hl7 library if available"""
        try:
            h = hl7.parse(message)
            
            # Extract MSH segment
            msh = h.segments("MSH")[0]
            
            # Determine message type
            msg_type_str = f"{msh[8][0]}^{msh[8][1]}"
            try:
                msg_type = HL7MessageType(msg_type_str)
            except ValueError:
                msg_type = HL7MessageType.ACK
            
            # Extract segments
            segments = []
            for seg in h.segments():
                seg_type = seg[0][0]
                fields = [str(field) for field in seg[1:]]
                segments.append({
                    "type": seg_type,
                    "fields": fields
                })
            
            return cls(
                message_type=msg_type,
                message_control_id=str(msh[9][0]) if len(msh) > 9 else "",
                sending_application=str(msh[2][0]) if len(msh) > 2 else "",
                sending_facility=str(msh[3][0]) if len(msh) > 3 else "",
                receiving_application=str(msh[4][0]) if len(msh) > 4 else "",
                receiving_facility=str(msh[5][0]) if len(msh) > 5 else "",
                timestamp=datetime.strptime(str(msh[6][0]), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc) if len(msh) > 6 else datetime.now(timezone.utc),
                segments=segments,
                raw_message=message
            )
        except Exception as e:
            logger.error(f"Error parsing HL7 message with library: {e}")
            return cls._parse_manual(message)
    
    @classmethod
    def _parse_manual(cls, message: str) -> "HL7Message":
        """Manual parsing fallback"""
        lines = message.strip().split("\r")
        if not lines:
            raise ValueError("Empty HL7 message")
        
        # Parse MSH segment
        msh_fields = lines[0].split("|")
        if len(msh_fields) < 12:
            raise ValueError("Invalid MSH segment")
        
        # Extract message type
        msg_type_str = msh_fields[8] if len(msh_fields) > 8 else "ACK"
        try:
            msg_type = HL7MessageType(msg_type_str)
        except ValueError:
            msg_type = HL7MessageType.ACK
        
        # Parse timestamp
        timestamp_str = msh_fields[6] if len(msh_fields) > 6 else ""
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except (ValueError, IndexError):
            timestamp = datetime.now(timezone.utc)
        
        # Parse other segments
        segments = []
        for line in lines[1:]:
            if line.strip():
                fields = line.split("|")
                if fields:
                    segments.append({
                        "type": fields[0],
                        "fields": fields[1:]
                    })
        
        return cls(
            message_type=msg_type,
            message_control_id=msh_fields[9] if len(msh_fields) > 9 else "",
            sending_application=msh_fields[2] if len(msh_fields) > 2 else "",
            sending_facility=msh_fields[3] if len(msh_fields) > 3 else "",
            receiving_application=msh_fields[4] if len(msh_fields) > 4 else "",
            receiving_facility=msh_fields[5] if len(msh_fields) > 5 else "",
            timestamp=timestamp,
            segments=segments,
            raw_message=message
        )


class HL7Adapter:
    """
    HL7 Adapter for EHR Integration
    
    Features:
    - Parse HL7 v2.x messages
    - Generate HL7 messages
    - Convert between HL7 and internal data models
    - Support for common message types (ADT, ORU, MDM)
    """
    
    def __init__(self):
        """Initialize HL7 adapter"""
        if not HL7_LIB_AVAILABLE:
            logger.warning(
                "hl7 library not available. Basic parsing will work, but advanced features may be limited. "
                "Install with: pip install hl7"
            )
        logger.info("HL7 adapter initialized")
    
    def parse_message(self, message: str) -> HL7Message:
        """
        Parse HL7 message string
        
        Args:
            message: HL7 v2.x message string
            
        Returns:
            Parsed HL7Message object
        """
        try:
            return HL7Message.from_hl7_string(message)
        except Exception as e:
            logger.error(f"Error parsing HL7 message: {e}")
            raise
    
    def create_admit_message(
        self,
        patient_id: str,
        patient_name: str,
        date_of_birth: str,
        gender: str,
        admission_date: datetime,
        diagnosis: Optional[str] = None
    ) -> HL7Message:
        """
        Create ADT^A01 (Admit Patient) message
        
        Args:
            patient_id: Patient identifier
            patient_name: Patient full name
            date_of_birth: Date of birth (YYYYMMDD)
            gender: Gender (M/F/O)
            admission_date: Admission date/time
            diagnosis: Optional diagnosis code
            
        Returns:
            HL7Message object
        """
        segments = []
        
        # PID segment (Patient Identification)
        pid_fields = [
            "PID",
            "1",  # Set ID
            patient_id,  # Patient ID
            "",  # Patient ID list
            "",  # Alternate patient ID
            patient_name,  # Patient name
            "",  # Mother's maiden name
            date_of_birth,  # Date of birth
            gender,  # Gender
            "",  # Patient alias
            "",  # Race
            "",  # Patient address
            "",  # County code
            "",  # Phone number
            "",  # Phone number business
            "",  # Primary language
            "",  # Marital status
            "",  # Religion
            "",  # Patient account number
            "",  # SSN
            "",  # Driver's license
            "",  # Mother's identifier
            "",  # Ethnic group
            "",  # Birth place
            "",  # Multiple birth indicator
            "",  # Birth order
            "",  # Citizenship
            "",  # Veterans military status
            "",  # Nationality
            "",  # Patient death date and time
            "",  # Patient death indicator
            "",  # Identity unknown indicator
            "",  # Identity reliability code
            "",  # Last update date/time
            "",  # Last update facility
            "",  # Species code
            "",  # Breed code
            "",  # Strain
            "",  # Production class code
            "",  # Tribal citizenship
        ]
        segments.append({
            "type": "PID",
            "fields": pid_fields[1:]
        })
        
        # PV1 segment (Patient Visit)
        pv1_fields = [
            "PV1",
            "1",  # Set ID
            "I",  # Patient class (Inpatient)
            "",  # Assigned patient location
            "",  # Admission type
            "",  # Preadmit number
            "",  # Prior patient location
            "",  # Attending doctor
            "",  # Referring doctor
            "",  # Consulting doctor
            "",  # Hospital service
            "",  # Temporary location
            "",  # Preadmit test indicator
            "",  # Re-admission indicator
            "",  # Admit source
            "",  # Ambulatory status
            "",  # VIP indicator
            "",  # Admitting doctor
            "",  # Patient type
            "",  # Visit number
            "",  # Financial class
            "",  # Charge price indicator
            "",  # Courtesy code
            "",  # Credit rating
            "",  # Contract code
            "",  # Contract effective date
            "",  # Contract amount
            "",  # Contract period
            "",  # Interest code
            "",  # Transfer to bad debt code
            "",  # Transfer to bad debt date
            "",  # Bad debt agency code
            "",  # Bad debt transfer amount
            "",  # Bad debt recovery amount
            "",  # Delete account indicator
            "",  # Delete account date
            "",  # Discharge disposition
            "",  # Discharged to location
            "",  # Diet type
            "",  # Servicing facility
            "",  # Bed status
            "",  # Account status
            "",  # Pending location
            "",  # Prior temporary location
            admission_date.strftime("%Y%m%d%H%M%S"),  # Admit date/time
            "",  # Discharge date/time
            "",  # Current patient balance
            "",  # Total charges
            "",  # Total adjustments
            "",  # Total payments
            "",  # Alternate visit ID
        ]
        segments.append({
            "type": "PV1",
            "fields": pv1_fields[1:]
        })
        
        # DG1 segment (Diagnosis) if provided
        if diagnosis:
            dg1_fields = [
                "DG1",
                "1",  # Set ID
                "",  # Coding method
                diagnosis,  # Diagnosis code
                "",  # Diagnosis description
                admission_date.strftime("%Y%m%d"),  # Diagnosis date/time
                "",  # Diagnosis type
                "",  # Major diagnostic category
                "",  # Diagnostic related group
                "",  # DRG approval indicator
                "",  # DRG grouper review code
                "",  # Outlier type
                "",  # Outlier days
                "",  # Outlier cost
                "",  # Grouper version and type
                "",  # Diagnosis priority
                "",  # Diagnosing clinician
                "",  # Diagnosis classification
                "",  # Confidential indicator
                "",  # Attestation date/time
                "",  # Diagnosis identifier
                "",  # Diagnosis action code
            ]
            segments.append({
                "type": "DG1",
                "fields": dg1_fields[1:]
            })
        
        message = HL7Message(
            message_type=HL7MessageType.ADT_A01,
            message_control_id=f"MSG{datetime.now().strftime('%Y%m%d%H%M%S')}",
            sending_application="HygiaAI",
            sending_facility="CLINIC",
            receiving_application="EHR",
            receiving_facility="HOSPITAL",
            segments=segments
        )
        
        return message
    
    def create_observation_message(
        self,
        patient_id: str,
        observation_code: str,
        observation_value: str,
        observation_date: datetime,
        units: Optional[str] = None
    ) -> HL7Message:
        """
        Create ORU^R01 (Observation Result) message
        
        Args:
            patient_id: Patient identifier
            observation_code: Observation/test code (e.g., LOINC code)
            observation_value: Observation value
            observation_date: Observation date/time
            units: Optional units for the observation
            
        Returns:
            HL7Message object
        """
        segments = []
        
        # PID segment
        segments.append({
            "type": "PID",
            "fields": [
                "1",
                patient_id,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        })
        
        # OBR segment (Observation Request)
        obr_fields = [
            "OBR",
            "1",  # Set ID
            "",  # Placer order number
            "",  # Filler order number
            observation_code,  # Universal service identifier
            "",  # Priority
            "",  # Requested date/time
            observation_date.strftime("%Y%m%d%H%M%S"),  # Observation date/time
            "",  # Observation end date/time
            "",  # Collection volume
            "",  # Collector identifier
            "",  # Specimen action code
            "",  # Danger code
            "",  # Relevant clinical information
            "",  # Specimen received date/time
            "",  # Specimen source
            "",  # Ordering provider
            "",  # Order callback phone number
            "",  # Placer field 1
            "",  # Placer field 2
            "",  # Filler field 1
            "",  # Filler field 2
            "",  # Results Rpt/Status Chng - Date/Time
            "",  # Charge to practice
            "",  # Diagnostic serv sect ID
            "",  # Result status
            "",  # Parent result
            "",  # Quantity/timing
            "",  # Result copies to
            "",  # Parent
            "",  # Transportation mode
            "",  # Reason for study
            "",  # Principal result interpreter
            "",  # Assistant result interpreter
            "",  # Technician
            "",  # Transcriptionist
            "",  # Scheduled date/time
            "",  # Number of sample containers
            "",  # Transport logistics of collected sample
            "",  # Collector's comment
            "",  # Transport arrangement responsibility
            "",  # Transport arranged
            "",  # Escort required
            "",  # Planned patient transport comment
            "",  # Procedure code
            "",  # Procedure code modifier
            "",  # Placer supplemental service information
            "",  # Filler supplemental service information
            "",  # Medically necessary duplicate procedure reason
            "",  # Result handling
        ]
        segments.append({
            "type": "OBR",
            "fields": obr_fields[1:]
        })
        
        # OBX segment (Observation/Result)
        obx_fields = [
            "OBX",
            "1",  # Set ID
            "NM",  # Value type (Numeric)
            observation_code,  # Observation identifier
            "",  # Observation sub-ID
            observation_value,  # Observation value
            units or "",  # Units
            "",  # References range
            "",  # Abnormal flags
            "",  # Probability
            "",  # Nature of abnormal test
            "",  # Observation result status
            "",  # Date last observation normal value
            "",  # User defined access checks
            observation_date.strftime("%Y%m%d%H%M%S"),  # Date/time of the observation
            "",  # Producer's ID
            "",  # Responsible observer
            "",  # Observation method
            "",  # Equipment instance identifier
            "",  # Date/time of the analysis
        ]
        segments.append({
            "type": "OBX",
            "fields": obx_fields[1:]
        })
        
        message = HL7Message(
            message_type=HL7MessageType.ORU_R01,
            message_control_id=f"MSG{datetime.now().strftime('%Y%m%d%H%M%S')}",
            sending_application="HygiaAI",
            sending_facility="CLINIC",
            receiving_application="EHR",
            receiving_facility="HOSPITAL",
            segments=segments
        )
        
        return message
    
    def convert_to_internal_format(self, message: HL7Message) -> Dict[str, Any]:
        """
        Convert HL7 message to internal data format
        
        Args:
            message: HL7Message object
            
        Returns:
            Dictionary in internal format
        """
        result = {
            "message_type": message.message_type.value,
            "message_control_id": message.message_control_id,
            "timestamp": message.timestamp.isoformat(),
            "patient_id": None,
            "patient_name": None,
            "diagnosis": None,
            "observations": []
        }
        
        # Extract PID segment
        for segment in message.segments:
            if segment.get("type") == "PID":
                fields = segment.get("fields", [])
                if len(fields) > 0:
                    result["patient_id"] = fields[0] if len(fields) > 0 else None
                if len(fields) > 4:
                    result["patient_name"] = fields[4] if len(fields) > 4 else None
            
            # Extract DG1 segment (Diagnosis)
            if segment.get("type") == "DG1":
                fields = segment.get("fields", [])
                if len(fields) > 2:
                    result["diagnosis"] = fields[2] if len(fields) > 2 else None
            
            # Extract OBX segment (Observations)
            if segment.get("type") == "OBX":
                fields = segment.get("fields", [])
                if len(fields) > 4:
                    result["observations"].append({
                        "code": fields[2] if len(fields) > 2 else "",
                        "value": fields[4] if len(fields) > 4 else "",
                        "units": fields[5] if len(fields) > 5 else "",
                        "timestamp": message.timestamp.isoformat()
                    })
        
        return result
    
    def create_acknowledgment(
        self,
        original_message: HL7Message,
        acknowledgment_code: str = "AA"  # AA=Application Accept, AE=Application Error, AR=Application Reject
    ) -> HL7Message:
        """
        Create acknowledgment message for received HL7 message
        
        Args:
            original_message: Original HL7 message to acknowledge
            acknowledgment_code: Acknowledgment code (AA/AE/AR)
            
        Returns:
            HL7Message acknowledgment
        """
        segments = []
        
        # MSA segment (Message Acknowledgment)
        msa_fields = [
            "MSA",
            acknowledgment_code,  # Acknowledgment code
            original_message.message_control_id,  # Message control ID
            "",  # Text message
            "",  # Expected sequence number
            "",  # Delayed acknowledgment type
            "",  # Error condition
        ]
        segments.append({
            "type": "MSA",
            "fields": msa_fields[1:]
        })
        
        message = HL7Message(
            message_type=HL7MessageType.ACK,
            message_control_id=f"ACK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            sending_application=original_message.receiving_application,
            sending_facility=original_message.receiving_facility,
            receiving_application=original_message.sending_application,
            receiving_facility=original_message.sending_facility,
            segments=segments
        )
        
        return message

