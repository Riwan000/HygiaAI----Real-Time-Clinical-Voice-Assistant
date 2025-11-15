"""
Evaluation Metrics for Medical Entity Extraction

Provides precision, recall, F1-score, and other metrics
for evaluating entity extraction accuracy.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

from .medical_ner import MedicalEntity, EntityType

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """Represents a match between predicted and ground truth entities"""
    predicted: MedicalEntity
    ground_truth: MedicalEntity
    match_type: str  # 'exact', 'partial', 'type_match', 'none'
    overlap_ratio: float = 0.0


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for entity extraction"""
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    total_predicted: int
    total_ground_truth: int
    true_positives: int
    false_positives: int
    false_negatives: int
    by_type: Dict[str, Dict[str, float]]  # Metrics per entity type


class EntityEvaluator:
    """
    Evaluates medical entity extraction accuracy
    
    Provides metrics such as:
    - Precision: TP / (TP + FP)
    - Recall: TP / (TP + FN)
    - F1-Score: 2 * (Precision * Recall) / (Precision + Recall)
    """
    
    def __init__(self, overlap_threshold: float = 0.5):
        """
        Initialize evaluator
        
        Args:
            overlap_threshold: Minimum overlap ratio for considering entities as matched
        """
        self.overlap_threshold = overlap_threshold
        logger.info("Entity evaluator initialized")
    
    def calculate_overlap(
        self,
        pred_start: int,
        pred_end: int,
        gt_start: int,
        gt_end: int
    ) -> float:
        """
        Calculate overlap ratio between two entity spans
        
        Args:
            pred_start: Start position of predicted entity
            pred_end: End position of predicted entity
            gt_start: Start position of ground truth entity
            gt_end: End position of ground truth entity
            
        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        # Calculate intersection
        intersection_start = max(pred_start, gt_start)
        intersection_end = min(pred_end, gt_end)
        
        if intersection_start >= intersection_end:
            return 0.0
        
        intersection_length = intersection_end - intersection_start
        
        # Calculate union
        union_start = min(pred_start, gt_start)
        union_end = max(pred_end, gt_end)
        union_length = union_end - union_start
        
        if union_length == 0:
            return 0.0
        
        return intersection_length / union_length
    
    def match_entities(
        self,
        predicted: List[MedicalEntity],
        ground_truth: List[MedicalEntity]
    ) -> List[EntityMatch]:
        """
        Match predicted entities with ground truth entities
        
        Args:
            predicted: List of predicted entities
            ground_truth: List of ground truth entities
            
        Returns:
            List of EntityMatch objects
        """
        matches = []
        matched_gt_indices = set()
        
        for pred_entity in predicted:
            best_match = None
            best_overlap = 0.0
            best_gt_idx = -1
            
            for idx, gt_entity in enumerate(ground_truth):
                if idx in matched_gt_indices:
                    continue
                
                # Check if types match
                if pred_entity.entity_type != gt_entity.entity_type:
                    continue
                
                # Calculate overlap
                overlap = self.calculate_overlap(
                    pred_entity.start_pos,
                    pred_entity.end_pos,
                    gt_entity.start_pos,
                    gt_entity.end_pos
                )
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = gt_entity
                    best_gt_idx = idx
            
            # Determine match type
            if best_match and best_overlap >= self.overlap_threshold:
                if best_overlap >= 0.95:  # Nearly exact match
                    match_type = 'exact'
                elif best_overlap >= 0.7:  # Good partial match
                    match_type = 'partial'
                else:
                    match_type = 'type_match'
                
                matches.append(EntityMatch(
                    predicted=pred_entity,
                    ground_truth=best_match,
                    match_type=match_type,
                    overlap_ratio=best_overlap
                ))
                matched_gt_indices.add(best_gt_idx)
            else:
                # False positive
                matches.append(EntityMatch(
                    predicted=pred_entity,
                    ground_truth=MedicalEntity(
                        text="",
                        entity_type=EntityType.UNKNOWN,
                        start_pos=0,
                        end_pos=0
                    ),
                    match_type='none',
                    overlap_ratio=0.0
                ))
        
        # False negatives (unmatched ground truth entities)
        for idx, gt_entity in enumerate(ground_truth):
            if idx not in matched_gt_indices:
                matches.append(EntityMatch(
                    predicted=MedicalEntity(
                        text="",
                        entity_type=EntityType.UNKNOWN,
                        start_pos=0,
                        end_pos=0
                    ),
                    ground_truth=gt_entity,
                    match_type='none',
                    overlap_ratio=0.0
                ))
        
        return matches
    
    def evaluate(
        self,
        predicted: List[MedicalEntity],
        ground_truth: List[MedicalEntity]
    ) -> EvaluationMetrics:
        """
        Evaluate entity extraction accuracy
        
        Args:
            predicted: List of predicted entities
            ground_truth: List of ground truth entities
            
        Returns:
            EvaluationMetrics object
        """
        matches = self.match_entities(predicted, ground_truth)
        
        # Count matches
        true_positives = sum(1 for m in matches if m.match_type != 'none' and m.predicted.text)
        false_positives = sum(1 for m in matches if m.match_type == 'none' and m.predicted.text)
        false_negatives = sum(1 for m in matches if m.match_type == 'none' and m.ground_truth.text)
        
        # Calculate overall metrics
        total_predicted = len(predicted)
        total_ground_truth = len(ground_truth)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Calculate accuracy (exact matches only)
        exact_matches = sum(1 for m in matches if m.match_type == 'exact')
        accuracy = exact_matches / total_ground_truth if total_ground_truth > 0 else 0.0
        
        # Calculate metrics by entity type
        by_type = defaultdict(lambda: {
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'true_positives': 0,
            'false_positives': 0,
            'false_negatives': 0
        })
        
        for entity_type in EntityType:
            type_matches = [m for m in matches if m.predicted.entity_type == entity_type or m.ground_truth.entity_type == entity_type]
            
            tp = sum(1 for m in type_matches if m.match_type != 'none' and m.predicted.entity_type == entity_type)
            fp = sum(1 for m in type_matches if m.match_type == 'none' and m.predicted.entity_type == entity_type)
            fn = sum(1 for m in type_matches if m.match_type == 'none' and m.ground_truth.entity_type == entity_type)
            
            type_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            type_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            type_f1 = 2 * (type_precision * type_recall) / (type_precision + type_recall) if (type_precision + type_recall) > 0 else 0.0
            
            by_type[entity_type.value] = {
                'precision': type_precision,
                'recall': type_recall,
                'f1_score': type_f1,
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn
            }
        
        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            accuracy=accuracy,
            total_predicted=total_predicted,
            total_ground_truth=total_ground_truth,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            by_type=dict(by_type)
        )
    
    def generate_report(
        self,
        metrics: EvaluationMetrics,
        detailed: bool = False
    ) -> str:
        """
        Generate evaluation report
        
        Args:
            metrics: EvaluationMetrics object
            detailed: Whether to include detailed per-type metrics
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("Entity Extraction Evaluation Report")
        report.append("=" * 60)
        report.append("")
        report.append("Overall Metrics:")
        report.append(f"  Precision: {metrics.precision:.4f}")
        report.append(f"  Recall: {metrics.recall:.4f}")
        report.append(f"  F1-Score: {metrics.f1_score:.4f}")
        report.append(f"  Accuracy: {metrics.accuracy:.4f}")
        report.append("")
        report.append("Counts:")
        report.append(f"  Total Predicted: {metrics.total_predicted}")
        report.append(f"  Total Ground Truth: {metrics.total_ground_truth}")
        report.append(f"  True Positives: {metrics.true_positives}")
        report.append(f"  False Positives: {metrics.false_positives}")
        report.append(f"  False Negatives: {metrics.false_negatives}")
        
        if detailed:
            report.append("")
            report.append("Per-Type Metrics:")
            for entity_type, type_metrics in metrics.by_type.items():
                if type_metrics['true_positives'] + type_metrics['false_positives'] + type_metrics['false_negatives'] > 0:
                    report.append(f"  {entity_type}:")
                    report.append(f"    Precision: {type_metrics['precision']:.4f}")
                    report.append(f"    Recall: {type_metrics['recall']:.4f}")
                    report.append(f"    F1-Score: {type_metrics['f1_score']:.4f}")
                    report.append(f"    TP: {type_metrics['true_positives']}, FP: {type_metrics['false_positives']}, FN: {type_metrics['false_negatives']}")
        
        report.append("=" * 60)
        return "\n".join(report)

