"""
Case data models for HygiaAI

Defines data structures for clinical cases including:
- Case information
- Modalities (text, image, audio)
- Metadata
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class CaseModality(BaseModel):
    """Represents a single modality within a case"""
    modality_type: str = Field(..., description="Type: text, image, or audio")
    content: Dict[str, Any] = Field(..., description="Modality-specific content")
    embeddings: Optional[List[float]] = Field(None, description="Vector embeddings")


class CaseMetadata(BaseModel):
    """Metadata for a clinical case"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    age_group: Optional[str] = Field(None, description="Age group: pediatric, adult, elderly")
    region: Optional[str] = Field(None, description="Geographic region or clinic ID")
    comorbidities: List[str] = Field(default_factory=list)
    diagnosis: Optional[str] = None
    outcome: Optional[str] = None


class Case(BaseModel):
    """Complete clinical case model"""
    case_id: str = Field(..., description="Unique case identifier")
    patient_id: str = Field(..., description="Anonymized patient ID")
    modalities: Dict[str, CaseModality] = Field(default_factory=dict)
    metadata: CaseMetadata = Field(default_factory=CaseMetadata)
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "uuid-123",
                "patient_id": "anon-456",
                "modalities": {
                    "text": {
                        "modality_type": "text",
                        "content": {
                            "transcript": "Patient reports fever and cough...",
                            "soap": "...",
                            "entities": ["fever", "cough"]
                        }
                    }
                },
                "metadata": {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "age_group": "adult",
                    "region": "rural_clinic_001",
                    "comorbidities": ["diabetes"],
                    "diagnosis": "pneumonia",
                    "outcome": "recovered"
                }
            }
        }

