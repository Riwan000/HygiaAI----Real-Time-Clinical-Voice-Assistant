"""
Unified Clinical Memory API Layer

Provides unified REST API endpoints for all clinical memory operations:
- Multimodal ingestion
- SOAP note generation
- Similar case recall
- Context-aware summarization
- Lab report normalization
"""

import logging
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..learning.case_ingestion import CaseIngestionOrchestrator
from ..learning.pattern_analyzer import PatternAnalyzer
from ..entity_extraction.soap_generator import SOAPGenerator
from ..retrieval.case_retrieval import CaseRetriever, RetrievalMode
from ..rag.clinical_rag import ClinicalRAG
from ..storage.qdrant_storage import QdrantStorage
from ..storage.knowledge_ingestion import KnowledgeIngestionPipeline
from ..embeddings import BioBERTEmbeddingGenerator
from ..utils.file_processor import FileProcessor
from ..models.case_models import Case, CaseModality, CaseMetadata
from ..storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
from ..knowledge_intelligence import (
    TemporalClusteringService,
    RegionalHealthAnalytics,
    ClinicalTrustScoreSystem
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/clinical_memory", tags=["Clinical Memory"])

# Global instances (can be dependency-injected in production)
_qdrant_storage: Optional[QdrantStorage] = None
_case_ingestion: Optional[CaseIngestionOrchestrator] = None
_pattern_analyzer: Optional[PatternAnalyzer] = None
_case_retriever: Optional[CaseRetriever] = None
_soap_generator: Optional[SOAPGenerator] = None
_clinical_rag: Optional[ClinicalRAG] = None
_temporal_clustering: Optional[TemporalClusteringService] = None
_regional_analytics: Optional[RegionalHealthAnalytics] = None
_trust_score_system: Optional[ClinicalTrustScoreSystem] = None


def get_qdrant_storage(collection_name: str = "hygiaai_cases") -> QdrantStorage:
    """
    Get or create Qdrant storage instance
    
    Args:
        collection_name: Name of the collection to use
            - "hygiaai_cases": Real-time patient cases from HygiaAI users
            - "patient_memory_collection": Historical patient records (MIMIC, eICU, etc.)
            - "clinical_kb_collection": Knowledge base (NCBI, PubMed, WHO, user uploads)
            - "imaging_collection": Medical images (optional)
            - "audio_collection": Audio datasets (optional)
    """
    # Use URL if provided (for cloud), otherwise use host/port (for local)
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        return QdrantStorage(
            url=qdrant_url,
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=collection_name,
            vector_size=768
        )
    else:
        return QdrantStorage(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=collection_name,
            vector_size=768
        )


def get_case_ingestion() -> CaseIngestionOrchestrator:
    """Get or create case ingestion orchestrator"""
    global _case_ingestion
    if _case_ingestion is None:
        storage = get_qdrant_storage()
        _case_ingestion = CaseIngestionOrchestrator(
            qdrant_storage=storage,
            collection_name="hygiaai_cases",
            use_rag=True
        )
    return _case_ingestion


def get_case_retriever() -> CaseRetriever:
    """Get or create case retriever"""
    global _case_retriever
    if _case_retriever is None:
        storage = get_qdrant_storage()
        _case_retriever = CaseRetriever(qdrant_storage=storage)
    return _case_retriever


def get_soap_generator() -> SOAPGenerator:
    """Get or create SOAP generator"""
    global _soap_generator
    if _soap_generator is None:
        _soap_generator = SOAPGenerator(use_rag=True)
    return _soap_generator


def get_clinical_rag() -> ClinicalRAG:
    """Get or create clinical RAG"""
    global _clinical_rag
    if _clinical_rag is None:
        # Use patient_memory_collection for case retrieval (includes all patient data)
        # Clinical RAG will use clinical_kb_collection for knowledge via its internal methods
        storage = get_qdrant_storage(collection_name="patient_memory_collection")
        retriever = CaseRetriever(qdrant_storage=storage)
        _clinical_rag = ClinicalRAG(case_retriever=retriever)
    return _clinical_rag


def get_temporal_clustering() -> TemporalClusteringService:
    """Get or create TemporalClusteringService instance"""
    global _temporal_clustering
    if _temporal_clustering is None:
        # Use patient_memory_collection for analytics (includes all patient data)
        _temporal_clustering = TemporalClusteringService(
            qdrant_storage=get_qdrant_storage(collection_name="patient_memory_collection"),
            collection_name="patient_memory_collection"
        )
    return _temporal_clustering


def get_regional_analytics() -> RegionalHealthAnalytics:
    """Get or create RegionalHealthAnalytics instance"""
    global _regional_analytics
    if _regional_analytics is None:
        # Use patient_memory_collection for analytics (includes all patient data)
        _regional_analytics = RegionalHealthAnalytics(
            qdrant_storage=get_qdrant_storage(collection_name="patient_memory_collection"),
            collection_name="patient_memory_collection"
        )
    return _regional_analytics


def get_trust_score_system() -> ClinicalTrustScoreSystem:
    """Get or create ClinicalTrustScoreSystem instance"""
    global _trust_score_system
    if _trust_score_system is None:
        _trust_score_system = ClinicalTrustScoreSystem()
    return _trust_score_system


# Request/Response Models
class IngestRequest(BaseModel):
    """Request model for multimodal ingestion"""
    patient_id: str = Field(..., description="Anonymized patient ID")
    age_group: Optional[str] = Field(None, description="Age group: pediatric, adult, elderly")
    region: Optional[str] = Field(None, description="Geographic region or clinic ID")
    comorbidities: List[str] = Field(default_factory=list, description="List of comorbidities")
    diagnosis: Optional[str] = Field(None, description="Diagnosis if available")
    outcome: Optional[str] = Field(None, description="Treatment outcome if available")


class IngestResponse(BaseModel):
    """Response model for ingestion"""
    status: str
    case_id: str
    point_ids: List[str]
    modalities_processed: List[Dict[str, Any]]
    soap_generated: bool
    message: str
    rag_suggestions: Optional[Dict[str, Any]] = Field(None, description="RAG-based clinical suggestions and insights")


class SOAPRequest(BaseModel):
    """Request model for SOAP note generation"""
    transcript: str = Field(..., description="Raw consultation transcript")
    patient_id: Optional[str] = Field(None, description="Anonymized patient ID")
    age_group: Optional[str] = Field(None, description="Age group")
    region: Optional[str] = Field(None, description="Region")
    comorbidities: List[str] = Field(default_factory=list, description="Comorbidities")


class SOAPResponse(BaseModel):
    """Response model for SOAP note"""
    case_id: str
    soap_note: Dict[str, str]  # S, O, A, P
    metadata: Dict[str, Any]
    point_ids: List[str]
    generated_at: str


class RecallRequest(BaseModel):
    """Request model for similar case recall"""
    query_text: Optional[str] = Field(None, description="Text query for similarity search")
    query_image_path: Optional[str] = Field(None, description="Path to image for similarity search")
    limit: int = Field(5, ge=1, le=200, description="Number of similar cases to return (higher limit for timeline queries)")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")
    patient_id: Optional[str] = Field(None, description="Filter by patient ID")
    age_group: Optional[str] = Field(None, description="Filter by age group")
    region: Optional[str] = Field(None, description="Filter by region")
    diagnosis: Optional[str] = Field(None, description="Filter by diagnosis")
    time_range_days: Optional[int] = Field(None, description="Filter by time range (days)")


class RecallResponse(BaseModel):
    """Response model for case recall"""
    query_type: str
    similar_cases: List[Dict[str, Any]]
    total_found: int
    latency_ms: float


class SummaryRequest(BaseModel):
    """Request model for context-aware summarization"""
    current_case: Dict[str, Any] = Field(..., description="Current case data")
    similar_cases: Optional[List[Dict[str, Any]]] = Field(None, description="Pre-retrieved similar cases")
    include_differential: bool = Field(True, description="Include differential diagnosis")
    include_treatment_plan: bool = Field(True, description="Include treatment recommendations")


class SummaryResponse(BaseModel):
    """Response model for case summary"""
    summary: str
    differential_diagnosis: List[Dict[str, Any]]
    treatment_recommendations: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    similar_cases_used: int


class LabReportRequest(BaseModel):
    """Request model for lab report normalization"""
    lab_data: Dict[str, Any] = Field(..., description="Lab report data (JSON format)")
    test_type: str = Field(..., description="Test type: CBC, LFT, RFT, etc.")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    timestamp: Optional[str] = Field(None, description="Report timestamp")


class LabReportResponse(BaseModel):
    """Response model for lab report"""
    normalized_data: Dict[str, Any]
    point_id: str
    embedding_generated: bool
    stored: bool


# Endpoints

@router.post("/ingest", response_model=IngestResponse)
async def ingest_multimodal(
    patient_id: str = Form(...),
    age_group: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    comorbidities: Optional[str] = Form(None),  # JSON string
    diagnosis: Optional[str] = Form(None),
    outcome: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    text_file: Optional[UploadFile] = File(None),
    transcript_text: Optional[str] = Form(None)
):
    """
    Multimodal Ingestion Endpoint
    
    Ingests audio consultations, text transcripts, lab reports, or images.
    Automatically detects input type and routes to appropriate processor.
    """
    try:
        logger.info(f"Received multimodal ingestion request for patient: {patient_id}")
        
        ingestion = get_case_ingestion()
        logger.info("Case ingestion orchestrator initialized")
        
        # Parse comorbidities if provided
        comorbidities_list = []
        if comorbidities:
            try:
                comorbidities_list = json.loads(comorbidities)
                logger.info(f"Parsed comorbidities: {comorbidities_list}")
            except Exception as parse_error:
                logger.warning(f"Failed to parse comorbidities as JSON: {parse_error}, treating as string")
                comorbidities_list = [comorbidities] if isinstance(comorbidities, str) else []
        
        # Create case metadata
        try:
            metadata = CaseMetadata(
                age_group=age_group,
                region=region,
                comorbidities=comorbidities_list,
                diagnosis=diagnosis,
                outcome=outcome
            )
            logger.info(f"Created case metadata: age_group={age_group}, region={region}, diagnosis={diagnosis}")
        except Exception as metadata_error:
            logger.error(f"Error creating CaseMetadata: {metadata_error}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Invalid metadata: {str(metadata_error)}")
        
        # Build modalities
        modalities = {}
        case_id = f"case_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{patient_id}"
        logger.info(f"Generated case_id: {case_id}")
        
        # Process text/transcript
        extracted_text = ""
        if transcript_text:
            try:
                extracted_text = transcript_text
                modalities["text"] = CaseModality(
                    modality_type="text",
                    content={"transcript": transcript_text}
                )
                logger.info(f"Added text modality from transcript_text ({len(transcript_text)} chars)")
            except Exception as text_error:
                logger.error(f"Error creating text modality from transcript_text: {text_error}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Error processing text: {str(text_error)}")
        elif text_file:
            try:
                # Check if it's a document file (PDF, DOCX) or plain text
                file_ext = Path(text_file.filename).suffix.lower() if text_file.filename else ".txt"
                
                if file_ext in ['.pdf', '.docx', '.doc']:
                    # Extract text from document
                    from src.utils.file_processor import FileProcessor
                    import tempfile
                    import io
                    
                    # Save file temporarily for processing
                    temp_dir = Path(tempfile.gettempdir())
                    doc_path = temp_dir / text_file.filename
                    
                    file_content = await text_file.read()
                    with open(doc_path, "wb") as f:
                        f.write(file_content)
                    
                    # Process document
                    doc_result = FileProcessor.process_file(str(doc_path))
                    extracted_text = doc_result.get("content", "") or doc_result.get("text", "")
                    
                    logger.info(f"Extracted text from {file_ext} document: {len(extracted_text)} chars")
                else:
                    # Plain text file
                    file_content = await text_file.read()
                    extracted_text = file_content.decode("utf-8")
                    logger.info(f"Read text from text_file: {len(extracted_text)} chars")
                
                # Add to modalities
                if "text" in modalities:
                    # Combine with existing text (e.g., from audio transcription)
                    existing_text = modalities["text"].content.get("transcript", "")
                    modalities["text"].content["transcript"] = f"{existing_text}\n\n[Document Content]\n{extracted_text}".strip()
                else:
                    modalities["text"] = CaseModality(
                        modality_type="text",
                        content={"transcript": extracted_text}
                    )
                    
            except Exception as text_file_error:
                logger.error(f"Error processing text_file: {text_file_error}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Error processing text file: {str(text_file_error)}")
        
        # Process audio - transcribe it to text
        audio_transcript = ""
        if audio_file:
            # Save audio file temporarily (cross-platform)
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            audio_path = temp_dir / audio_file.filename
            try:
                with open(audio_path, "wb") as f:
                    content = await audio_file.read()
                    f.write(content)
                
                # Transcribe audio using Deepgram
                try:
                    from src.api.transcription_ws_api import transcribe_audio_file
                    logger.info(f"Transcribing audio file: {audio_file.filename}")
                    
                    # Create a file-like object for transcription
                    import io
                    audio_file_for_transcription = io.BytesIO(content)
                    audio_file_for_transcription.name = audio_file.filename
                    
                    # Transcribe audio
                    transcription_result = await transcribe_audio_file(
                        audio_file=audio_file_for_transcription,
                        language="en-US",
                        model="nova-2",
                        smart_format=True,
                        punctuate=True,
                        diarize=True,
                        generate_soap=False  # We'll generate SOAP later
                    )
                    
                    if transcription_result.success and transcription_result.transcript:
                        audio_transcript = transcription_result.transcript
                        logger.info(f"✓ Audio transcribed: {len(audio_transcript)} characters")
                        
                        # Add transcribed text to text modality or create new one
                        if "text" in modalities:
                            # Combine with existing text
                            existing_text = modalities["text"].content.get("transcript", "")
                            modalities["text"].content["transcript"] = f"{existing_text}\n\n[Audio Transcription]\n{audio_transcript}".strip()
                        else:
                            # Create text modality from transcription
                            modalities["text"] = CaseModality(
                                modality_type="text",
                                content={"transcript": audio_transcript}
                            )
                    else:
                        logger.warning(f"Audio transcription failed: {transcription_result.error}")
                        # Still store audio modality even if transcription fails
                        modalities["audio"] = CaseModality(
                            modality_type="audio",
                            content={"audio_path": str(audio_path), "transcription_failed": True}
                        )
                except Exception as transcribe_error:
                    logger.warning(f"Error transcribing audio: {transcribe_error}, storing audio without transcription")
                    # Store audio modality even if transcription fails
                    modalities["audio"] = CaseModality(
                        modality_type="audio",
                        content={"audio_path": str(audio_path), "transcription_error": str(transcribe_error)}
                    )
                
            except Exception as audio_error:
                logger.error(f"Error saving audio file: {audio_error}")
                raise HTTPException(status_code=500, detail=f"Error processing audio file: {str(audio_error)}")
        
        # Process image
        if image_file:
            # Save image file temporarily (cross-platform)
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            image_path = temp_dir / image_file.filename
            try:
                with open(image_path, "wb") as f:
                    content = await image_file.read()
                    f.write(content)
                
                modalities["image"] = CaseModality(
                    modality_type="image",
                    content={"image_path": str(image_path)}
                )
            except Exception as image_error:
                logger.error(f"Error saving image file: {image_error}")
                raise HTTPException(status_code=500, detail=f"Error processing image file: {str(image_error)}")
        
        # If no modalities provided, create a text modality from form inputs
        # This ensures SOAP notes are generated even with form-only inputs
        if not modalities:
            logger.info("No modalities provided, creating text modality from form inputs")
            # Build a synthetic transcript from form inputs
            synthetic_transcript_parts = []
            
            if age_group:
                synthetic_transcript_parts.append(f"Patient age group: {age_group}")
            if region:
                synthetic_transcript_parts.append(f"Region: {region}")
            if comorbidities_list:
                synthetic_transcript_parts.append(f"Comorbidities: {', '.join(comorbidities_list)}")
            if diagnosis:
                synthetic_transcript_parts.append(f"Diagnosis: {diagnosis}")
            if outcome:
                synthetic_transcript_parts.append(f"Outcome: {outcome}")
            
            # Create a basic clinical note format
            if synthetic_transcript_parts:
                synthetic_transcript = "CLINICAL ENTRY:\n" + "\n".join(synthetic_transcript_parts)
            else:
                # Minimal transcript if only patient_id is provided
                synthetic_transcript = f"Patient consultation for patient ID: {patient_id}"
            
            modalities["text"] = CaseModality(
                modality_type="text",
                content={"transcript": synthetic_transcript}
            )
            extracted_text = synthetic_transcript
            logger.info(f"Created synthetic text modality from form inputs ({len(synthetic_transcript)} chars)")
        
        logger.info(f"Prepared {len(modalities)} modality(ies): {list(modalities.keys())}")
        
        # Create case
        try:
            case = Case(
                case_id=case_id,
                patient_id=patient_id,
                modalities=modalities,
                metadata=metadata
            )
            logger.info(f"Created Case object: {case_id}")
        except Exception as case_error:
            logger.error(f"Error creating Case object: {case_error}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Error creating case: {str(case_error)}")
        
        # Ingest case
        try:
            logger.info(f"Starting case ingestion for {case_id}...")
            result = ingestion.ingest_case(case, generate_soap=True)
            logger.info(f"Case ingestion completed: status={result.get('status')}")
        except Exception as ingest_error:
            logger.error(f"Error during case ingestion: {ingest_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error ingesting case: {str(ingest_error)}")
        
        # Also store in patient_memory_collection for patient history retrieval
        if result["status"] == "success":
            try:
                from src.storage.qdrant_storage import QdrantStorage
                from src.embeddings import BioBERTEmbeddingGenerator
                from src.storage.schema import StorageMetadata, ModalityType
                
                # Get patient memory storage
                patient_memory_storage = get_qdrant_storage(collection_name="patient_memory_collection")
                embedder = BioBERTEmbeddingGenerator()
                
                # Extract text content for patient record
                text_content = ""
                if transcript_text:
                    text_content = transcript_text
                elif text_file:
                    # Re-read text file content
                    await text_file.seek(0)  # Reset file pointer
                    text_content = (await text_file.read()).decode("utf-8")
                elif "text" in modalities:
                    text_content = modalities["text"].content.get("transcript", "")
                
                if text_content:
                    # Generate embedding
                    embedding = embedder.generate_embedding(text_content[:2000])  # Limit length
                    
                    # Create transcript data
                    transcript_data = {
                        "transcript": text_content[:5000],  # Store full transcript
                        "session_id": case.case_id,
                        "metadata": {
                            "patient_id": patient_id,
                            "age_group": age_group,
                            "region": region,
                            "comorbidities": comorbidities_list,
                            "diagnosis": diagnosis,
                            "outcome": outcome,
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "confidence": 1.0,
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Create metadata
                    metadata = StorageMetadata(
                        session_id=case.case_id,
                        patient_id=patient_id,
                        timestamp=datetime.now(timezone.utc),
                        modality=ModalityType.TEXT,
                        confidence=1.0
                    )
                    
                    # Store in patient_memory_collection
                    patient_memory_storage.store_transcript(transcript_data, embedding, metadata)
                    logger.info(f"✓ Stored patient record in patient_memory_collection for patient {patient_id}")
                    
            except Exception as patient_storage_error:
                # Don't fail the entire request if patient memory storage fails
                logger.warning(f"Failed to store patient record in patient_memory_collection: {patient_storage_error}")
        
        # Generate RAG-based suggestions if ingestion was successful
        rag_suggestions = None
        if result["status"] == "success":
            try:
                # Extract and combine all text sources for RAG query
                query_text = ""
                
                # Get text from various sources
                if transcript_text:
                    query_text = transcript_text
                elif "text" in modalities:
                    query_text = modalities["text"].content.get("transcript", "")
                
                # Also include audio transcript if available
                if audio_transcript and audio_transcript not in query_text:
                    query_text = f"{query_text}\n\n[Audio Transcription]\n{audio_transcript}".strip() if query_text else audio_transcript
                
                # Also include extracted document text if available
                if extracted_text and extracted_text not in query_text:
                    query_text = f"{query_text}\n\n[Document Content]\n{extracted_text}".strip() if query_text else extracted_text
                
                # Build comprehensive enriched query with all form inputs and parsed content
                if query_text and len(query_text.strip()) > 10:  # Only generate if we have meaningful text
                    # Build enriched query text combining all inputs
                    enriched_query_parts = []
                    
                    # Add main content (transcript/audio/document)
                    enriched_query_parts.append("PATIENT PRESENTATION:")
                    enriched_query_parts.append(query_text)
                    
                    # Add form inputs as structured context
                    enriched_query_parts.append("\nPATIENT INFORMATION:")
                    if age_group:
                        enriched_query_parts.append(f"Age Group: {age_group}")
                    if region:
                        enriched_query_parts.append(f"Region: {region}")
                    if comorbidities_list:
                        enriched_query_parts.append(f"Comorbidities: {', '.join(comorbidities_list)}")
                    if diagnosis:
                        enriched_query_parts.append(f"Current/Provisional Diagnosis: {diagnosis}")
                    if outcome:
                        enriched_query_parts.append(f"Outcome: {outcome}")
                    
                    enriched_query = "\n".join(enriched_query_parts)
                    
                    # Generate RAG insights with timeout protection
                    logger.info(f"Generating RAG-based suggestions for case {case.case_id}...")
                    
                    try:
                        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
                        
                        rag = get_clinical_rag()
                        
                        from ..rag.clinical_rag import RAGOptions
                        rag_options = RAGOptions(
                            retrieval_limit=5,
                            include_knowledge_base=True,  # Include knowledge base in retrieval
                            generate_differential_diagnoses=True,
                            generate_recommendations=True,
                            generate_summary=True,
                            temperature=0.3
                        )
                        
                        # Run RAG generation in thread pool with timeout
                        def run_rag_generation():
                            return rag.generate_insights(
                                query_text=enriched_query,
                                query_case=case,
                                options=rag_options
                            )
                        
                        # Use thread pool executor with timeout
                        executor = ThreadPoolExecutor(max_workers=1)
                        future = executor.submit(run_rag_generation)
                        
                        insight = None
                        try:
                            # Wait for RAG generation with 30 second timeout
                            insight = future.result(timeout=30.0)
                            
                            # Convert insight to dictionary for response
                            rag_suggestions = insight.to_dict()
                            logger.info(f"✓ RAG suggestions generated successfully")
                            
                        except FutureTimeoutError:
                            logger.warning(f"RAG generation timed out after 30 seconds for case {case.case_id}")
                            rag_suggestions = {
                                "error": "RAG generation timed out",
                                "message": "Clinical suggestions generation took too long. The patient data was stored successfully."
                            }
                            future.cancel()
                        except Exception as rag_exec_error:
                            logger.error(f"Error during RAG generation execution: {rag_exec_error}", exc_info=True)
                            rag_suggestions = {
                                "error": "RAG generation failed",
                                "message": str(rag_exec_error)
                            }
                        finally:
                            executor.shutdown(wait=False)
                            
                        # Store summary in knowledge base if available (only if RAG succeeded)
                        if insight and insight.summary:
                            try:
                                from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
                                from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
                                from src.embeddings import BioBERTEmbeddingGenerator
                                
                                # Get knowledge base storage
                                kb_storage = get_qdrant_storage(collection_name="clinical_kb_collection")
                                embedder = BioBERTEmbeddingGenerator()
                                
                                # Create summary document
                                summary_title = f"Patient Summary - {patient_id} - {case.case_id}"
                                summary_content = f"""Patient Summary for Case {case.case_id}

Patient ID: {patient_id}
Age Group: {age_group or 'Not specified'}
Region: {region or 'Not specified'}
Comorbidities: {', '.join(comorbidities_list) if comorbidities_list else 'None'}
Diagnosis: {diagnosis or 'Not specified'}
Outcome: {outcome or 'Not specified'}

CLINICAL SUMMARY:
{insight.summary}

DIFFERENTIAL DIAGNOSES:
{chr(10).join([f"- {dd.get('diagnosis', '')} (Confidence: {dd.get('confidence', 'N/A')})" for dd in insight.differential_diagnoses]) if insight.differential_diagnoses else 'None provided'}

RECOMMENDATIONS:
{chr(10).join([f"- {rec.title}: {rec.description} (Confidence: {rec.confidence:.2f})" for rec in insight.recommendations]) if insight.recommendations else 'None provided'}

Generated: {datetime.now(timezone.utc).isoformat()}
"""
                                
                                # Create document data
                                document_data = {
                                    "title": summary_title,
                                    "content": summary_content,
                                    "source": "HygiaAI Patient Summary",
                                    "author": "HygiaAI Clinical RAG",
                                    "year": datetime.now(timezone.utc).year,
                                    "provenance_url": f"https://hygiaai.local/patient-summary/{case.case_id}",
                                    "patient_id": patient_id,
                                    "case_id": case.case_id
                                }
                                
                                # Create metadata
                                kb_metadata = KnowledgeBaseMetadata(
                                    title=summary_title,
                                    source="HygiaAI Patient Summary",
                                    domain="guidelines",  # Use guidelines domain for patient summaries
                                    year=datetime.now(timezone.utc).year,
                                    embedding_type=EmbeddingType.TEXT,
                                    access_type=AccessType.RESTRICTED,  # Patient summaries are restricted
                                    provenance_url=f"https://hygiaai.local/patient-summary/{case.case_id}",
                                    author="HygiaAI Clinical RAG"
                                )
                                
                                # Initialize ingestion pipeline
                                ingestion_pipeline = KnowledgeIngestionPipeline(
                                    qdrant_storage=kb_storage,
                                    text_embedding_generator=lambda text: embedder.generate_embedding(text),
                                    chunk_size=512,
                                    chunk_overlap=50,
                                    enforce_open_access=False  # Allow patient summaries
                                )
                                
                                # Ingest summary into knowledge base
                                point_ids = ingestion_pipeline.ingest_document(
                                    document_data,
                                    metadata=kb_metadata
                                )
                                
                                logger.info(f"✓ Stored patient summary in knowledge base: {len(point_ids)} chunks")
                                
                            except Exception as kb_storage_error:
                                # Don't fail the request if knowledge base storage fails
                                logger.warning(f"Failed to store patient summary in knowledge base: {kb_storage_error}")
                                logger.debug(f"KB storage error details: {kb_storage_error}", exc_info=True)
                    
                    except Exception as rag_inner_error:
                        # Handle errors in the inner try block (RAG setup/execution)
                        logger.error(f"Error in RAG generation inner block: {rag_inner_error}", exc_info=True)
                        rag_suggestions = {
                            "error": "RAG generation failed",
                            "message": str(rag_inner_error)
                        }
                    
            except Exception as rag_error:
                # Don't fail the entire request if RAG generation fails
                logger.warning(f"Failed to generate RAG suggestions: {rag_error}")
                logger.debug(f"RAG error details: {rag_error}", exc_info=True)
                rag_suggestions = {
                    "error": "Failed to generate suggestions",
                    "message": str(rag_error)
                }
        
        return IngestResponse(
            status=result["status"],
            case_id=result["case_id"],
            point_ids=result["point_ids"],
            modalities_processed=result["metadata"].get("modalities_processed", []),
            soap_generated=result["metadata"].get("soap_generated", False),
            message="Case ingested successfully" if result["status"] == "success" else result.get("error", "Unknown error"),
            rag_suggestions=rag_suggestions
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in multimodal ingestion: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing multimodal input: {str(e)}")


@router.post("/soap", response_model=SOAPResponse)
async def generate_soap_note(request: SOAPRequest):
    """
    Automated SOAP Note Generation Endpoint
    
    Converts raw consultation transcripts to structured SOAP notes.
    Each SOAP field is embedded separately and stored in Qdrant.
    """
    try:
        soap_gen = get_soap_generator()
        ingestion = get_case_ingestion()
        
        # Generate SOAP note
        patient_metadata = {
            "age_group": request.age_group,
            "region": request.region,
            "comorbidities": request.comorbidities
        }
        
        soap_note = soap_gen.generate_soap(
            request.transcript,
            patient_metadata=patient_metadata
        )
        
        # Store SOAP note in Qdrant
        case_id = f"soap_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        if request.patient_id:
            case_id += f"_{request.patient_id}"
        
        metadata = CaseMetadata(
            age_group=request.age_group,
            region=request.region,
            comorbidities=request.comorbidities
        )
        
        case = Case(
            case_id=case_id,
            patient_id=request.patient_id or "unknown",
            modalities={
                "text": CaseModality(
                    modality_type="text",
                    content={"transcript": request.transcript}
                )
            },
            metadata=metadata
        )
        
        ingest_result = ingestion.ingest_case(case, generate_soap=False)  # SOAP already generated
        
        return SOAPResponse(
            case_id=case_id,
            soap_note={
                "subjective": soap_note.subjective,
                "objective": soap_note.objective,
                "assessment": soap_note.assessment,
                "plan": soap_note.plan
            },
            metadata=soap_note.metadata,
            point_ids=ingest_result.get("point_ids", []),
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating SOAP note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/soap/export/pdf")
async def export_soap_to_pdf(
    soap_note: str = Form(...),
    patient_info: Optional[str] = Form(None),
    clinician_info: Optional[str] = Form(None)
):
    """
    Export SOAP note to PDF format
    
    Accepts SOAP note data as JSON string and optional patient/clinician info,
    generates PDF using reportlab, and returns as file download.
    """
    try:
        from ..entity_extraction.soap_generator import SOAPNote as SOAPNoteClass
        import tempfile
        
        # Parse JSON strings
        try:
            soap_note_dict = json.loads(soap_note)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid SOAP note JSON format")
        
        patient_info_dict = None
        if patient_info:
            try:
                patient_info_dict = json.loads(patient_info)
            except json.JSONDecodeError:
                patient_info_dict = {"patient_id": patient_info}
        
        clinician_info_dict = None
        if clinician_info:
            try:
                clinician_info_dict = json.loads(clinician_info)
            except json.JSONDecodeError:
                clinician_info_dict = {"name": clinician_info}
        
        # Create SOAPNote object
        soap_note_obj = SOAPNoteClass(
            subjective=soap_note_dict.get("subjective", ""),
            objective=soap_note_dict.get("objective", ""),
            assessment=soap_note_dict.get("assessment", ""),
            plan=soap_note_dict.get("plan", ""),
            metadata=soap_note_dict.get("metadata", {})
        )
        
        # Create temporary file for PDF
        temp_dir = Path(tempfile.gettempdir())
        pdf_filename = f"soap_note_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = temp_dir / pdf_filename
        
        # Export to PDF
        success = soap_note_obj.export_to_pdf(
            str(pdf_path),
            patient_info=patient_info_dict,
            clinician_info=clinician_info_dict
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Check if file exists
        if not pdf_path.exists():
            raise HTTPException(status_code=500, detail="PDF file was not created")
        
        # Read file and return as streaming response
        def generate():
            with open(pdf_path, "rb") as f:
                while True:
                    chunk = f.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    yield chunk
            # Clean up temp file after streaming
            try:
                pdf_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file {pdf_path}: {e}")
        
        return StreamingResponse(
            generate(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={pdf_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting SOAP note to PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recall_case", response_model=RecallResponse)
async def recall_similar_cases(request: RecallRequest):
    """
    Instant Similar Case Recall Endpoint
    
    Input (audio/text/image/lab) → embedding → Qdrant → top 3–5 similar cases.
    Target latency: <300ms
    """
    try:
        import time
        start_time = time.time()
        
        retriever = get_case_retriever()
        
        # Determine query type and generate embedding
        # Allow empty query_text to list all cases (for dashboard/case viewer)
        if request.query_text is not None:  # Allow empty string
            query_type = "text"
        elif request.query_image_path:
            query_type = "image"
        elif request.patient_id:
            query_type = "text"  # Use text type even with empty query when patient_id is provided
        else:
            # Default to text type with empty query to list all cases
            query_type = "text"
            request.query_text = ""
        
        # Build retrieval options
        from ..retrieval.case_retrieval import RetrievalOptions
        
        options = RetrievalOptions(
            limit=request.limit,
            score_threshold=request.score_threshold,
            patient_id=request.patient_id,
            age_group=request.age_group,
            region=request.region,
            diagnosis=request.diagnosis
        )
        
        if request.time_range_days:
            end_time = datetime.now(timezone.utc)
            start_time_range = end_time - timedelta(days=request.time_range_days)
            options.time_range = {"gte": start_time_range, "lte": end_time}
        
        # If patient_id is provided, use keyword mode (filter-based) instead of semantic search
        # This is more efficient and accurate for patient ID lookups
        if request.patient_id and not request.query_text:
            options.mode = RetrievalMode.KEYWORD
        
        # Retrieve similar cases
        if query_type == "text":
            results = retriever.retrieve_similar_cases(
                query_text=request.query_text if request.query_text else None,
                options=options
            )
        else:  # image
            # For images, we'd need to generate CLIP embedding
            # For now, return error if image search not fully implemented
            raise HTTPException(status_code=501, detail="Image-based search not yet fully implemented")
        
        # Format results
        similar_cases = []
        for result in results[:request.limit]:
            # Extract patient_id from case_data payload
            patient_id = result.case_data.get("patient_id") if result.case_data else None
            
            # Extract SOAP note from case_data or modalities
            soap_note = None
            if result.case_data:
                soap_note = result.case_data.get("soap_note") or result.case_data.get("soap_notes")
            if not soap_note and result.modalities and result.modalities.get("text"):
                soap_note = result.modalities["text"].get("soap")
            
            # Build case_data dict with SOAP note included
            case_data_dict = result.case_data.copy() if result.case_data else {}
            if soap_note and "soap_note" not in case_data_dict:
                case_data_dict["soap_note"] = soap_note
            
            similar_cases.append({
                "case_id": result.case_id,
                "patient_id": patient_id,  # Include patient_id at top level for easy access
                "similarity_score": result.score,
                "semantic_score": result.semantic_score,
                "keyword_score": result.keyword_score,
                "metadata": result.metadata.dict() if result.metadata and hasattr(result.metadata, 'dict') else (result.metadata.model_dump() if result.metadata and hasattr(result.metadata, 'model_dump') else None),
                "case_data": case_data_dict,  # Include full case data with SOAP note
                "modalities": result.modalities
            })
        
        latency_ms = (time.time() - start_time) * 1000
        
        return RecallResponse(
            query_type=query_type,
            similar_cases=similar_cases,
            total_found=len(results),  # results is already a list
            latency_ms=latency_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in case recall: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=SummaryResponse)
async def generate_context_aware_summary(request: SummaryRequest):
    """
    Context-Aware Case Summarizer Endpoint
    
    Rewrites summary based on retrieved past cases.
    Generates differential diagnosis + recommended plan using LLM reasoning.
    """
    try:
        rag = get_clinical_rag()
        retriever = get_case_retriever()
        
        # Retrieve similar cases if not provided
        if not request.similar_cases:
            current_text = request.current_case.get("transcript") or request.current_case.get("text", "")
            if not current_text:
                raise HTTPException(status_code=400, detail="Current case must contain transcript or text")
            
            from ..retrieval.case_retrieval import RetrievalOptions
            options = RetrievalOptions(limit=5)
            
            retrieval_results = retriever.retrieve_similar_cases(
                query_text=current_text,
                options=options
            )
            
            similar_cases = [
                {
                    "case_id": result.case_id,
                    "similarity_score": result.score,
                    "metadata": result.metadata.dict() if result.metadata and hasattr(result.metadata, 'dict') else (result.metadata.model_dump() if result.metadata and hasattr(result.metadata, 'model_dump') else None),
                    "case_data": result.case_data
                }
                for result in retrieval_results
            ]
        else:
            similar_cases = request.similar_cases
        
        # Generate context-aware summary using RAG
        # Note: generate_insights returns a ClinicalInsight object, not a dict
        insight = rag.generate_insights(
            query_text=request.current_case.get("transcript") or request.current_case.get("text", ""),
            options=None  # Use default options
        )
        
        # Convert ClinicalInsight to response format
        differential_diagnosis = [
            {"diagnosis": d.get("diagnosis", ""), "confidence": d.get("confidence", 0.0)}
            for d in insight.differential_diagnoses
        ]
        
        treatment_recommendations = [
            {
                "type": rec.type,
                "title": rec.title,
                "description": rec.description,
                "confidence": rec.confidence,
                "priority": rec.priority
            }
            for rec in insight.recommendations
        ]
        
        confidence_scores = {
            "overall": insight.confidence_score or 0.0,
            "retrieval": len(similar_cases) / 5.0  # Normalize to 0-1
        }
        
        return SummaryResponse(
            summary=insight.summary or "",
            differential_diagnosis=differential_diagnosis,
            treatment_recommendations=treatment_recommendations,
            confidence_scores=confidence_scores,
            similar_cases_used=len(similar_cases)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lab_report", response_model=LabReportResponse)
async def normalize_lab_report(request: LabReportRequest):
    """
    Lab Report Normalization & Embedding Endpoint
    
    Converts CBC/LFT/RFT lab values into numerical/semantic formats.
    Stores as structured JSON + embedding in Qdrant.
    """
    try:
        storage = get_qdrant_storage()
        from ..embeddings import BioBERTEmbeddingGenerator
        
        embedder = BioBERTEmbeddingGenerator()
        
        # Normalize lab data
        normalized_data = {
            "test_type": request.test_type,
            "patient_id": request.patient_id,
            "timestamp": request.timestamp or datetime.now(timezone.utc).isoformat(),
            "values": {}
        }
        
        # Normalize based on test type
        if request.test_type.upper() == "CBC":
            # Complete Blood Count normalization
            for key, value in request.lab_data.items():
                normalized_data["values"][key.lower()] = {
                    "value": float(value) if isinstance(value, (int, float, str)) and str(value).replace('.', '').isdigit() else value,
                    "unit": _infer_cbc_unit(key),
                    "normal_range": _get_cbc_normal_range(key)
                }
        elif request.test_type.upper() in ["LFT", "LIVER"]:
            # Liver Function Test normalization
            for key, value in request.lab_data.items():
                normalized_data["values"][key.lower()] = {
                    "value": float(value) if isinstance(value, (int, float, str)) and str(value).replace('.', '').isdigit() else value,
                    "unit": _infer_lft_unit(key),
                    "normal_range": _get_lft_normal_range(key)
                }
        elif request.test_type.upper() in ["RFT", "RENAL"]:
            # Renal Function Test normalization
            for key, value in request.lab_data.items():
                normalized_data["values"][key.lower()] = {
                    "value": float(value) if isinstance(value, (int, float, str)) and str(value).replace('.', '').isdigit() else value,
                    "unit": _infer_rft_unit(key),
                    "normal_range": _get_rft_normal_range(key)
                }
        else:
            # Generic normalization
            normalized_data["values"] = request.lab_data
        
        # Generate embedding from lab data text representation
        lab_text = f"{request.test_type}: {str(normalized_data['values'])}"
        embedding = embedder.generate_embedding(lab_text)
        
        # Store in Qdrant
        point_id = f"lab_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        if request.patient_id:
            point_id += f"_{request.patient_id}"
        
        from qdrant_client.models import PointStruct
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "type": "lab_report",
                "test_type": request.test_type,
                "normalized_data": normalized_data,
                "timestamp": normalized_data["timestamp"]
            }
        )
        
        storage.client.upsert(
            collection_name="hygiaai_cases",
            points=[point]
        )
        
        return LabReportResponse(
            normalized_data=normalized_data,
            point_id=point_id,
            embedding_generated=True,
            stored=True
        )
        
    except Exception as e:
        logger.error(f"Error normalizing lab report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions for lab report normalization
def _infer_cbc_unit(test_name: str) -> str:
    """Infer unit for CBC test"""
    test_lower = test_name.lower()
    if "hemoglobin" in test_lower or "hb" in test_lower:
        return "g/dL"
    elif "hematocrit" in test_lower or "hct" in test_lower:
        return "%"
    elif "wbc" in test_lower or "white" in test_lower:
        return "cells/μL"
    elif "platelet" in test_lower or "plt" in test_lower:
        return "cells/μL"
    return "units"


def _get_cbc_normal_range(test_name: str) -> Dict[str, float]:
    """Get normal range for CBC test"""
    test_lower = test_name.lower()
    if "hemoglobin" in test_lower or "hb" in test_lower:
        return {"min": 12.0, "max": 16.0}
    elif "hematocrit" in test_lower or "hct" in test_lower:
        return {"min": 36.0, "max": 46.0}
    elif "wbc" in test_lower or "white" in test_lower:
        return {"min": 4000, "max": 11000}
    elif "platelet" in test_lower or "plt" in test_lower:
        return {"min": 150000, "max": 450000}
    return {"min": 0, "max": 0}


def _infer_lft_unit(test_name: str) -> str:
    """Infer unit for LFT test"""
    test_lower = test_name.lower()
    if "alt" in test_lower or "ast" in test_lower or "sgot" in test_lower or "sgpt" in test_lower:
        return "U/L"
    elif "bilirubin" in test_lower:
        return "mg/dL"
    elif "albumin" in test_lower:
        return "g/dL"
    return "U/L"


def _get_lft_normal_range(test_name: str) -> Dict[str, float]:
    """Get normal range for LFT test"""
    test_lower = test_name.lower()
    if "alt" in test_lower or "sgpt" in test_lower:
        return {"min": 7, "max": 56}
    elif "ast" in test_lower or "sgot" in test_lower:
        return {"min": 10, "max": 40}
    elif "bilirubin" in test_lower:
        return {"min": 0.1, "max": 1.2}
    elif "albumin" in test_lower:
        return {"min": 3.5, "max": 5.0}
    return {"min": 0, "max": 0}


def _infer_rft_unit(test_name: str) -> str:
    """Infer unit for RFT test"""
    test_lower = test_name.lower()
    if "creatinine" in test_lower:
        return "mg/dL"
    elif "urea" in test_lower or "bun" in test_lower:
        return "mg/dL"
    elif "egfr" in test_lower or "gfr" in test_lower:
        return "mL/min/1.73m²"
    return "mg/dL"


def _get_rft_normal_range(test_name: str) -> Dict[str, float]:
    """Get normal range for RFT test"""
    test_lower = test_name.lower()
    if "creatinine" in test_lower:
        return {"min": 0.6, "max": 1.2}
    elif "urea" in test_lower or "bun" in test_lower:
        return {"min": 7, "max": 20}
    elif "egfr" in test_lower or "gfr" in test_lower:
        return {"min": 90, "max": 120}
    return {"min": 0, "max": 0}


# Knowledge Intelligence & Trend Analysis Endpoints

class TemporalClusteringRequest(BaseModel):
    """Request for temporal clustering"""
    time_granularity: str = Field(default="weekly", description="Time granularity: weekly, monthly, seasonal")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    region: Optional[str] = None
    min_cluster_size: int = Field(default=3, ge=2)


class TemporalClusteringResponse(BaseModel):
    """Response for temporal clustering"""
    clusters: List[Dict[str, Any]]
    time_granularity: str
    total_cases_analyzed: int
    clusters_by_time_window: Dict[str, List[int]]
    pattern_insights: List[Dict[str, Any]]
    timestamp: str


class RegionalAnalyticsRequest(BaseModel):
    """Request for regional health analytics"""
    region: str = Field(..., description="Region to analyze")
    time_window_days: int = Field(default=30, ge=1, le=365)
    compare_with_previous: bool = Field(default=True)


class RegionalAnalyticsResponse(BaseModel):
    """Response for regional health analytics"""
    region: str
    time_period: Dict[str, str]
    disease_trends: List[Dict[str, Any]]
    common_complaints: List[Dict[str, Any]]
    treatment_success_rates: List[Dict[str, Any]]
    outbreak_alerts: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: str


class TrustScoreRequest(BaseModel):
    """Request for trust score calculation"""
    case_id: str
    similar_cases: Optional[List[Dict[str, Any]]] = None
    query_similarity_score: Optional[float] = None


class TrustScoreResponse(BaseModel):
    """Response for trust score"""
    case_id: str
    overall_score: float
    similarity_score: float
    source_reliability: float
    recency_score: float
    agreement_score: float
    confidence_level: str
    factors: Dict[str, Any]
    explanation: str


@router.post("/temporal_clustering", response_model=TemporalClusteringResponse)
async def perform_temporal_clustering(request: TemporalClusteringRequest):
    """
    Cross-Patient Temporal Clustering Endpoint
    
    Identifies clusters by time (week/month/season), location, symptom similarity, and lab pattern similarity.
    """
    try:
        clustering_service = get_temporal_clustering()
        
        # Parse time parameters
        start_time = None
        end_time = None
        if request.start_time:
            start_time = datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
        if request.end_time:
            end_time = datetime.fromisoformat(request.end_time.replace("Z", "+00:00"))
        
        # Perform clustering
        result = clustering_service.cluster_by_temporal_window(
            time_granularity=request.time_granularity,
            start_time=start_time,
            end_time=end_time,
            region=request.region,
            min_cluster_size=request.min_cluster_size
        )
        
        # Convert clusters to dict
        clusters_dict = []
        for cluster in result.clusters:
            clusters_dict.append({
                "cluster_id": cluster.cluster_id,
                "case_ids": cluster.case_ids,
                "time_window": {
                    "start": cluster.time_window[0].isoformat(),
                    "end": cluster.time_window[1].isoformat()
                },
                "characteristics": cluster.characteristics,
                "symptoms": cluster.symptoms,
                "diagnoses": cluster.diagnoses,
                "lab_patterns": cluster.lab_patterns,
                "locations": cluster.locations,
                "size": cluster.size,
                "density_score": cluster.density_score
            })
        
        return TemporalClusteringResponse(
            clusters=clusters_dict,
            time_granularity=result.time_granularity,
            total_cases_analyzed=result.total_cases_analyzed,
            clusters_by_time_window=result.clusters_by_time_window,
            pattern_insights=result.pattern_insights,
            timestamp=result.timestamp.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in temporal clustering: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regional_analytics", response_model=RegionalAnalyticsResponse)
async def analyze_regional_health(request: RegionalAnalyticsRequest):
    """
    Regional Health Trend Analytics Endpoint
    
    Tracks rising diseases, common complaints, treatment success rates, and local outbreaks.
    """
    try:
        analytics_service = get_regional_analytics()
        
        # Generate regional health report
        report = analytics_service.analyze_regional_health(
            region=request.region,
            time_window_days=request.time_window_days,
            compare_with_previous=request.compare_with_previous
        )
        
        # Convert to response format
        disease_trends_dict = []
        for trend in report.disease_trends:
            disease_trends_dict.append({
                "disease_name": trend.disease_name,
                "region": trend.region,
                "current_frequency": trend.current_frequency,
                "previous_frequency": trend.previous_frequency,
                "trend_direction": trend.trend_direction,
                "change_percentage": trend.change_percentage,
                "time_period": {
                    "start": trend.time_period["start"].isoformat(),
                    "end": trend.time_period["end"].isoformat()
                }
            })
        
        treatment_success_dict = []
        for treatment in report.treatment_success_rates:
            treatment_success_dict.append({
                "treatment": treatment.treatment,
                "region": treatment.region,
                "success_rate": treatment.success_rate,
                "total_cases": treatment.total_cases,
                "successful_outcomes": treatment.successful_outcomes,
                "time_period": {
                    "start": treatment.time_period["start"].isoformat(),
                    "end": treatment.time_period["end"].isoformat()
                }
            })
        
        return RegionalAnalyticsResponse(
            region=report.region,
            time_period={
                "start": report.time_period["start"].isoformat(),
                "end": report.time_period["end"].isoformat()
            },
            disease_trends=disease_trends_dict,
            common_complaints=report.common_complaints,
            treatment_success_rates=treatment_success_dict,
            outbreak_alerts=report.outbreak_alerts,
            summary=report.summary,
            generated_at=report.generated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in regional analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trust_score", response_model=TrustScoreResponse)
async def calculate_trust_score(request: TrustScoreRequest):
    """
    Clinical Trust Score System Endpoint
    
    Calculates confidence scores based on embedding similarity, source reliability, recency, and cross-case agreement.
    """
    try:
        trust_system = get_trust_score_system()
        retriever = get_case_retriever()
        
        # Retrieve the case
        from ..retrieval.case_retrieval import RetrievalOptions
        options = RetrievalOptions(limit=1)
        
        # For now, we'll need to get the case by ID
        # This is a simplified version - in production, you'd have a get_case_by_id method
        if not request.similar_cases:
            # Retrieve similar cases for agreement analysis
            # Note: This is a simplified approach
            # In production, you'd retrieve the case first, then find similar cases
            similar_results = retriever.retrieve_similar_cases(
                query_text="",  # Empty query to get recent cases
                options=RetrievalOptions(limit=10)
            )
        else:
            # Convert similar cases from request to RetrievalResult objects
            # This is a simplified conversion
            similar_results = []
            for case_dict in request.similar_cases:
                # Create a mock RetrievalResult from dict
                # In production, you'd have proper conversion
                from ..retrieval.case_retrieval import RetrievalResult
                similar_results.append(RetrievalResult(
                    case_id=case_dict.get("case_id", ""),
                    score=case_dict.get("similarity_score", 0.0),
                    case_data=case_dict.get("case_data", {}),
                    metadata=None,
                    modalities=[]
                ))
        
        # Get the primary case (first result or from request)
        if request.case_id:
            # Calculate trust score for the specified case
            trust_score = trust_system.calculate_trust_score(
                case_id=request.case_id,
                similar_cases=similar_results
            )
        else:
            # Use first similar case
            if similar_results:
                primary_case_id = similar_results[0].case_id
                trust_score = trust_system.calculate_trust_score(
                    case_id=primary_case_id,
                    similar_cases=similar_results
                )
            else:
                raise HTTPException(status_code=400, detail="No cases available for trust score calculation")
        
        return TrustScoreResponse(
            case_id=trust_score.case_id,
            overall_score=trust_score.overall_score,
            confidence_level=trust_score.confidence_level,
            factors=trust_score.breakdown.dict() if hasattr(trust_score.breakdown, 'dict') else trust_score.breakdown.model_dump(),
            explanation=trust_score.explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating trust score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge Base Search Endpoints

class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge base search"""
    query: str = Field("", description="Search query text. Empty string returns all entries.")
    domain: Optional[str] = Field(None, description="Filter by domain (e.g., 'pathology', 'pharmacology', 'guidelines')")
    source: Optional[str] = Field(None, description="Filter by source")
    year_range: Optional[Dict[str, int]] = Field(None, description="Filter by year range: {'min': 2020, 'max': 2024}")
    limit: int = Field(100, ge=1, le=500, description="Number of results to return")
    score_threshold: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score")


class KnowledgeEntry(BaseModel):
    """Knowledge base entry model"""
    id: str
    title: str
    content: str
    source: str
    domain: Optional[str] = None
    year: Optional[int] = None
    provenance_url: Optional[str] = None
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    """Response model for knowledge base search"""
    query: str
    entries: List[KnowledgeEntry]
    total_found: int
    domains: List[str] = Field(default_factory=list, description="Available domains in results")
    sources: List[str] = Field(default_factory=list, description="Available sources in results")
    latency_ms: float


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_base(request: KnowledgeSearchRequest):
    """
    Search Knowledge Base Endpoint
    
    Searches the medical knowledge base for relevant documents, guidelines, and information.
    """
    try:
        import time
        start_time = time.time()
        
        # Use clinical_kb_collection for knowledge base searches
        knowledge_storage = get_qdrant_storage(collection_name="clinical_kb_collection")
        
        # Check if collection exists, create if it doesn't
        try:
            knowledge_storage.get_collection_info()
        except Exception as e:
            # Collection might not exist, try to create it
            logger.warning(f"Collection 'clinical_kb_collection' not found, attempting to create: {e}")
            # The collection will be created automatically by QdrantStorage._ensure_collection()
            # Re-initialize to trigger collection creation
            knowledge_storage = get_qdrant_storage(collection_name="clinical_kb_collection")
        
        # Build filters
        filters = {}
        if request.domain:
            filters["domain"] = request.domain
        if request.source:
            filters["source"] = request.source
        if request.year_range:
            if "min" in request.year_range:
                filters["year"] = {"gte": request.year_range["min"]}
            if "max" in request.year_range:
                if "year" in filters:
                    filters["year"]["lte"] = request.year_range["max"]
                else:
                    filters["year"] = {"lte": request.year_range["max"]}
        
        # If query is empty, scroll through all entries instead of searching
        if not request.query or not request.query.strip():
            # Scroll through all entries
            # Note: We'll filter client-side if filters are provided
            scroll_result = knowledge_storage.client.scroll(
                collection_name="clinical_kb_collection",
                limit=request.limit * 2,  # Get more to account for filtering
                with_payload=True,
                with_vectors=False
            )
            
            results = []
            for point in scroll_result[0]:
                payload = point.payload or {}
                
                # Apply filters if provided
                matches = True
                if filters:
                    if "domain" in filters and payload.get("domain") != filters["domain"]:
                        matches = False
                    if "source" in filters and payload.get("source") != filters["source"]:
                        matches = False
                    if "year" in filters:
                        year_val = payload.get("year")
                        if year_val:
                            year_val = int(year_val) if isinstance(year_val, (int, float, str)) else None
                            if year_val:
                                if "gte" in filters["year"] and year_val < filters["year"]["gte"]:
                                    matches = False
                                if "lte" in filters["year"] and year_val > filters["year"]["lte"]:
                                    matches = False
                        else:
                            matches = False
                
                if matches:
                    results.append({
                        "id": point.id,
                        "payload": payload,
                        "score": 1.0  # All entries shown when no query
                    })
                    
                    # Stop if we have enough results
                    if len(results) >= request.limit:
                        break
        else:
            # Perform vector search with query
            from src.embeddings import BioBERTEmbeddingGenerator
            embedder = BioBERTEmbeddingGenerator()
            
            # Generate query embedding
            query_embedding = embedder.generate_embedding(request.query)
            
            # Search knowledge base collection
            results = knowledge_storage.search_with_filters(
                query_embedding=query_embedding,
                filters=filters if filters else None,
                limit=request.limit,
                score_threshold=request.score_threshold
            )
        
        # Format results
        entries = []
        domains = set()
        sources = set()
        
        for result in results:
            payload = result.get("payload", {})
            score = result.get("score", 0.0)
            
            entry = KnowledgeEntry(
                id=result.get("id", ""),
                title=payload.get("title", "Untitled"),
                content=payload.get("content", payload.get("text", "")),
                source=payload.get("source", "Unknown"),
                domain=payload.get("domain"),
                year=payload.get("year"),
                provenance_url=payload.get("provenance_url"),
                similarity_score=score,
                metadata=payload
            )
            entries.append(entry)
            
            if entry.domain:
                domains.add(entry.domain)
            if entry.source:
                sources.add(entry.source)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return KnowledgeSearchResponse(
            query=request.query,
            entries=entries,
            total_found=len(results),
            domains=sorted(list(domains)),
            sources=sorted(list(sources)),
            latency_ms=latency_ms
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error searching knowledge base: {e}", exc_info=True)
        
        # Check if it's a collection not found error
        if "not found" in error_msg.lower() or "404" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail=f"Knowledge base collection not found. Please run: python scripts/ingest_knowledge_base.py to populate the knowledge base."
            )
        
        raise HTTPException(status_code=500, detail=f"Error searching knowledge base: {error_msg}")


@router.get("/knowledge/domains", response_model=List[str])
async def get_knowledge_domains():
    """
    Get available knowledge base domains
    """
    try:
        # Use clinical_kb_collection for knowledge base searches
        knowledge_storage = get_qdrant_storage(collection_name="clinical_kb_collection")
        
        # Scroll through knowledge base to get unique domains
        # Note: This is a simplified approach. In production, you'd maintain a separate index
        try:
            scroll_result = knowledge_storage.client.scroll(
                collection_name=knowledge_storage.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
        except Exception as scroll_error:
            logger.warning(f"Error scrolling collection for domains: {scroll_error}")
            return []  # Return empty list if collection doesn't exist or is empty
        
        domains = set()
        for point in scroll_result[0]:
            payload = point.payload or {}
            if "domain" in payload:
                domains.add(payload["domain"])
        
        return sorted(list(domains))
        
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        return []


@router.get("/knowledge/sources", response_model=List[str])
async def get_knowledge_sources():
    """
    Get available knowledge base sources
    """
    try:
        # Use clinical_kb_collection for knowledge base searches
        knowledge_storage = get_qdrant_storage(collection_name="clinical_kb_collection")
        
        # Scroll through knowledge base to get unique sources
        try:
            scroll_result = knowledge_storage.client.scroll(
                collection_name=knowledge_storage.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
        except Exception as scroll_error:
            logger.warning(f"Error scrolling collection for sources: {scroll_error}")
            return []  # Return empty list if collection doesn't exist or is empty
        
        sources = set()
        for point in scroll_result[0]:
            payload = point.payload or {}
            if "source" in payload:
                sources.add(payload["source"])
        
        return sorted(list(sources))
        
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        return []


@router.post("/knowledge/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    domain: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    author: Optional[str] = Form(None)
):
    """
    Upload and process a file for knowledge base ingestion
    
    Supports: PDF, DOCX, TXT, MD files
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Process file to extract text
        logger.info(f"Processing file: {file.filename}")
        processed = FileProcessor.process_file(file.filename, file_content)
        
        # Prepare document data
        document_data = {
            "title": processed.get("title", Path(file.filename).stem),
            "content": processed.get("content", processed.get("text", "")),
            "text": processed.get("text", processed.get("content", "")),
            "source": source or "User Upload",
            "domain": domain or "general",
            "year": year or datetime.now(timezone.utc).year,
            "author": author or processed.get("metadata", {}).get("author", ""),
            "file_type": processed.get("file_type", file_ext[1:]),
            "filename": file.filename,
            "provenance_url": f"https://hygiaai.local/user-upload/{file.filename}",
            "version": "1.0",
            **processed.get("metadata", {})
        }
        
        # Create metadata
        metadata = KnowledgeBaseMetadata(
            title=document_data["title"],
            source=document_data["source"],
            domain=document_data["domain"],
            year=document_data["year"],
            embedding_type=EmbeddingType.TEXT,
            access_type=AccessType.OPEN,
            provenance_url=document_data["provenance_url"],
            author=document_data["author"],
            version="1.0"
        )
        
        # Initialize knowledge base storage - use clinical_kb_collection
        knowledge_storage = get_qdrant_storage(collection_name="clinical_kb_collection")
        
        # Initialize embedding generator
        embedder = BioBERTEmbeddingGenerator()
        
        # Initialize ingestion pipeline
        # Disable license checking for manual uploads - allow any content to be uploaded
        ingestion_pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=knowledge_storage,
            text_embedding_generator=lambda text: embedder.generate_embedding(text),
            chunk_size=512,
            chunk_overlap=50,
            enforce_open_access=False  # Bypass license validation for manual uploads
        )
        
        # Ingest document
        import time
        start_time = time.time()
        logger.info(f"Ingesting document: {document_data['title']} (size: {len(file_content)} bytes)")
        
        # Get text length for progress estimation
        text_length = len(document_data.get("text", "") or document_data.get("content", ""))
        estimated_chunks = max(1, text_length // 512)  # Rough estimate
        logger.info(f"Estimated chunks: {estimated_chunks}, text length: {text_length} characters")
        
        point_ids = ingestion_pipeline.ingest_document(document_data, metadata=metadata)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully ingested document in {elapsed_time:.2f}s: {len(point_ids)} chunks created")
        
        return {
            "success": True,
            "message": f"Successfully uploaded and processed {file.filename}",
            "document_id": point_ids[0] if point_ids else None,
            "chunks_created": len(point_ids),
            "title": document_data["title"],
            "domain": document_data["domain"],
            "source": document_data["source"],
            "processing_time_seconds": round(elapsed_time, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading knowledge file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

