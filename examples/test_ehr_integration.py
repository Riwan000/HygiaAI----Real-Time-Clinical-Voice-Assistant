#!/usr/bin/env python3
"""
Test EHR Integration

Tests HL7 and FHIR adapters, EHR connector, and integration with HygiaAI.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ehr import (
    HL7Adapter,
    HL7MessageType,
    FHIRAdapter,
    FHIRResourceType,
    EHRConnector,
    ConnectionConfig,
    EHRSystem,
    EHRIntegration
)
from src.storage.qdrant_storage import QdrantStorage

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    """Test EHR integration"""
    print("=" * 80)
    print("  EHR Integration Test")
    print("=" * 80)
    
    # Test 1: HL7 Adapter
    print_section("Test 1: HL7 Adapter")
    hl7_adapter = HL7Adapter()
    
    # Create ADT message
    print("Creating ADT^A01 (Admit Patient) message...")
    admit_msg = hl7_adapter.create_admit_message(
        patient_id="PAT001",
        patient_name="John^Doe",
        date_of_birth="19800101",
        gender="M",
        admission_date=datetime.now(timezone.utc),
        diagnosis="Pneumonia"
    )
    
    print(f"✓ Created HL7 message: {admit_msg.message_type.value}")
    print(f"  Message Control ID: {admit_msg.message_control_id}")
    print(f"  Segments: {len(admit_msg.segments)}")
    
    # Convert to HL7 string
    hl7_string = admit_msg.to_hl7_string()
    print(f"\n  HL7 Message (first 200 chars):")
    print(f"  {hl7_string[:200]}...")
    
    # Parse HL7 message
    print("\n  Parsing HL7 message...")
    parsed_msg = hl7_adapter.parse_message(hl7_string)
    print(f"✓ Parsed message type: {parsed_msg.message_type.value}")
    print(f"  Patient ID: {parsed_msg.segments[0].get('fields', [])[0] if parsed_msg.segments else 'N/A'}")
    
    # Convert to internal format
    internal_data = hl7_adapter.convert_to_internal_format(parsed_msg)
    print(f"\n  Internal format:")
    print(f"  Patient ID: {internal_data.get('patient_id')}")
    print(f"  Patient Name: {internal_data.get('patient_name')}")
    print(f"  Diagnosis: {internal_data.get('diagnosis')}")
    
    # Create Observation message
    print("\n  Creating ORU^R01 (Observation Result) message...")
    obs_msg = hl7_adapter.create_observation_message(
        patient_id="PAT001",
        observation_code="8480-6",  # Systolic BP LOINC code
        observation_value="120",
        observation_date=datetime.now(timezone.utc),
        units="mmHg"
    )
    print(f"✓ Created observation message: {obs_msg.message_type.value}")
    
    # Test 2: FHIR Adapter
    print_section("Test 2: FHIR Adapter")
    fhir_adapter = FHIRAdapter()
    
    # Create Patient resource
    print("Creating FHIR Patient resource...")
    patient = fhir_adapter.create_patient(
        patient_id="PAT001",
        name="John Doe",
        date_of_birth="1980-01-01",
        gender="male"
    )
    print(f"✓ Created Patient resource")
    patient_json = patient.to_json()
    print(f"  Resource Type: {patient.resource_type.value}")
    print(f"  Resource ID: {patient.id}")
    print(f"  JSON (first 200 chars):")
    print(f"  {patient_json[:200]}...")
    
    # Parse FHIR resource
    print("\n  Parsing FHIR resource...")
    parsed_patient = fhir_adapter.parse_resource(patient_json)
    print(f"✓ Parsed resource type: {parsed_patient.resource_type.value}")
    
    # Convert to internal format
    internal_patient = fhir_adapter.convert_to_internal_format(parsed_patient)
    print(f"\n  Internal format:")
    print(f"  Patient ID: {internal_patient.get('patient_id')}")
    print(f"  Patient Name: {internal_patient.get('patient_name')}")
    print(f"  Date of Birth: {internal_patient.get('date_of_birth')}")
    print(f"  Gender: {internal_patient.get('gender')}")
    
    # Create Observation resource
    print("\n  Creating FHIR Observation resource...")
    observation = fhir_adapter.create_observation(
        patient_id="PAT001",
        observation_code="8480-6",
        observation_value=120.0,
        observation_date=datetime.now(timezone.utc),
        units="mmHg",
        display_name="Systolic Blood Pressure"
    )
    print(f"✓ Created Observation resource")
    print(f"  Observation Code: {observation.data.get('code', {}).get('coding', [{}])[0].get('code')}")
    
    # Create Condition resource
    print("\n  Creating FHIR Condition resource...")
    condition = fhir_adapter.create_condition(
        patient_id="PAT001",
        condition_code="233604007",  # SNOMED CT code for Pneumonia
        condition_name="Pneumonia",
        onset_date=datetime.now(timezone.utc)
    )
    print(f"✓ Created Condition resource")
    print(f"  Condition Code: {condition.data.get('code', {}).get('coding', [{}])[0].get('code')}")
    
    # Test 3: EHR Connector
    print_section("Test 3: EHR Connector")
    
    # Create connection config for generic FHIR
    config = ConnectionConfig(
        system=EHRSystem.GENERIC_FHIR,
        host="fhir.example.com",
        port=443,
        use_ssl=True,
        fhir_base_url="https://fhir.example.com/fhir"
    )
    
    connector = EHRConnector(config)
    print(f"✓ Created connector for {config.system.value}")
    
    # Connect
    print("\n  Connecting to EHR...")
    if connector.connect():
        print(f"✓ Connected to EHR system")
        print(f"  System: {connector.config.system.value}")
        print(f"  Host: {connector.config.host}")
    else:
        print("✗ Failed to connect (expected in test environment)")
    
    # Test 4: EHR Integration
    print_section("Test 4: EHR Integration")
    
    # Initialize storage
    storage = QdrantStorage(
        host="localhost",
        port=6333,
        collection_name="clinical_cases",
        vector_size=768,
        enable_encryption=False,
        enable_deidentification=False
    )
    
    integration = EHRIntegration(
        ehr_connector=connector,
        qdrant_storage=storage
    )
    print("✓ EHR integration initialized")
    
    # Import from HL7
    print("\n  Importing from HL7...")
    try:
        imported_hl7 = integration.import_patient_from_hl7(hl7_string)
        print(f"✓ Imported patient data from HL7")
        print(f"  Patient ID: {imported_hl7.get('patient_id')}")
        print(f"  Diagnosis: {imported_hl7.get('diagnosis')}")
    except Exception as e:
        print(f"✗ Error importing from HL7: {e}")
    
    # Import from FHIR
    print("\n  Importing from FHIR...")
    try:
        imported_fhir = integration.import_patient_from_fhir(patient_json)
        print(f"✓ Imported patient data from FHIR")
        print(f"  Resource ID: {imported_fhir.get('resource_id')}")
        print(f"  Patient Name: {imported_fhir.get('patient_name')}")
    except Exception as e:
        print(f"✗ Error importing from FHIR: {e}")
    
    print("\n" + "=" * 80)
    print("  All Tests Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()

