"""
Unit tests for entity evaluation module
"""

import pytest
from src.entity_extraction.evaluation import (
    EntityEvaluator,
    EvaluationMetrics,
    EntityMatch
)
from src.entity_extraction.medical_ner import MedicalEntity, EntityType


class TestEntityEvaluator:
    """Test EntityEvaluator class"""
    
    def test_initialization(self):
        """Test evaluator initialization"""
        evaluator = EntityEvaluator(overlap_threshold=0.5)
        assert evaluator.overlap_threshold == 0.5
    
    def test_calculate_overlap_exact_match(self):
        """Test overlap calculation for exact match"""
        evaluator = EntityEvaluator()
        overlap = evaluator.calculate_overlap(10, 20, 10, 20)
        assert overlap == 1.0
    
    def test_calculate_overlap_partial_match(self):
        """Test overlap calculation for partial match"""
        evaluator = EntityEvaluator()
        overlap = evaluator.calculate_overlap(10, 20, 15, 25)
        assert overlap > 0.0
        assert overlap < 1.0
    
    def test_calculate_overlap_no_match(self):
        """Test overlap calculation for no match"""
        evaluator = EntityEvaluator()
        overlap = evaluator.calculate_overlap(10, 20, 30, 40)
        assert overlap == 0.0
    
    def test_match_entities_exact(self):
        """Test entity matching with exact matches"""
        evaluator = EntityEvaluator()
        
        predicted = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            )
        ]
        
        ground_truth = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            )
        ]
        
        matches = evaluator.match_entities(predicted, ground_truth)
        assert len(matches) == 1
        assert matches[0].match_type == 'exact'
        assert matches[0].overlap_ratio >= 0.95
    
    def test_match_entities_false_positive(self):
        """Test entity matching with false positive"""
        evaluator = EntityEvaluator()
        
        predicted = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            )
        ]
        
        ground_truth = []
        
        matches = evaluator.match_entities(predicted, ground_truth)
        assert len(matches) == 1
        assert matches[0].match_type == 'none'
    
    def test_match_entities_false_negative(self):
        """Test entity matching with false negative"""
        evaluator = EntityEvaluator()
        
        predicted = []
        
        ground_truth = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            )
        ]
        
        matches = evaluator.match_entities(predicted, ground_truth)
        assert len(matches) == 1
        assert matches[0].match_type == 'none'
    
    def test_evaluate_perfect_match(self):
        """Test evaluation with perfect matches"""
        evaluator = EntityEvaluator()
        
        predicted = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            ),
            MedicalEntity(
                text="cough",
                entity_type=EntityType.SYMPTOM,
                start_pos=10,
                end_pos=15
            )
        ]
        
        ground_truth = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            ),
            MedicalEntity(
                text="cough",
                entity_type=EntityType.SYMPTOM,
                start_pos=10,
                end_pos=15
            )
        ]
        
        metrics = evaluator.evaluate(predicted, ground_truth)
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
        assert metrics.true_positives == 2
        assert metrics.false_positives == 0
        assert metrics.false_negatives == 0
    
    def test_evaluate_with_errors(self):
        """Test evaluation with errors"""
        evaluator = EntityEvaluator()
        
        predicted = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            ),
            MedicalEntity(
                text="wrong",
                entity_type=EntityType.SYMPTOM,
                start_pos=10,
                end_pos=15
            )
        ]
        
        ground_truth = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            ),
            MedicalEntity(
                text="cough",
                entity_type=EntityType.SYMPTOM,
                start_pos=20,
                end_pos=25
            )
        ]
        
        metrics = evaluator.evaluate(predicted, ground_truth)
        assert metrics.precision < 1.0  # Has false positive
        assert metrics.recall < 1.0  # Has false negative
        assert metrics.true_positives == 1
        assert metrics.false_positives == 1
        assert metrics.false_negatives == 1
    
    def test_generate_report(self):
        """Test report generation"""
        evaluator = EntityEvaluator()
        
        predicted = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            )
        ]
        
        ground_truth = [
            MedicalEntity(
                text="fever",
                entity_type=EntityType.SYMPTOM,
                start_pos=0,
                end_pos=5
            )
        ]
        
        metrics = evaluator.evaluate(predicted, ground_truth)
        report = evaluator.generate_report(metrics, detailed=True)
        
        assert "Entity Extraction Evaluation Report" in report
        assert "Precision" in report
        assert "Recall" in report
        assert "F1-Score" in report
        assert "Per-Type Metrics" in report

