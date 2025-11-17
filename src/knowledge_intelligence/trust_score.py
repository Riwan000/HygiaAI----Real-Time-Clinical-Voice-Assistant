"""
Clinical Trust Score System

Calculates confidence scores based on:
- Embedding similarity
- Source reliability
- Recency
- Cross-case agreement
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from ..retrieval.case_retrieval import RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class TrustScore:
    """Clinical trust score for a case or recommendation"""
    overall_score: float  # 0.0 to 1.0
    similarity_score: float  # Based on embedding similarity
    source_reliability: float  # Based on source quality
    recency_score: float  # Based on how recent the case is
    agreement_score: float  # Based on cross-case agreement
    confidence_level: str  # "high", "medium", "low"
    factors: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""


@dataclass
class TrustScoreBreakdown:
    """Detailed breakdown of trust score calculation"""
    case_id: str
    trust_score: TrustScore
    similar_cases_analyzed: int
    agreement_details: Dict[str, Any] = field(default_factory=dict)
    source_metadata: Dict[str, Any] = field(default_factory=dict)


class ClinicalTrustScoreSystem:
    """
    Clinical Trust Score System
    
    Calculates confidence scores for clinical cases and recommendations based on:
    - Embedding similarity
    - Source reliability
    - Recency
    - Cross-case agreement
    """
    
    def __init__(self):
        """Initialize trust score system"""
        # Source reliability weights (can be configured)
        self.source_reliability_weights = {
            "verified_clinic": 1.0,
            "hospital": 0.95,
            "clinic": 0.85,
            "mobile_unit": 0.75,
            "unknown": 0.5
        }
        
        # Recency decay factor (cases older than this get lower scores)
        self.recency_decay_days = 365  # 1 year
        
        # Agreement thresholds
        self.high_agreement_threshold = 0.8  # 80% of cases agree
        self.medium_agreement_threshold = 0.6  # 60% of cases agree
        
        logger.info("Clinical trust score system initialized")
    
    def calculate_trust_score(
        self,
        case: RetrievalResult,
        similar_cases: List[RetrievalResult],
        query_similarity_score: Optional[float] = None
    ) -> TrustScore:
        """
        Calculate trust score for a case based on similar cases
        
        Args:
            case: The case to score
            similar_cases: List of similar cases for agreement analysis
            query_similarity_score: Optional pre-calculated similarity score
            
        Returns:
            TrustScore with overall score and breakdown
        """
        try:
            # 1. Similarity score (from embedding similarity)
            similarity_score = query_similarity_score or case.score
            # Normalize to 0-1 range (assuming scores are already in this range)
            similarity_score = max(0.0, min(1.0, similarity_score))
            
            # 2. Source reliability score
            source_reliability = self._calculate_source_reliability(case)
            
            # 3. Recency score
            recency_score = self._calculate_recency_score(case)
            
            # 4. Agreement score (cross-case agreement)
            agreement_score = self._calculate_agreement_score(case, similar_cases)
            
            # 5. Weighted overall score
            weights = {
                "similarity": 0.4,
                "source": 0.2,
                "recency": 0.2,
                "agreement": 0.2
            }
            
            overall_score = (
                similarity_score * weights["similarity"] +
                source_reliability * weights["source"] +
                recency_score * weights["recency"] +
                agreement_score * weights["agreement"]
            )
            
            # Determine confidence level
            if overall_score >= 0.8:
                confidence_level = "high"
            elif overall_score >= 0.6:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            # Generate explanation
            explanation = self._generate_explanation(
                overall_score,
                similarity_score,
                source_reliability,
                recency_score,
                agreement_score,
                len(similar_cases)
            )
            
            return TrustScore(
                overall_score=overall_score,
                similarity_score=similarity_score,
                source_reliability=source_reliability,
                recency_score=recency_score,
                agreement_score=agreement_score,
                confidence_level=confidence_level,
                factors={
                    "weights": weights,
                    "similar_cases_count": len(similar_cases)
                },
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"Error calculating trust score: {e}")
            return TrustScore(
                overall_score=0.0,
                similarity_score=0.0,
                source_reliability=0.0,
                recency_score=0.0,
                agreement_score=0.0,
                confidence_level="low",
                explanation=f"Error calculating trust score: {e}"
            )
    
    def calculate_batch_trust_scores(
        self,
        cases: List[RetrievalResult],
        all_similar_cases: Optional[List[List[RetrievalResult]]] = None
    ) -> List[TrustScoreBreakdown]:
        """
        Calculate trust scores for multiple cases
        
        Args:
            cases: List of cases to score
            all_similar_cases: Optional list of similar cases for each case
            
        Returns:
            List of TrustScoreBreakdown objects
        """
        breakdowns = []
        
        for i, case in enumerate(cases):
            similar_cases = all_similar_cases[i] if all_similar_cases and i < len(all_similar_cases) else []
            
            trust_score = self.calculate_trust_score(
                case,
                similar_cases,
                query_similarity_score=case.score
            )
            
            # Extract source metadata
            case_data = case.case_data if hasattr(case, 'case_data') else {}
            payload = case_data.get("payload", {})
            metadata = payload.get("case_metadata", {})
            
            source_metadata = {
                "region": metadata.get("region"),
                "timestamp": payload.get("timestamp"),
                "source_type": self._infer_source_type(metadata)
            }
            
            # Calculate agreement details
            agreement_details = self._calculate_agreement_details(case, similar_cases)
            
            breakdown = TrustScoreBreakdown(
                case_id=case.case_id,
                trust_score=trust_score,
                similar_cases_analyzed=len(similar_cases),
                agreement_details=agreement_details,
                source_metadata=source_metadata
            )
            
            breakdowns.append(breakdown)
        
        return breakdowns
    
    def _calculate_source_reliability(
        self,
        case: RetrievalResult
    ) -> float:
        """Calculate source reliability score"""
        case_data = case.case_data if hasattr(case, 'case_data') else {}
        payload = case_data.get("payload", {})
        metadata = payload.get("case_metadata", {})
        
        # Infer source type from metadata
        source_type = self._infer_source_type(metadata)
        
        # Get reliability weight
        reliability = self.source_reliability_weights.get(
            source_type,
            self.source_reliability_weights["unknown"]
        )
        
        return reliability
    
    def _infer_source_type(
        self,
        metadata: Dict[str, Any]
    ) -> str:
        """Infer source type from metadata"""
        region = metadata.get("region", "").lower()
        
        if "hospital" in region or "hosp" in region:
            return "hospital"
        elif "clinic" in region:
            if "verified" in region or "certified" in region:
                return "verified_clinic"
            return "clinic"
        elif "mobile" in region or "unit" in region:
            return "mobile_unit"
        else:
            return "unknown"
    
    def _calculate_recency_score(
        self,
        case: RetrievalResult
    ) -> float:
        """Calculate recency score (newer cases get higher scores)"""
        case_data = case.case_data if hasattr(case, 'case_data') else {}
        payload = case_data.get("payload", {})
        timestamp_str = payload.get("timestamp")
        
        if not timestamp_str:
            return 0.5  # Default score if no timestamp
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_days = (now - timestamp).days
            
            # Exponential decay: newer cases get higher scores
            if age_days <= 0:
                return 1.0
            elif age_days >= self.recency_decay_days:
                return 0.1  # Very old cases
            else:
                # Exponential decay: score = e^(-age/decay_days)
                import math
                decay_factor = math.exp(-age_days / self.recency_decay_days)
                return max(0.1, decay_factor)
                
        except Exception as e:
            logger.warning(f"Error parsing timestamp: {e}")
            return 0.5
    
    def _calculate_agreement_score(
        self,
        case: RetrievalResult,
        similar_cases: List[RetrievalResult]
    ) -> float:
        """Calculate cross-case agreement score"""
        if not similar_cases:
            return 0.5  # Neutral score if no similar cases
        
        # Extract diagnosis from case
        case_data = case.case_data if hasattr(case, 'case_data') else {}
        payload = case_data.get("payload", {})
        metadata = payload.get("case_metadata", {})
        case_diagnosis = metadata.get("diagnosis", "").lower()
        
        if not case_diagnosis:
            return 0.5  # No diagnosis to compare
        
        # Count how many similar cases have the same diagnosis
        matching_diagnoses = 0
        total_with_diagnosis = 0
        
        for similar_case in similar_cases:
            similar_data = similar_case.case_data if hasattr(similar_case, 'case_data') else {}
            similar_payload = similar_data.get("payload", {})
            similar_metadata = similar_payload.get("case_metadata", {})
            similar_diagnosis = similar_metadata.get("diagnosis", "").lower()
            
            if similar_diagnosis:
                total_with_diagnosis += 1
                if similar_diagnosis == case_diagnosis:
                    matching_diagnoses += 1
        
        if total_with_diagnosis == 0:
            return 0.5  # No diagnoses to compare
        
        # Agreement ratio
        agreement_ratio = matching_diagnoses / total_with_diagnosis
        
        return agreement_ratio
    
    def _calculate_agreement_details(
        self,
        case: RetrievalResult,
        similar_cases: List[RetrievalResult]
    ) -> Dict[str, Any]:
        """Calculate detailed agreement metrics"""
        case_data = case.case_data if hasattr(case, 'case_data') else {}
        payload = case_data.get("payload", {})
        metadata = payload.get("case_metadata", {})
        case_diagnosis = metadata.get("diagnosis", "").lower()
        
        diagnosis_counts = defaultdict(int)
        symptom_overlaps = defaultdict(int)
        
        for similar_case in similar_cases:
            similar_data = similar_case.case_data if hasattr(similar_case, 'case_data') else {}
            similar_payload = similar_data.get("payload", {})
            similar_metadata = similar_payload.get("case_metadata", {})
            
            # Count diagnoses
            similar_diagnosis = similar_metadata.get("diagnosis", "").lower()
            if similar_diagnosis:
                diagnosis_counts[similar_diagnosis] += 1
            
            # Count symptom overlaps (simplified)
            similar_soap = similar_payload.get("soap_note", {})
            if similar_soap:
                similar_subjective = similar_soap.get("subjective", "").lower()
                case_soap = payload.get("soap_note", {})
                if case_soap:
                    case_subjective = case_soap.get("subjective", "").lower()
                    # Simple overlap detection
                    case_words = set(case_subjective.split())
                    similar_words = set(similar_subjective.split())
                    overlap = len(case_words & similar_words)
                    symptom_overlaps[similar_case.case_id] = overlap
        
        return {
            "total_similar_cases": len(similar_cases),
            "diagnosis_distribution": dict(diagnosis_counts),
            "most_common_diagnosis": max(diagnosis_counts.items(), key=lambda x: x[1])[0] if diagnosis_counts else None,
            "symptom_overlaps": dict(symptom_overlaps),
            "average_symptom_overlap": sum(symptom_overlaps.values()) / len(symptom_overlaps) if symptom_overlaps else 0
        }
    
    def _generate_explanation(
        self,
        overall_score: float,
        similarity_score: float,
        source_reliability: float,
        recency_score: float,
        agreement_score: float,
        similar_cases_count: int
    ) -> str:
        """Generate human-readable explanation of trust score"""
        parts = []
        
        if overall_score >= 0.8:
            parts.append("High confidence")
        elif overall_score >= 0.6:
            parts.append("Medium confidence")
        else:
            parts.append("Low confidence")
        
        parts.append(f"based on {similar_cases_count} similar cases")
        
        if similarity_score >= 0.8:
            parts.append("with high similarity")
        elif similarity_score < 0.5:
            parts.append("with low similarity")
        
        if agreement_score >= self.high_agreement_threshold:
            parts.append("and strong cross-case agreement")
        elif agreement_score < self.medium_agreement_threshold:
            parts.append("but limited cross-case agreement")
        
        if recency_score >= 0.8:
            parts.append("from recent cases")
        elif recency_score < 0.5:
            parts.append("from older cases")
        
        return ". ".join(parts) + "."

