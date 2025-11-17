"""
Pattern Learning & Evolution Service

Learns evolving diagnostic patterns in local context (e.g., rural disease trends).
Performs periodic clustering analysis, trend detection, and regional pattern identification.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from collections import defaultdict

from ..storage.qdrant_storage import QdrantStorage
from ..retrieval.case_retrieval import CaseRetriever
from ..visualization.temporal_trends import TemporalTrendAnalyzer
from ..outbreak.outbreak_detector import OutbreakDetector

logger = logging.getLogger(__name__)

# Optional scikit-learn for advanced clustering
try:
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")


@dataclass
class PatternInsight:
    """Represents a learned pattern insight"""
    pattern_type: str  # "diagnostic", "temporal", "regional", "treatment"
    pattern_description: str
    confidence: float  # 0.0 to 1.0
    supporting_cases: int
    time_window: Optional[Tuple[datetime, datetime]] = None
    region: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternLearningResult:
    """Result of pattern learning analysis"""
    insights: List[PatternInsight]
    clusters: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]
    recommendation_weights: Dict[str, float]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PatternAnalyzer:
    """
    Analyzes patterns in clinical cases and learns evolving diagnostic patterns
    
    Features:
    - Periodic clustering analysis
    - Trend detection over time windows
    - Regional pattern identification
    - Update recommendation weights based on patterns
    """
    
    def __init__(
        self,
        qdrant_storage: Optional[QdrantStorage] = None,
        collection_name: str = "hygiaai_cases",
        case_retriever: Optional[CaseRetriever] = None
    ):
        """
        Initialize pattern analyzer
        
        Args:
            qdrant_storage: QdrantStorage instance
            collection_name: Collection name for cases
            case_retriever: CaseRetriever instance (creates new if not provided)
        """
        import os
        
        if qdrant_storage:
            self.storage = qdrant_storage
        else:
            self.storage = QdrantStorage(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6334")),
                collection_name=collection_name,
                vector_size=768
            )
        
        self.collection_name = collection_name
        self.case_retriever = case_retriever or CaseRetriever(
            qdrant_storage=self.storage
        )
        self.trend_analyzer = TemporalTrendAnalyzer(
            qdrant_storage=self.storage
        )
        self.outbreak_detector = OutbreakDetector(
            qdrant_storage=self.storage
        )
        
        # Recommendation weights (updated based on patterns)
        self.recommendation_weights: Dict[str, float] = {
            "diagnosis": 1.0,
            "treatment": 1.0,
            "symptom": 1.0,
            "regional": 1.0,
            "temporal": 1.0
        }
        
        logger.info("Pattern analyzer initialized")
    
    def analyze_patterns(
        self,
        time_window_days: int = 30,
        region: Optional[str] = None,
        min_cases_for_pattern: int = 5
    ) -> PatternLearningResult:
        """
        Perform comprehensive pattern analysis
        
        Args:
            time_window_days: Number of days to analyze
            region: Optional region filter
            min_cases_for_pattern: Minimum cases required to identify a pattern
            
        Returns:
            PatternLearningResult with insights, clusters, and trend analysis
        """
        try:
            insights = []
            clusters = []
            
            # Get cases in time window
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=time_window_days)
            
            # Retrieve cases
            all_cases = self._retrieve_cases_in_window(start_time, end_time, region)
            
            if len(all_cases) < min_cases_for_pattern:
                logger.warning(f"Insufficient cases for pattern analysis: {len(all_cases)} < {min_cases_for_pattern}")
                return PatternLearningResult(
                    insights=[],
                    clusters=[],
                    trend_analysis={},
                    recommendation_weights=self.recommendation_weights.copy()
                )
            
            # 1. Diagnostic pattern analysis
            diagnostic_insights = self._analyze_diagnostic_patterns(
                all_cases,
                min_cases_for_pattern
            )
            insights.extend(diagnostic_insights)
            
            # 2. Temporal pattern analysis
            temporal_insights = self._analyze_temporal_patterns(
                all_cases,
                time_window_days,
                min_cases_for_pattern
            )
            insights.extend(temporal_insights)
            
            # 3. Regional pattern analysis
            if region:
                regional_insights = self._analyze_regional_patterns(
                    all_cases,
                    region,
                    min_cases_for_pattern
                )
                insights.extend(regional_insights)
            
            # 4. Clustering analysis
            clusters = self._perform_clustering(all_cases)
            
            # 5. Trend analysis
            trend_analysis = self.trend_analyzer.analyze_trends(
                start_time=start_time,
                end_time=end_time,
                granularity="daily"
            )
            
            # 6. Update recommendation weights based on patterns
            self._update_recommendation_weights(insights, clusters)
            
            logger.info(f"Pattern analysis complete: {len(insights)} insights, {len(clusters)} clusters")
            
            return PatternLearningResult(
                insights=insights,
                clusters=clusters,
                trend_analysis=trend_analysis,
                recommendation_weights=self.recommendation_weights.copy()
            )
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return PatternLearningResult(
                insights=[],
                clusters=[],
                trend_analysis={},
                recommendation_weights=self.recommendation_weights.copy()
            )
    
    def _retrieve_cases_in_window(
        self,
        start_time: datetime,
        end_time: datetime,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all cases in the specified time window"""
        try:
            # Use case retriever with time range filter
            results = self.case_retriever.retrieve_by_time_range(
                start_time=start_time,
                end_time=end_time,
                limit=1000  # Large limit to get all cases
            )
            
            cases = []
            for result in results.cases:
                if region:
                    # Filter by region if specified
                    case_region = result.metadata.get("region")
                    if case_region == region:
                        cases.append(result.to_dict())
                else:
                    cases.append(result.to_dict())
            
            return cases
        except Exception as e:
            logger.error(f"Error retrieving cases: {e}")
            return []
    
    def _analyze_diagnostic_patterns(
        self,
        cases: List[Dict[str, Any]],
        min_cases: int
    ) -> List[PatternInsight]:
        """Analyze diagnostic patterns (common diagnoses, symptom-diagnosis pairs)"""
        insights = []
        
        # Count diagnoses
        diagnosis_counts = defaultdict(int)
        symptom_diagnosis = defaultdict(int)
        
        for case in cases:
            payload = case.get("payload", {})
            metadata = payload.get("case_metadata", {})
            diagnosis = metadata.get("diagnosis")
            
            if diagnosis:
                diagnosis_counts[diagnosis] += 1
                
                # Extract symptoms from SOAP or entities
                soap = payload.get("soap_note", {})
                symptoms = []
                if soap:
                    subjective = soap.get("subjective", "")
                    # Simple extraction (in production, use NER)
                    if "fever" in subjective.lower():
                        symptoms.append("fever")
                    if "cough" in subjective.lower():
                        symptoms.append("cough")
                
                for symptom in symptoms:
                    symptom_diagnosis[(symptom, diagnosis)] += 1
        
        # Generate insights for common diagnoses
        for diagnosis, count in diagnosis_counts.items():
            if count >= min_cases:
                confidence = min(1.0, count / len(cases))
                insights.append(PatternInsight(
                    pattern_type="diagnostic",
                    pattern_description=f"Common diagnosis: {diagnosis} ({count} cases)",
                    confidence=confidence,
                    supporting_cases=count,
                    metadata={"diagnosis": diagnosis, "frequency": count}
                ))
        
        # Generate insights for symptom-diagnosis patterns
        for (symptom, diagnosis), count in symptom_diagnosis.items():
            if count >= min_cases:
                confidence = min(1.0, count / len(cases))
                insights.append(PatternInsight(
                    pattern_type="diagnostic",
                    pattern_description=f"Pattern: {symptom} → {diagnosis} ({count} cases)",
                    confidence=confidence,
                    supporting_cases=count,
                    metadata={"symptom": symptom, "diagnosis": diagnosis, "frequency": count}
                ))
        
        return insights
    
    def _analyze_temporal_patterns(
        self,
        cases: List[Dict[str, Any]],
        time_window_days: int,
        min_cases: int
    ) -> List[PatternInsight]:
        """Analyze temporal patterns (seasonal trends, time-based clusters)"""
        insights = []
        
        # Group cases by day of week
        day_of_week_counts = defaultdict(int)
        hour_counts = defaultdict(int)
        
        for case in cases:
            payload = case.get("payload", {})
            timestamp_str = payload.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    day_of_week_counts[timestamp.weekday()] += 1
                    hour_counts[timestamp.hour] += 1
                except:
                    pass
        
        # Identify peak days/hours
        if day_of_week_counts:
            peak_day = max(day_of_week_counts.items(), key=lambda x: x[1])
            if peak_day[1] >= min_cases:
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                insights.append(PatternInsight(
                    pattern_type="temporal",
                    pattern_description=f"Peak consultation day: {day_names[peak_day[0]]} ({peak_day[1]} cases)",
                    confidence=min(1.0, peak_day[1] / len(cases)),
                    supporting_cases=peak_day[1],
                    metadata={"day_of_week": peak_day[0], "count": peak_day[1]}
                ))
        
        return insights
    
    def _analyze_regional_patterns(
        self,
        cases: List[Dict[str, Any]],
        region: str,
        min_cases: int
    ) -> List[PatternInsight]:
        """Analyze regional patterns"""
        insights = []
        
        # Count cases by region
        regional_diagnoses = defaultdict(int)
        
        for case in cases:
            payload = case.get("payload", {})
            metadata = payload.get("case_metadata", {})
            diagnosis = metadata.get("diagnosis")
            
            if diagnosis:
                regional_diagnoses[diagnosis] += 1
        
        # Generate regional insights
        for diagnosis, count in regional_diagnoses.items():
            if count >= min_cases:
                insights.append(PatternInsight(
                    pattern_type="regional",
                    pattern_description=f"Regional pattern in {region}: {diagnosis} ({count} cases)",
                    confidence=min(1.0, count / len(cases)),
                    supporting_cases=count,
                    region=region,
                    metadata={"diagnosis": diagnosis, "count": count}
                ))
        
        return insights
    
    def _perform_clustering(
        self,
        cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform clustering analysis on cases"""
        if not SKLEARN_AVAILABLE or len(cases) < 3:
            return []
        
        try:
            # Extract embeddings
            embeddings = []
            case_ids = []
            
            for case in cases:
                vector = case.get("vector")
                if vector and len(vector) == 768:
                    embeddings.append(vector)
                    case_ids.append(case.get("id"))
            
            if len(embeddings) < 3:
                return []
            
            # Normalize embeddings
            scaler = StandardScaler()
            embeddings_scaled = scaler.fit_transform(embeddings)
            
            # Perform DBSCAN clustering
            dbscan = DBSCAN(eps=0.5, min_samples=2)
            cluster_labels = dbscan.fit_predict(embeddings_scaled)
            
            # Group cases by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                if label != -1:  # -1 is noise in DBSCAN
                    clusters[label].append(case_ids[i])
            
            # Format cluster results
            cluster_results = []
            for cluster_id, case_ids_in_cluster in clusters.items():
                cluster_results.append({
                    "cluster_id": int(cluster_id),
                    "case_ids": case_ids_in_cluster,
                    "size": len(case_ids_in_cluster)
                })
            
            return cluster_results
            
        except Exception as e:
            logger.error(f"Error in clustering: {e}")
            return []
    
    def _update_recommendation_weights(
        self,
        insights: List[PatternInsight],
        clusters: List[Dict[str, Any]]
    ):
        """Update recommendation weights based on learned patterns"""
        # Increase weights for patterns with high confidence
        for insight in insights:
            if insight.confidence > 0.7:
                weight_key = insight.pattern_type
                if weight_key in self.recommendation_weights:
                    # Boost weight by confidence
                    self.recommendation_weights[weight_key] = min(
                        2.0,
                        self.recommendation_weights[weight_key] * (1 + insight.confidence * 0.1)
                    )
        
        # Boost weight if significant clusters found
        if len(clusters) > 0:
            self.recommendation_weights["diagnosis"] *= 1.1
        
        logger.info(f"Updated recommendation weights: {self.recommendation_weights}")

