"""
Unit tests for Case Retrieval Module

Tests:
- Semantic search
- Keyword-based search
- Hybrid search
- Retrieval options and filters
- Result formatting
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone

from src.retrieval.case_retrieval import (
    CaseRetriever,
    RetrievalOptions,
    RetrievalResult,
    RetrievalMode,
)
from src.storage import QdrantStorage
from src.embeddings import BioBERTEmbeddingGenerator, CLIPEmbeddingGenerator


class TestRetrievalOptions:
    """Test RetrievalOptions dataclass"""
    
    def test_default_options(self):
        """Test default retrieval options"""
        options = RetrievalOptions()
        
        assert options.limit == 5
        assert options.score_threshold is None
        assert options.mode == RetrievalMode.HYBRID
        assert options.semantic_weight == 0.7
        assert options.keyword_weight == 0.3
    
    def test_custom_options(self):
        """Test custom retrieval options"""
        options = RetrievalOptions(
            limit=10,
            score_threshold=0.8,
            mode=RetrievalMode.SEMANTIC,
            semantic_weight=0.9,
            keyword_weight=0.1
        )
        
        assert options.limit == 10
        assert options.score_threshold == 0.8
        assert options.mode == RetrievalMode.SEMANTIC
        assert options.semantic_weight == 0.9
        assert options.keyword_weight == 0.1
    
    def test_to_filters(self):
        """Test converting options to Qdrant filters"""
        options = RetrievalOptions(
            age_group="adult",
            age_range={"gte": 30, "lte": 50},
            region="rural_clinic_001",
            comorbidities=["diabetes", "hypertension"],
            diagnosis="pneumonia",
            time_range={
                "gte": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "lte": datetime(2024, 12, 31, tzinfo=timezone.utc)
            },
            entity_types=["symptom", "diagnosis"],
            domain="pathology",
            source="NCBI Bookshelf"
        )
        
        filters = options.to_filters()
        
        assert filters["age_group"] == "adult"
        assert filters["age"] == {"gte": 30, "lte": 50}
        assert filters["region"] == "rural_clinic_001"
        assert "in" in filters["comorbidities"]
        assert filters["diagnosis"] == "pneumonia"
        assert "timestamp" in filters
        assert "in" in filters["medical_entities.entity_type"]
        assert filters["domain"] == "pathology"
        assert filters["source"] == "NCBI Bookshelf"


class TestCaseRetriever:
    """Test CaseRetriever class"""
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    @patch('src.retrieval.case_retrieval.CLIPEmbeddingGenerator')
    def test_initialization(self, mock_clip, mock_biobert, mock_storage):
        """Test retriever initialization"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        retriever = CaseRetriever(mock_storage_instance)
        
        assert retriever.storage == mock_storage_instance
        assert retriever.text_embedding_generator is not None
        assert retriever.image_embedding_generator is not None
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_semantic_search(self, mock_biobert, mock_storage):
        """Test semantic search"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock search results
        mock_result = {
            "id": "case-1",
            "score": 0.95,
            "payload": {
                "transcript": "Patient has fever and cough",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "age_group": "adult",
                "region": "rural_clinic_001",
                "diagnosis": "pneumonia"
            }
        }
        mock_storage_instance.search_with_filters.return_value = [mock_result]
        
        # Mock embedding generator
        mock_text_gen = Mock()
        mock_text_gen.generate_embedding.return_value = [0.1] * 768
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(mock_storage_instance, text_embedding_generator=mock_text_gen)
        
        options = RetrievalOptions(mode=RetrievalMode.SEMANTIC, limit=5)
        results = retriever.retrieve_similar_cases(
            query_text="fever cough",
            options=options
        )
        
        assert len(results) == 1
        assert results[0].case_id == "case-1"
        assert results[0].score == 0.95
        mock_storage_instance.search_with_filters.assert_called_once()
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_keyword_search(self, mock_biobert, mock_storage):
        """Test keyword-based search"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock search results
        mock_result = {
            "id": "case-1",
            "score": 0.85,
            "payload": {
                "transcript": "Patient has fever",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "age_group": "adult",
                "diagnosis": "pneumonia"
            }
        }
        mock_storage_instance.search_with_filters.return_value = [mock_result]
        
        # Mock embedding generator
        mock_text_gen = Mock()
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(mock_storage_instance, text_embedding_generator=mock_text_gen)
        
        options = RetrievalOptions(
            mode=RetrievalMode.KEYWORD,
            age_group="adult",
            diagnosis="pneumonia"
        )
        results = retriever.retrieve_similar_cases(
            query_text="fever",
            options=options
        )
        
        assert len(results) == 1
        assert results[0].case_id == "case-1"
        mock_storage_instance.search_with_filters.assert_called_once()
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_hybrid_search(self, mock_biobert, mock_storage):
        """Test hybrid search"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock search results
        mock_result = {
            "id": "case-1",
            "score": 0.90,
            "semantic_score": 0.95,
            "keyword_score": 0.80,
            "combined_score": 0.905,
            "payload": {
                "transcript": "Patient has fever and cough",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "age_group": "adult"
            }
        }
        mock_storage_instance.hybrid_search.return_value = [mock_result]
        
        # Mock embedding generator
        mock_text_gen = Mock()
        mock_text_gen.generate_embedding.return_value = [0.1] * 768
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(mock_storage_instance, text_embedding_generator=mock_text_gen)
        
        options = RetrievalOptions(mode=RetrievalMode.HYBRID, limit=5)
        results = retriever.retrieve_similar_cases(
            query_text="fever cough",
            options=options
        )
        
        assert len(results) == 1
        assert results[0].case_id == "case-1"
        assert results[0].semantic_score == 0.95
        assert results[0].keyword_score == 0.80
        assert results[0].combined_score == 0.905
        mock_storage_instance.hybrid_search.assert_called_once()
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_retrieve_by_entity_type(self, mock_biobert, mock_storage):
        """Test retrieval by entity type"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock search results
        mock_result = {
            "id": "case-1",
            "score": 0.85,
            "payload": {
                "transcript": "Patient has fever",
                "medical_entities": [{"entity_type": "symptom", "text": "fever"}],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        mock_storage_instance.search_with_filters.return_value = [mock_result]
        
        # Mock embedding generator
        mock_text_gen = Mock()
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(mock_storage_instance, text_embedding_generator=mock_text_gen)
        
        results = retriever.retrieve_by_entity_type(
            entity_type="symptom",
            entity_value="fever"
        )
        
        assert len(results) == 1
        assert results[0].case_id == "case-1"
        mock_storage_instance.search_with_filters.assert_called_once()
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_retrieve_by_time_range(self, mock_biobert, mock_storage):
        """Test retrieval by time range"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock search results (hybrid_search is used by default)
        mock_result = {
            "id": "case-1",
            "score": 0.90,
            "semantic_score": 0.90,
            "keyword_score": 0.85,
            "combined_score": 0.885,
            "payload": {
                "transcript": "Patient has fever",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        mock_storage_instance.hybrid_search.return_value = [mock_result]
        
        # Mock embedding generator
        mock_text_gen = Mock()
        mock_text_gen.generate_embedding.return_value = [0.1] * 768
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(mock_storage_instance, text_embedding_generator=mock_text_gen)
        
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 12, 31, tzinfo=timezone.utc)
        
        results = retriever.retrieve_by_time_range(
            start_time=start_time,
            end_time=end_time,
            query_text="fever"
        )
        
        assert len(results) == 1
        assert results[0].case_id == "case-1"
        mock_storage_instance.hybrid_search.assert_called_once()
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_retrieve_by_demographics(self, mock_biobert, mock_storage):
        """Test retrieval by demographics"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock search results (hybrid_search is used by default)
        mock_result = {
            "id": "case-1",
            "score": 0.88,
            "semantic_score": 0.88,
            "keyword_score": 0.82,
            "combined_score": 0.862,
            "payload": {
                "transcript": "Patient has fever",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "age_group": "adult",
                "region": "rural_clinic_001",
                "comorbidities": ["diabetes"]
            }
        }
        mock_storage_instance.hybrid_search.return_value = [mock_result]
        
        # Mock embedding generator
        mock_text_gen = Mock()
        mock_text_gen.generate_embedding.return_value = [0.1] * 768
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(mock_storage_instance, text_embedding_generator=mock_text_gen)
        
        results = retriever.retrieve_by_demographics(
            age_group="adult",
            age_range={"gte": 30, "lte": 50},
            region="rural_clinic_001",
            comorbidities=["diabetes"],
            query_text="fever"
        )
        
        assert len(results) == 1
        assert results[0].case_id == "case-1"
        mock_storage_instance.hybrid_search.assert_called_once()
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_format_results(self, mock_biobert, mock_storage):
        """Test result formatting"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock embedding generator
        mock_text_gen = Mock()
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(mock_storage_instance, text_embedding_generator=mock_text_gen)
        
        # Test result formatting
        raw_results = [{
            "id": "case-1",
            "score": 0.95,
            "semantic_score": 0.95,
            "keyword_score": 0.80,
            "combined_score": 0.905,
            "payload": {
                "transcript": "Patient has fever and cough",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "age_group": "adult",
                "region": "rural_clinic_001",
                "comorbidities": ["diabetes"],
                "diagnosis": "pneumonia",
                "outcome": "recovered",
                "medical_entities": [
                    {"entity_type": "symptom", "text": "fever"},
                    {"entity_type": "symptom", "text": "cough"}
                ],
                "soap_notes": "Subjective: Patient reports fever..."
            }
        }]
        
        options = RetrievalOptions()
        formatted = retriever._format_results(raw_results, options)
        
        assert len(formatted) == 1
        assert formatted[0].case_id == "case-1"
        assert formatted[0].score == 0.95
        assert formatted[0].metadata is not None
        assert formatted[0].metadata.age_group == "adult"
        assert formatted[0].metadata.region == "rural_clinic_001"
        assert formatted[0].metadata.comorbidities == ["diabetes"]
        assert formatted[0].metadata.diagnosis == "pneumonia"
        assert formatted[0].metadata.outcome == "recovered"
        assert "text" in formatted[0].modalities
        assert formatted[0].modalities["text"]["transcript"] == "Patient has fever and cough"
    
    @patch('src.retrieval.case_retrieval.QdrantStorage')
    @patch('src.retrieval.case_retrieval.BioBERTEmbeddingGenerator')
    def test_multimodal_query(self, mock_biobert, mock_storage):
        """Test multi-modal query (text + image)"""
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.vector_size = 384
        
        # Mock multimodal embedding generator
        mock_multimodal = Mock()
        mock_multimodal.generate_multimodal_embedding.return_value = {
            "multimodal_embedding": [0.1] * 1280,  # Combined text + image
            "text_embedding": [0.1] * 768,
            "image_embedding": [0.2] * 512,
            "modalities": ["text", "image"]
        }
        
        # Mock search results
        mock_result = {
            "id": "case-1",
            "score": 0.92,
            "payload": {
                "transcript": "Patient has fever",
                "image_path": "xray.jpg",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        mock_storage_instance.search_with_filters.return_value = [mock_result]
        
        # Mock embedding generators
        mock_text_gen = Mock()
        mock_biobert.return_value = mock_text_gen
        
        retriever = CaseRetriever(
            mock_storage_instance,
            text_embedding_generator=mock_text_gen,
            multimodal_embedding_generator=mock_multimodal
        )
        
        options = RetrievalOptions(mode=RetrievalMode.SEMANTIC)
        results = retriever.retrieve_similar_cases(
            query_text="fever",
            query_image_path="xray.jpg",
            options=options
        )
        
        assert len(results) == 1
        assert results[0].case_id == "case-1"
        mock_multimodal.generate_multimodal_embedding.assert_called_once()
        mock_storage_instance.search_with_filters.assert_called_once()


class TestRetrievalResult:
    """Test RetrievalResult dataclass"""
    
    def test_to_dict(self):
        """Test converting result to dictionary"""
        from src.models import CaseMetadata
        
        metadata = CaseMetadata(
            timestamp=datetime.now(timezone.utc),
            age_group="adult",
            region="rural_clinic_001",
            comorbidities=["diabetes"],
            diagnosis="pneumonia",
            outcome="recovered"
        )
        
        result = RetrievalResult(
            case_id="case-1",
            score=0.95,
            semantic_score=0.95,
            keyword_score=0.80,
            combined_score=0.905,
            case_data={"transcript": "Patient has fever"},
            metadata=metadata,
            modalities={"text": {"transcript": "Patient has fever"}}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["case_id"] == "case-1"
        assert result_dict["score"] == 0.95
        assert result_dict["semantic_score"] == 0.95
        assert result_dict["keyword_score"] == 0.80
        assert result_dict["combined_score"] == 0.905
        assert result_dict["metadata"] is not None
        assert result_dict["modalities"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

