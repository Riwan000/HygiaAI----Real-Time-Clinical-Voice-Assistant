"""
Unit tests for Clinical RAG Module

Tests:
- RAG pipeline architecture
- Context retrieval and aggregation
- LLM integration
- Response parsing
- Recommendation generation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.rag.clinical_rag import (
    ClinicalRAG,
    ClinicalInsight,
    Recommendation,
    RAGOptions,
    LLMProvider,
)
from src.retrieval import CaseRetriever, RetrievalResult, RetrievalMode
from src.models import Case, CaseMetadata, CaseModality


class TestRAGOptions:
    """Test RAGOptions dataclass"""
    
    def test_default_options(self):
        """Test default RAG options"""
        options = RAGOptions()
        
        assert options.retrieval_limit == 5
        assert options.retrieval_mode == RetrievalMode.HYBRID
        assert options.llm_provider == LLMProvider.OPENAI
        assert options.llm_model == "gpt-4"
        assert options.temperature == 0.3
        assert options.max_tokens == 2000
        assert options.include_similar_cases is True
        assert options.generate_differential_diagnoses is True
        assert options.generate_recommendations is True
    
    def test_custom_options(self):
        """Test custom RAG options"""
        options = RAGOptions(
            retrieval_limit=10,
            retrieval_mode=RetrievalMode.SEMANTIC,
            llm_provider=LLMProvider.ANTHROPIC,
            llm_model="claude-3-opus",
            temperature=0.2,
            max_tokens=3000,
            generate_summary=False
        )
        
        assert options.retrieval_limit == 10
        assert options.retrieval_mode == RetrievalMode.SEMANTIC
        assert options.llm_provider == LLMProvider.ANTHROPIC
        assert options.llm_model == "claude-3-opus"
        assert options.temperature == 0.2
        assert options.max_tokens == 3000
        assert options.generate_summary is False


class TestClinicalRAG:
    """Test ClinicalRAG class"""
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_initialization_openai(self, mock_retriever_class):
        """Test RAG initialization with OpenAI"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI,
                    llm_model="gpt-4"
                )
                
                assert rag.case_retriever == mock_retriever
                assert rag.llm_provider == LLMProvider.OPENAI
                assert rag.llm_model == "gpt-4"
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_initialization_anthropic(self, mock_retriever_class):
        """Test RAG initialization with Anthropic (skipped if Anthropic not available)"""
        # Skip if Anthropic is not available
        from src.rag.clinical_rag import ANTHROPIC_AVAILABLE
        if not ANTHROPIC_AVAILABLE:
            pytest.skip("Anthropic library not available")
        
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.Anthropic') as mock_anthropic:
                mock_client = Mock()
                mock_anthropic.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.ANTHROPIC,
                    llm_model="claude-3-opus"
                )
                
                assert rag.llm_provider == LLMProvider.ANTHROPIC
                assert rag.llm_model == "claude-3-opus"
                mock_anthropic.assert_called_once_with(api_key='test-key')
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_format_context(self, mock_retriever_class):
        """Test context formatting"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                # Create test case
                query_case = Case(
                    case_id="case-1",
                    patient_id="patient-1",
                    metadata=CaseMetadata(
                        age_group="adult",
                        region="rural_clinic_001",
                        comorbidities=["diabetes"]
                    ),
                    modalities={
                        "text": CaseModality(
                            modality_type="text",
                            content={"transcript": "Patient reports fever and cough"}
                        )
                    }
                )
                
                # Create retrieved results
                retrieved_results = [
                    RetrievalResult(
                        case_id="retrieved-1",
                        score=0.95,
                        metadata=CaseMetadata(
                            age_group="adult",
                            diagnosis="pneumonia",
                            outcome="recovered"
                        ),
                        modalities={"text": {"transcript": "Similar case with fever"}},
                        case_data={"medical_entities": [{"text": "fever", "entity_type": "symptom"}]}
                    )
                ]
                
                options = RAGOptions()
                context = rag._format_context(
                    query_text="fever cough",
                    query_case=query_case,
                    retrieved_results=retrieved_results,
                    options=options
                )
                
                assert "CURRENT CASE" in context
                assert "SIMILAR PAST CASES" in context
                assert "fever" in context
                assert "pneumonia" in context
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_build_prompt(self, mock_retriever_class):
        """Test prompt building"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                context = "Test context with similar cases"
                options = RAGOptions()
                
                prompt = rag._build_prompt(
                    query_text="fever cough",
                    query_case=None,
                    context=context,
                    options=options
                )
                
                assert "clinical decision support system" in prompt.lower()
                assert "CONTEXT" in prompt
                assert "CURRENT CASE QUERY" in prompt
                assert "fever cough" in prompt
                assert "differential diagnoses" in prompt.lower()
                assert "recommendations" in prompt.lower()
                assert "JSON" in prompt
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_call_llm_openai(self, mock_retriever_class):
        """Test LLM call with OpenAI"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '{"differential_diagnoses": [], "recommendations": []}'
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                options = RAGOptions()
                response = rag._call_llm("Test prompt", options)
                
                assert response is not None
                mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_parse_llm_response(self, mock_retriever_class):
        """Test LLM response parsing"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                # Test JSON response
                llm_response = json.dumps({
                    "differential_diagnoses": [
                        {"diagnosis": "pneumonia", "confidence": 0.85},
                        {"diagnosis": "bronchitis", "confidence": 0.65}
                    ],
                    "recommendations": [
                        {
                            "type": "test",
                            "title": "Chest X-ray",
                            "description": "Perform chest X-ray to confirm diagnosis",
                            "confidence": 0.9,
                            "priority": "high",
                            "citations": ["case-1", "case-2"]
                        }
                    ],
                    "summary": "Patient presents with fever and cough, likely respiratory infection",
                    "reasoning_chain": ["Step 1", "Step 2"],
                    "confidence_score": 0.8
                })
                
                retrieved_results = [
                    RetrievalResult(
                        case_id="case-1",
                        score=0.95,
                        metadata=CaseMetadata(diagnosis="pneumonia")
                    )
                ]
                
                options = RAGOptions()
                insight = rag._parse_llm_response(
                    llm_response=llm_response,
                    query_text="fever cough",
                    query_case=None,
                    retrieved_results=retrieved_results,
                    options=options
                )
                
                assert insight is not None
                assert len(insight.differential_diagnoses) == 2
                assert insight.differential_diagnoses[0]["diagnosis"] == "pneumonia"
                assert len(insight.recommendations) == 1
                assert insight.recommendations[0].type == "test"
                assert insight.recommendations[0].title == "Chest X-ray"
                assert insight.summary is not None
                assert insight.confidence_score == 0.8
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_parse_llm_response_with_markdown(self, mock_retriever_class):
        """Test parsing LLM response with markdown code blocks"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                # Test response with markdown code blocks
                llm_response = "```json\n" + json.dumps({
                    "differential_diagnoses": [],
                    "recommendations": [],
                    "summary": "Test summary"
                }) + "\n```"
                
                options = RAGOptions()
                insight = rag._parse_llm_response(
                    llm_response=llm_response,
                    query_text="test",
                    query_case=None,
                    retrieved_results=[],
                    options=options
                )
                
                assert insight is not None
                assert insight.summary == "Test summary"
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_generate_insights_full_pipeline(self, mock_retriever_class):
        """Test full insight generation pipeline"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        # Mock retrieval results
        retrieved_results = [
            RetrievalResult(
                case_id="case-1",
                score=0.95,
                metadata=CaseMetadata(
                    age_group="adult",
                    diagnosis="pneumonia",
                    outcome="recovered"
                ),
                modalities={"text": {"transcript": "Similar case"}},
                case_data={}
            )
        ]
        mock_retriever.retrieve_similar_cases.return_value = retrieved_results
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = json.dumps({
                    "differential_diagnoses": [
                        {"diagnosis": "pneumonia", "confidence": 0.85}
                    ],
                    "recommendations": [
                        {
                            "type": "test",
                            "title": "Chest X-ray",
                            "description": "Perform chest X-ray",
                            "confidence": 0.9,
                            "priority": "high",
                            "citations": ["case-1"]
                        }
                    ],
                    "summary": "Test summary",
                    "reasoning_chain": ["Step 1"],
                    "confidence_score": 0.8
                })
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                insight = rag.generate_insights(
                    query_text="Patient reports fever and cough"
                )
                
                assert insight is not None
                assert len(insight.differential_diagnoses) == 1
                assert len(insight.recommendations) == 1
                assert insight.summary is not None
                mock_retriever.retrieve_similar_cases.assert_called_once()
                mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_generate_recommendations_only(self, mock_retriever_class):
        """Test recommendation-only generation"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        mock_retriever.retrieve_similar_cases.return_value = []
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = json.dumps({
                    "differential_diagnoses": [],
                    "recommendations": [
                        {
                            "type": "treatment",
                            "title": "Antibiotics",
                            "description": "Prescribe antibiotics",
                            "confidence": 0.85,
                            "priority": "high",
                            "citations": []
                        }
                    ],
                    "summary": "",
                    "reasoning_chain": [],
                    "confidence_score": 0.7
                })
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                recommendations = rag.generate_recommendations(
                    query_text="fever cough"
                )
                
                assert len(recommendations) == 1
                assert recommendations[0].type == "treatment"
                assert recommendations[0].title == "Antibiotics"
    
    @patch('src.rag.clinical_rag.CaseRetriever')
    def test_generate_differential_diagnoses_only(self, mock_retriever_class):
        """Test differential diagnoses-only generation"""
        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever
        
        mock_retriever.retrieve_similar_cases.return_value = []
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.rag.clinical_rag.openai') as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = json.dumps({
                    "differential_diagnoses": [
                        {"diagnosis": "pneumonia", "confidence": 0.85},
                        {"diagnosis": "bronchitis", "confidence": 0.65}
                    ],
                    "recommendations": [],
                    "summary": "",
                    "reasoning_chain": [],
                    "confidence_score": 0.7
                })
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.OpenAI.return_value = mock_client
                
                rag = ClinicalRAG(
                    case_retriever=mock_retriever,
                    llm_provider=LLMProvider.OPENAI
                )
                
                diagnoses = rag.generate_differential_diagnoses(
                    query_text="fever cough"
                )
                
                assert len(diagnoses) == 2
                assert diagnoses[0]["diagnosis"] == "pneumonia"
                assert diagnoses[0]["confidence"] == 0.85


class TestClinicalInsight:
    """Test ClinicalInsight dataclass"""
    
    def test_to_dict(self):
        """Test converting insight to dictionary"""
        recommendation = Recommendation(
            type="test",
            title="Chest X-ray",
            description="Perform chest X-ray",
            confidence=0.9,
            priority="high",
            citations=["case-1"]
        )
        
        insight = ClinicalInsight(
            query_text="fever cough",
            differential_diagnoses=[
                {"diagnosis": "pneumonia", "confidence": 0.85}
            ],
            recommendations=[recommendation],
            summary="Test summary",
            confidence_score=0.8,
            reasoning_chain=["Step 1", "Step 2"],
            citations=["case-1"]
        )
        
        insight_dict = insight.to_dict()
        
        assert insight_dict["query_text"] == "fever cough"
        assert len(insight_dict["differential_diagnoses"]) == 1
        assert len(insight_dict["recommendations"]) == 1
        assert insight_dict["summary"] == "Test summary"
        assert insight_dict["confidence_score"] == 0.8
        assert "generated_at" in insight_dict


class TestRecommendation:
    """Test Recommendation dataclass"""
    
    def test_to_dict(self):
        """Test converting recommendation to dictionary"""
        recommendation = Recommendation(
            type="treatment",
            title="Antibiotics",
            description="Prescribe antibiotics",
            confidence=0.85,
            evidence=["Evidence 1", "Evidence 2"],
            citations=["case-1", "case-2"],
            priority="high"
        )
        
        rec_dict = recommendation.to_dict()
        
        assert rec_dict["type"] == "treatment"
        assert rec_dict["title"] == "Antibiotics"
        assert rec_dict["description"] == "Prescribe antibiotics"
        assert rec_dict["confidence"] == 0.85
        assert len(rec_dict["evidence"]) == 2
        assert len(rec_dict["citations"]) == 2
        assert rec_dict["priority"] == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

