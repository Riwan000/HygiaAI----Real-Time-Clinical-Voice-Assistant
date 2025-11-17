"""
Automatic Case Addition Orchestrator

Automatically adds new patient cases (text/image/audio) to Qdrant memory.
Generates embeddings, creates payloads with metadata, and upserts to Qdrant.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from pathlib import Path

from ..storage.qdrant_storage import QdrantStorage
from ..embeddings import (
    BioBERTEmbeddingGenerator,
    CLIPEmbeddingGenerator,
    AudioCLIPEmbeddingGenerator,
    MultimodalEmbeddingGenerator
)
from ..models.case_models import Case, CaseModality, CaseMetadata
from ..entity_extraction.soap_generator import SOAPGenerator

logger = logging.getLogger(__name__)


class CaseIngestionOrchestrator:
    """
    Orchestrates automatic case addition to clinical memory
    
    Features:
    - Automatically processes new cases (text/image/audio)
    - Generates embeddings for each modality
    - Stores cases in Qdrant with rich metadata
    - Updates local memory index
    """
    
    def __init__(
        self,
        qdrant_storage: Optional[QdrantStorage] = None,
        collection_name: str = "hygiaai_cases",
        use_rag: bool = True
    ):
        """
        Initialize case ingestion orchestrator
        
        Args:
            qdrant_storage: QdrantStorage instance (creates new if not provided)
            collection_name: Qdrant collection name for cases
            use_rag: Whether to use RAG enhancement for SOAP generation
        """
        import os
        
        self.collection_name = collection_name
        
        # Initialize Qdrant storage
        if qdrant_storage:
            self.storage = qdrant_storage
        else:
            self.storage = QdrantStorage(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6334")),
                collection_name=collection_name,
                vector_size=768
            )
        
        # Initialize embedding generators
        self.text_embedder = BioBERTEmbeddingGenerator()
        self.image_embedder = CLIPEmbeddingGenerator()
        
        # Initialize audio embedder only if available
        try:
            self.audio_embedder = AudioCLIPEmbeddingGenerator()
        except ImportError:
            logger.warning("Audio embedding generator not available (PyTorch/TorchAudio required)")
            self.audio_embedder = None
        
        self.multimodal_embedder = MultimodalEmbeddingGenerator()
        
        # Initialize SOAP generator
        self.soap_generator = SOAPGenerator(use_rag=use_rag)
        
        logger.info(f"Case ingestion orchestrator initialized (collection: {collection_name})")
    
    def ingest_case(
        self,
        case: Case,
        generate_soap: bool = True,
        store_modalities_separately: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest a complete case into Qdrant
        
        Args:
            case: Case object with modalities and metadata
            generate_soap: Whether to generate SOAP notes for text transcripts
            store_modalities_separately: Whether to store each modality as separate points
            
        Returns:
            Dictionary with ingestion results (point_ids, status, metadata)
        """
        try:
            point_ids = []
            ingestion_metadata = {
                "case_id": case.case_id,
                "patient_id": case.patient_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "modalities_processed": [],
                "soap_generated": False
            }
            
            # Process each modality
            for modality_name, modality in case.modalities.items():
                try:
                    if modality.modality_type == "text":
                        result = self._ingest_text_modality(
                            modality,
                            case.metadata,
                            generate_soap=generate_soap
                        )
                        point_ids.extend(result.get("point_ids", []))
                        ingestion_metadata["modalities_processed"].append({
                            "modality": modality_name,
                            "type": "text",
                            "point_ids": result.get("point_ids", [])
                        })
                        if result.get("soap_generated"):
                            ingestion_metadata["soap_generated"] = True
                    
                    elif modality.modality_type == "image":
                        result = self._ingest_image_modality(
                            modality,
                            case.metadata
                        )
                        point_ids.extend(result.get("point_ids", []))
                        ingestion_metadata["modalities_processed"].append({
                            "modality": modality_name,
                            "type": "image",
                            "point_ids": result.get("point_ids", [])
                        })
                    
                    elif modality.modality_type == "audio":
                        result = self._ingest_audio_modality(
                            modality,
                            case.metadata
                        )
                        point_ids.extend(result.get("point_ids", []))
                        ingestion_metadata["modalities_processed"].append({
                            "modality": modality_name,
                            "type": "audio",
                            "point_ids": result.get("point_ids", [])
                        })
                    
                except Exception as e:
                    logger.error(f"Error processing modality {modality_name}: {e}")
                    continue
            
            # Store unified case metadata if storing separately
            if store_modalities_separately and point_ids:
                case_metadata_point_id = self._store_case_metadata(case, point_ids)
                if case_metadata_point_id:
                    point_ids.append(case_metadata_point_id)
            
            logger.info(f"Successfully ingested case {case.case_id}: {len(point_ids)} points stored")
            
            return {
                "status": "success",
                "case_id": case.case_id,
                "point_ids": point_ids,
                "metadata": ingestion_metadata
            }
            
        except Exception as e:
            logger.error(f"Error ingesting case {case.case_id}: {e}")
            return {
                "status": "error",
                "case_id": case.case_id,
                "error": str(e),
                "point_ids": []
            }
    
    def _ingest_text_modality(
        self,
        modality: CaseModality,
        case_metadata: CaseMetadata,
        generate_soap: bool = True
    ) -> Dict[str, Any]:
        """Ingest text modality (transcript, SOAP note, etc.)"""
        point_ids = []
        soap_generated = False
        
        content = modality.content
        transcript = content.get("transcript") or content.get("text", "")
        
        if not transcript:
            logger.warning("No transcript found in text modality")
            return {"point_ids": [], "soap_generated": False}
        
        # Generate embedding
        embedding = self.text_embedder.generate_embedding(transcript)
        
        # Generate SOAP note if requested
        soap_note = None
        if generate_soap:
            try:
                soap_note = self.soap_generator.generate_soap(
                    transcript,
                    patient_metadata={
                        "age_group": case_metadata.age_group,
                        "region": case_metadata.region,
                        "comorbidities": case_metadata.comorbidities
                    }
                )
                soap_generated = True
            except Exception as e:
                logger.warning(f"Error generating SOAP note: {e}")
        
        # Prepare payload
        payload = {
            "modality_type": "text",
            "transcript": transcript,
            "case_metadata": case_metadata.dict(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if soap_note:
            payload["soap_note"] = {
                "subjective": soap_note.subjective,
                "objective": soap_note.objective,
                "assessment": soap_note.assessment,
                "plan": soap_note.plan
            }
        
        # Store in Qdrant
        point_id = str(uuid.uuid4())
        try:
            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            self.storage.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            point_ids.append(point_id)
        except Exception as e:
            logger.error(f"Error storing text modality: {e}")
        
        return {"point_ids": point_ids, "soap_generated": soap_generated}
    
    def _ingest_image_modality(
        self,
        modality: CaseModality,
        case_metadata: CaseMetadata
    ) -> Dict[str, Any]:
        """Ingest image modality (X-rays, lab reports, etc.)"""
        point_ids = []
        
        content = modality.content
        image_path = content.get("image_path") or content.get("path")
        
        if not image_path:
            logger.warning("No image path found in image modality")
            return {"point_ids": []}
        
        # Generate embedding
        try:
            embedding = self.image_embedder.generate_embedding(image_path)
        except Exception as e:
            logger.error(f"Error generating image embedding: {e}")
            return {"point_ids": []}
        
        # Prepare payload
        payload = {
            "modality_type": "image",
            "image_path": str(image_path),
            "case_metadata": case_metadata.dict(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in Qdrant
        point_id = str(uuid.uuid4())
        try:
            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            self.storage.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            point_ids.append(point_id)
        except Exception as e:
            logger.error(f"Error storing image modality: {e}")
        
        return {"point_ids": point_ids}
    
    def _ingest_audio_modality(
        self,
        modality: CaseModality,
        case_metadata: CaseMetadata
    ) -> Dict[str, Any]:
        """Ingest audio modality (consultation recordings)"""
        point_ids = []
        
        content = modality.content
        audio_path = content.get("audio_path") or content.get("path")
        
        if not audio_path:
            logger.warning("No audio path found in audio modality")
            return {"point_ids": []}
        
        # Generate embedding
        if not self.audio_embedder:
            logger.warning("Audio embedding generator not available. Skipping audio modality.")
            return {"point_ids": []}
        
        try:
            embedding = self.audio_embedder.generate_embedding(audio_path)
        except Exception as e:
            logger.error(f"Error generating audio embedding: {e}")
            return {"point_ids": []}
        
        # Prepare payload
        payload = {
            "modality_type": "audio",
            "audio_path": str(audio_path),
            "case_metadata": case_metadata.dict(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in Qdrant
        point_id = str(uuid.uuid4())
        try:
            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            self.storage.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            point_ids.append(point_id)
        except Exception as e:
            logger.error(f"Error storing audio modality: {e}")
        
        return {"point_ids": point_ids}
    
    def _store_case_metadata(
        self,
        case: Case,
        modality_point_ids: List[str]
    ) -> Optional[str]:
        """Store unified case metadata as a separate point"""
        try:
            # Generate embedding from case summary
            case_summary = f"Case {case.case_id}: {case.metadata.diagnosis or 'No diagnosis'}"
            embedding = self.text_embedder.generate_embedding(case_summary)
            
            payload = {
                "type": "case_metadata",
                "case_id": case.case_id,
                "patient_id": case.patient_id,
                "metadata": case.metadata.dict(),
                "modality_point_ids": modality_point_ids,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            point_id = str(uuid.uuid4())
            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            self.storage.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return point_id
        except Exception as e:
            logger.error(f"Error storing case metadata: {e}")
            return None

