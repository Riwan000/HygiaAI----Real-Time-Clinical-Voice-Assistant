"""
SOAP RAG Enhancer

Uses Retrieval-Augmented Generation (RAG) with medical knowledge base
to enhance SOAP note generation with accurate medical information.
"""

import logging
from typing import List, Dict, Any, Optional
from src.storage.qdrant_storage import QdrantStorage
from src.embeddings import BioBERTEmbeddingGenerator
from src.entity_extraction.medical_ner import MedicalEntity, EntityType

logger = logging.getLogger(__name__)


class SOAPRAGEnhancer:
    """
    Enhances SOAP note generation using RAG from medical knowledge base
    
    Features:
    - Retrieves relevant medical knowledge for context
    - Enhances entity extraction with knowledge base
    - Provides structured templates for SOAP sections
    - Validates extracted information against medical knowledge
    """
    
    def __init__(
        self,
        qdrant_storage: Optional[QdrantStorage] = None,
        text_embedding_generator: Optional[BioBERTEmbeddingGenerator] = None
    ):
        """
        Initialize SOAP RAG enhancer
        
        Args:
            qdrant_storage: QdrantStorage instance for knowledge base
            text_embedding_generator: BioBERT embedding generator
        """
        self.storage = qdrant_storage
        self.embedding_generator = text_embedding_generator or BioBERTEmbeddingGenerator()
        
        if not self.storage:
            # Initialize default storage
            import os
            self.storage = QdrantStorage(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6334")),
                api_key=os.getenv("QDRANT_API_KEY"),
                collection_name="hygiaai_knowledge_base",
                vector_size=768,
                enable_encryption=False,
                enable_deidentification=False
            )
        
        logger.info("SOAP RAG enhancer initialized")
    
    def retrieve_relevant_knowledge(
        self,
        query: str,
        top_k: int = 3,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant medical knowledge from knowledge base
        
        Args:
            query: Search query
            top_k: Number of results to return
            domain: Optional domain filter (e.g., "clinical_documentation", "pharmacology")
            
        Returns:
            List of relevant knowledge documents
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Build filters
            filters = {}
            if domain:
                filters["domain"] = domain
            
            # Search knowledge base
            results = self.storage.search_with_filters(
                query_embedding=query_embedding,
                filters=filters if filters else None,
                limit=top_k,
                score_threshold=0.3  # Minimum similarity threshold
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")
            return []
    
    def enhance_subjective_extraction(
        self,
        transcript: str,
        entities: List[MedicalEntity]
    ) -> Dict[str, Any]:
        """
        Enhance subjective section extraction using knowledge base
        
        Args:
            transcript: Consultation transcript
            entities: Extracted medical entities
            
        Returns:
            Enhanced extraction with knowledge base context
        """
        # Retrieve SOAP guidelines
        guidelines = self.retrieve_relevant_knowledge(
            "SOAP note subjective section chief complaint history of present illness",
            domain="clinical_documentation"
        )
        
        # Retrieve symptom patterns
        symptoms = [e.text for e in entities if e.entity_type == EntityType.SYMPTOM]
        symptom_knowledge = []
        if symptoms:
            symptom_query = f"common symptoms {', '.join(symptoms[:3])}"
            symptom_knowledge = self.retrieve_relevant_knowledge(
                symptom_query,
                domain="clinical_patterns"
            )
        
        return {
            "guidelines": guidelines,
            "symptom_knowledge": symptom_knowledge,
            "enhanced_entities": entities
        }
    
    def enhance_objective_extraction(
        self,
        transcript: str,
        entities: List[MedicalEntity]
    ) -> Dict[str, Any]:
        """
        Enhance objective section extraction using knowledge base
        
        Args:
            transcript: Consultation transcript
            entities: Extracted medical entities
            
        Returns:
            Enhanced extraction with knowledge base context
        """
        # Retrieve vital signs reference
        vitals = [e.text for e in entities if e.entity_type == EntityType.VITAL_SIGN]
        vital_knowledge = []
        if vitals:
            vital_query = "normal vital signs blood pressure heart rate temperature"
            vital_knowledge = self.retrieve_relevant_knowledge(
                vital_query,
                domain="clinical_reference"
            )
        
        # Retrieve physical exam patterns
        exam_knowledge = self.retrieve_relevant_knowledge(
            "physical examination findings objective observations",
            domain="clinical_documentation"
        )
        
        return {
            "vital_knowledge": vital_knowledge,
            "exam_knowledge": exam_knowledge,
            "enhanced_entities": entities
        }
    
    def enhance_assessment_generation(
        self,
        transcript: str,
        entities: List[MedicalEntity],
        subjective: str,
        objective: str
    ) -> Dict[str, Any]:
        """
        Enhance assessment generation using knowledge base
        
        Args:
            transcript: Consultation transcript
            entities: Extracted medical entities
            subjective: Subjective section text
            objective: Objective section text
            
        Returns:
            Enhanced assessment with diagnostic knowledge
        """
        # Retrieve diagnostic patterns
        diagnoses = [e.text for e in entities if e.entity_type == EntityType.DIAGNOSIS]
        diagnostic_knowledge = []
        if diagnoses:
            diag_query = f"diagnosis {', '.join(diagnoses[:2])} diagnostic criteria"
            diagnostic_knowledge = self.retrieve_relevant_knowledge(
                diag_query,
                domain="diagnostics"
            )
        
        # Retrieve clinical reasoning patterns
        reasoning_knowledge = self.retrieve_relevant_knowledge(
            "clinical assessment impression differential diagnosis",
            domain="clinical_documentation"
        )
        
        return {
            "diagnostic_knowledge": diagnostic_knowledge,
            "reasoning_knowledge": reasoning_knowledge,
            "enhanced_entities": entities
        }
    
    def enhance_plan_generation(
        self,
        transcript: str,
        entities: List[MedicalEntity],
        assessment: str
    ) -> Dict[str, Any]:
        """
        Enhance plan generation using knowledge base
        
        Args:
            transcript: Consultation transcript
            entities: Extracted medical entities
            assessment: Assessment section text
            
        Returns:
            Enhanced plan with treatment knowledge
        """
        # Retrieve medication information
        medications = [e.text for e in entities if e.entity_type == EntityType.MEDICATION]
        medication_knowledge = []
        if medications:
            med_query = f"medications {', '.join(medications[:2])} dosage administration"
            medication_knowledge = self.retrieve_relevant_knowledge(
                med_query,
                domain="pharmacology"
            )
        
        # Retrieve treatment plan guidelines
        treatment_knowledge = self.retrieve_relevant_knowledge(
            "treatment plan follow-up instructions patient education",
            domain="clinical_documentation"
        )
        
        return {
            "medication_knowledge": medication_knowledge,
            "treatment_knowledge": treatment_knowledge,
            "enhanced_entities": entities
        }
    
    def format_knowledge_context(self, knowledge_results: List[Dict[str, Any]]) -> str:
        """
        Format knowledge base results into context string
        
        Args:
            knowledge_results: List of knowledge base search results
            
        Returns:
            Formatted context string
        """
        if not knowledge_results:
            return ""
        
        context_parts = []
        for result in knowledge_results:
            payload = result.get("payload", {})
            text = payload.get("text", "") or payload.get("content", "")
            title = payload.get("title", "")
            
            if text:
                # Extract relevant snippet (first 200 chars)
                snippet = text[:200] + "..." if len(text) > 200 else text
                context_parts.append(f"[{title}]: {snippet}")
        
        return "\n".join(context_parts)

