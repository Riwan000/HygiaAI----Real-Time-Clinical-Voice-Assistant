"""
Unit tests for EHR integration module
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from src.ehr import (
    HL7Adapter,
    HL7Message,
    HL7MessageType,
    FHIRAdapter,
    FHIRResource,
    FHIRResourceType,
    EHRConnector,
    ConnectionConfig,
    EHRSystem,
    EHRIntegration
)


class TestHL7Adapter:
    """Test HL7Adapter"""
    
    def test_initialization(self):
        """Test adapter initialization"""
        adapter = HL7Adapter()
        assert adapter is not None
    
    def test_create_admit_message(self):
        """Test creating ADT message"""
        adapter = HL7Adapter()
        message = adapter.create_admit_message(
            patient_id="PAT001",
            patient_name="John^Doe",
            date_of_birth="19800101",
            gender="M",
            admission_date=datetime.now(timezone.utc),
            diagnosis="Pneumonia"
        )
        
        assert message.message_type == HL7MessageType.ADT_A01
        assert message.message_control_id is not None
        assert len(message.segments) > 0
    
    def test_create_observation_message(self):
        """Test creating ORU message"""
        adapter = HL7Adapter()
        message = adapter.create_observation_message(
            patient_id="PAT001",
            observation_code="8480-6",
            observation_value="120",
            observation_date=datetime.now(timezone.utc),
            units="mmHg"
        )
        
        assert message.message_type == HL7MessageType.ORU_R01
        assert len(message.segments) > 0
    
    def test_parse_message(self):
        """Test parsing HL7 message"""
        adapter = HL7Adapter()
        
        # Create a message first
        original = adapter.create_admit_message(
            patient_id="PAT001",
            patient_name="John^Doe",
            date_of_birth="19800101",
            gender="M",
            admission_date=datetime.now(timezone.utc)
        )
        
        # Convert to string and parse back
        message_str = original.to_hl7_string()
        parsed = adapter.parse_message(message_str)
        
        assert parsed.message_type == original.message_type
        assert parsed.message_control_id == original.message_control_id
    
    def test_convert_to_internal_format(self):
        """Test converting HL7 to internal format"""
        adapter = HL7Adapter()
        message = adapter.create_admit_message(
            patient_id="PAT001",
            patient_name="John^Doe",
            date_of_birth="19800101",
            gender="M",
            admission_date=datetime.now(timezone.utc),
            diagnosis="Pneumonia"
        )
        
        internal = adapter.convert_to_internal_format(message)
        
        assert "patient_id" in internal
        assert "patient_name" in internal
        assert "diagnosis" in internal
    
    def test_create_acknowledgment(self):
        """Test creating acknowledgment"""
        adapter = HL7Adapter()
        original = adapter.create_admit_message(
            patient_id="PAT001",
            patient_name="John^Doe",
            date_of_birth="19800101",
            gender="M",
            admission_date=datetime.now(timezone.utc)
        )
        
        ack = adapter.create_acknowledgment(original, acknowledgment_code="AA")
        
        assert ack.message_type == HL7MessageType.ACK
        assert len(ack.segments) > 0


class TestFHIRAdapter:
    """Test FHIRAdapter"""
    
    def test_initialization(self):
        """Test adapter initialization"""
        adapter = FHIRAdapter()
        assert adapter is not None
    
    def test_create_patient(self):
        """Test creating Patient resource"""
        adapter = FHIRAdapter()
        patient = adapter.create_patient(
            patient_id="PAT001",
            name="John Doe",
            date_of_birth="1980-01-01",
            gender="male"
        )
        
        assert patient.resource_type == FHIRResourceType.PATIENT
        assert patient.id == "PAT001"
        assert "name" in patient.data
        assert "gender" in patient.data
    
    def test_create_observation(self):
        """Test creating Observation resource"""
        adapter = FHIRAdapter()
        observation = adapter.create_observation(
            patient_id="PAT001",
            observation_code="8480-6",
            observation_value=120.0,
            observation_date=datetime.now(timezone.utc),
            units="mmHg"
        )
        
        assert observation.resource_type == FHIRResourceType.OBSERVATION
        assert "code" in observation.data
        assert "valueQuantity" in observation.data
    
    def test_create_condition(self):
        """Test creating Condition resource"""
        adapter = FHIRAdapter()
        condition = adapter.create_condition(
            patient_id="PAT001",
            condition_code="233604007",
            condition_name="Pneumonia",
            onset_date=datetime.now(timezone.utc)
        )
        
        assert condition.resource_type == FHIRResourceType.CONDITION
        assert "code" in condition.data
        assert "subject" in condition.data
    
    def test_parse_resource(self):
        """Test parsing FHIR resource"""
        adapter = FHIRAdapter()
        
        # Create a resource first
        original = adapter.create_patient(
            patient_id="PAT001",
            name="John Doe",
            date_of_birth="1980-01-01",
            gender="male"
        )
        
        # Convert to JSON and parse back
        json_str = original.to_json()
        parsed = adapter.parse_resource(json_str)
        
        assert parsed.resource_type == original.resource_type
        assert parsed.id == original.id
    
    def test_convert_to_internal_format(self):
        """Test converting FHIR to internal format"""
        adapter = FHIRAdapter()
        patient = adapter.create_patient(
            patient_id="PAT001",
            name="John Doe",
            date_of_birth="1980-01-01",
            gender="male"
        )
        
        internal = adapter.convert_to_internal_format(patient)
        
        assert "patient_id" in internal
        assert "patient_name" in internal
        assert "date_of_birth" in internal


class TestEHRConnector:
    """Test EHRConnector"""
    
    def test_initialization(self):
        """Test connector initialization"""
        config = ConnectionConfig(
            system=EHRSystem.GENERIC_FHIR,
            host="fhir.example.com",
            fhir_base_url="https://fhir.example.com/fhir"
        )
        
        connector = EHRConnector(config)
        assert connector.config == config
        assert not connector.is_connected()
    
    def test_connect(self):
        """Test connecting to EHR"""
        config = ConnectionConfig(
            system=EHRSystem.GENERIC_FHIR,
            host="fhir.example.com",
            fhir_base_url="https://fhir.example.com/fhir"
        )
        
        connector = EHRConnector(config)
        result = connector.connect()
        
        assert result is True
        assert connector.is_connected()
    
    def test_convert_case_to_hl7(self):
        """Test converting case to HL7"""
        config = ConnectionConfig(
            system=EHRSystem.GENERIC_HL7,
            host="hl7.example.com",
            hl7_endpoint="mllp://hl7.example.com:2575"
        )
        
        connector = EHRConnector(config)
        connector.connect()
        
        case_data = {
            "patient_id": "PAT001",
            "patient_name": "John Doe",
            "date_of_birth": "1980-01-01",
            "gender": "M",
            "diagnosis": "Pneumonia",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        message = connector.convert_case_to_hl7(case_data)
        
        assert message.message_type == HL7MessageType.ADT_A01
        assert message.message_control_id is not None
    
    def test_convert_case_to_fhir(self):
        """Test converting case to FHIR"""
        config = ConnectionConfig(
            system=EHRSystem.GENERIC_FHIR,
            host="fhir.example.com",
            fhir_base_url="https://fhir.example.com/fhir"
        )
        
        connector = EHRConnector(config)
        connector.connect()
        
        case_data = {
            "patient_id": "PAT001",
            "patient_name": "John Doe",
            "date_of_birth": "1980-01-01",
            "gender": "male",
            "diagnosis": "Pneumonia",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        resources = connector.convert_case_to_fhir(case_data)
        
        assert len(resources) > 0
        assert any(r.resource_type == FHIRResourceType.PATIENT for r in resources)


class TestEHRIntegration:
    """Test EHRIntegration"""
    
    def test_initialization(self):
        """Test integration initialization"""
        config = ConnectionConfig(
            system=EHRSystem.GENERIC_FHIR,
            host="fhir.example.com",
            fhir_base_url="https://fhir.example.com/fhir"
        )
        
        connector = EHRConnector(config)
        integration = EHRIntegration(
            ehr_connector=connector,
            qdrant_storage=None
        )
        
        assert integration.connector == connector
    
    def test_import_patient_from_hl7(self):
        """Test importing from HL7"""
        adapter = HL7Adapter()
        message = adapter.create_admit_message(
            patient_id="PAT001",
            patient_name="John^Doe",
            date_of_birth="19800101",
            gender="M",
            admission_date=datetime.now(timezone.utc),
            diagnosis="Pneumonia"
        )
        
        message_str = message.to_hl7_string()
        
        config = ConnectionConfig(
            system=EHRSystem.GENERIC_HL7,
            host="hl7.example.com"
        )
        connector = EHRConnector(config)
        
        integration = EHRIntegration(
            ehr_connector=connector,
            qdrant_storage=None
        )
        
        imported = integration.import_patient_from_hl7(message_str)
        
        assert "patient_id" in imported
        assert imported["patient_id"] is not None
    
    def test_import_patient_from_fhir(self):
        """Test importing from FHIR"""
        adapter = FHIRAdapter()
        patient = adapter.create_patient(
            patient_id="PAT001",
            name="John Doe",
            date_of_birth="1980-01-01",
            gender="male"
        )
        
        patient_json = patient.to_json()
        
        config = ConnectionConfig(
            system=EHRSystem.GENERIC_FHIR,
            host="fhir.example.com",
            fhir_base_url="https://fhir.example.com/fhir"
        )
        connector = EHRConnector(config)
        
        integration = EHRIntegration(
            ehr_connector=connector,
            qdrant_storage=None
        )
        
        imported = integration.import_patient_from_fhir(patient_json)
        
        assert "resource_id" in imported
        assert imported["resource_id"] == "PAT001"

