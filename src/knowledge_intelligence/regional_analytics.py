"""
Regional Health Trend Analytics Service

Tracks rising diseases, common complaints, treatment success rates, and local outbreaks.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from ..storage.qdrant_storage import QdrantStorage
from ..retrieval.case_retrieval import CaseRetriever, RetrievalOptions
from ..visualization.temporal_trends import TemporalTrendAnalyzer
from ..outbreak.outbreak_detector import OutbreakDetector

logger = logging.getLogger(__name__)


@dataclass
class DiseaseTrend:
    """Trend data for a specific disease"""
    disease_name: str
    region: str
    current_frequency: int
    previous_frequency: int
    trend_direction: str  # "rising", "stable", "declining"
    change_percentage: float
    time_period: Dict[str, datetime]


@dataclass
class TreatmentSuccessMetric:
    """Treatment success metrics"""
    treatment: str
    region: str
    success_rate: float
    total_cases: int
    successful_outcomes: int
    time_period: Dict[str, datetime]


@dataclass
class RegionalHealthReport:
    """Comprehensive regional health analytics report"""
    region: str
    time_period: Dict[str, datetime]
    disease_trends: List[DiseaseTrend]
    common_complaints: List[Dict[str, Any]]
    treatment_success_rates: List[TreatmentSuccessMetric]
    outbreak_alerts: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RegionalHealthAnalytics:
    """
    Regional Health Trend Analytics Service
    
    Features:
    - Tracks rising diseases
    - Common complaints analysis
    - Treatment success rates
    - Local outbreak detection
    """
    
    def __init__(
        self,
        qdrant_storage: Optional[QdrantStorage] = None,
        collection_name: str = "hygiaai_cases"
    ):
        """
        Initialize regional health analytics service
        
        Args:
            qdrant_storage: QdrantStorage instance
            collection_name: Collection name for cases
        """
        import os
        
        if qdrant_storage:
            self.storage = qdrant_storage
        else:
            self.storage = QdrantStorage(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6334")),
                api_key=os.getenv("QDRANT_API_KEY"),
                collection_name=collection_name,
                vector_size=768
            )
        
        self.collection_name = collection_name
        self.case_retriever = CaseRetriever(qdrant_storage=self.storage)
        self.trend_analyzer = TemporalTrendAnalyzer(qdrant_storage=self.storage)
        self.outbreak_detector = OutbreakDetector(qdrant_storage=self.storage)
        
        logger.info("Regional health analytics service initialized")
    
    def analyze_regional_health(
        self,
        region: str,
        time_window_days: int = 30,
        compare_with_previous: bool = True
    ) -> RegionalHealthReport:
        """
        Generate comprehensive regional health analytics
        
        Args:
            region: Region to analyze
            time_window_days: Time window for current analysis
            compare_with_previous: Whether to compare with previous period
            
        Returns:
            RegionalHealthReport with all analytics
        """
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=time_window_days)
            
            # Retrieve cases for current period
            options = RetrievalOptions(limit=1000, region=region)
            options.time_range = {"gte": start_time, "lte": end_time}
            
            current_cases = self.case_retriever.retrieve_similar_cases(
                query_text="",
                options=options
            )
            
            # Retrieve cases for previous period (if comparison enabled)
            previous_cases = []
            if compare_with_previous:
                prev_start = start_time - timedelta(days=time_window_days)
                prev_options = RetrievalOptions(limit=1000, region=region)
                prev_options.time_range = {"gte": prev_start, "lte": start_time}
                
                previous_cases = self.case_retriever.retrieve_similar_cases(
                    query_text="",
                    options=prev_options
                )
            
            # Analyze disease trends
            disease_trends = self._analyze_disease_trends(
                current_cases,
                previous_cases,
                region,
                start_time,
                end_time
            )
            
            # Analyze common complaints
            common_complaints = self._analyze_common_complaints(current_cases)
            
            # Analyze treatment success rates
            treatment_success = self._analyze_treatment_success(
                current_cases,
                region,
                start_time,
                end_time
            )
            
            # Detect outbreaks
            outbreak_alerts = self._detect_outbreaks(current_cases, region)
            
            # Generate summary
            summary = self._generate_summary(
                disease_trends,
                common_complaints,
                treatment_success,
                outbreak_alerts
            )
            
            logger.info(f"Regional health analysis complete for {region}")
            
            return RegionalHealthReport(
                region=region,
                time_period={"start": start_time, "end": end_time},
                disease_trends=disease_trends,
                common_complaints=common_complaints,
                treatment_success_rates=treatment_success,
                outbreak_alerts=outbreak_alerts,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error in regional health analysis: {e}")
            return RegionalHealthReport(
                region=region,
                time_period={"start": datetime.now(timezone.utc), "end": datetime.now(timezone.utc)},
                disease_trends=[],
                common_complaints=[],
                treatment_success_rates=[],
                outbreak_alerts=[],
                summary={}
            )
    
    def _analyze_disease_trends(
        self,
        current_cases: List[Any],
        previous_cases: List[Any],
        region: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[DiseaseTrend]:
        """Analyze disease frequency trends"""
        # Count diseases in current period
        current_diseases = defaultdict(int)
        for case in current_cases:
            if hasattr(case, 'case_data'):
                # RetrievalResult object
                payload = case.case_data.get("payload", {})
            elif isinstance(case, dict):
                # Dictionary
                payload = case.get("payload", {}) or case.get("case_data", {}).get("payload", {})
            else:
                payload = {}
            
            metadata = payload.get("case_metadata", {})
            diagnosis = metadata.get("diagnosis")
            if diagnosis:
                current_diseases[diagnosis] += 1
        
        # Count diseases in previous period
        previous_diseases = defaultdict(int)
        for case in previous_cases:
            if hasattr(case, 'case_data'):
                # RetrievalResult object
                payload = case.case_data.get("payload", {})
            elif isinstance(case, dict):
                # Dictionary
                payload = case.get("payload", {}) or case.get("case_data", {}).get("payload", {})
            else:
                payload = {}
            
            metadata = payload.get("case_metadata", {})
            diagnosis = metadata.get("diagnosis")
            if diagnosis:
                previous_diseases[diagnosis] += 1
        
        # Calculate trends
        trends = []
        all_diseases = set(list(current_diseases.keys()) + list(previous_diseases.keys()))
        
        for disease in all_diseases:
            current_freq = current_diseases.get(disease, 0)
            previous_freq = previous_diseases.get(disease, 0)
            
            if previous_freq > 0:
                change_pct = ((current_freq - previous_freq) / previous_freq) * 100
            elif current_freq > 0:
                change_pct = 100.0  # New disease
            else:
                change_pct = 0.0
            
            if change_pct > 20:
                direction = "rising"
            elif change_pct < -20:
                direction = "declining"
            else:
                direction = "stable"
            
            trends.append(DiseaseTrend(
                disease_name=disease,
                region=region,
                current_frequency=current_freq,
                previous_frequency=previous_freq,
                trend_direction=direction,
                change_percentage=change_pct,
                time_period={"start": start_time, "end": end_time}
            ))
        
        # Sort by change percentage (descending)
        trends.sort(key=lambda x: x.change_percentage, reverse=True)
        
        return trends
    
    def _analyze_common_complaints(
        self,
        cases: List[Any]
    ) -> List[Dict[str, Any]]:
        """Analyze common complaints/symptoms"""
        complaint_counts = defaultdict(int)
        
        for case in cases:
            if hasattr(case, 'case_data'):
                # RetrievalResult object
                payload = case.case_data.get("payload", {})
            elif isinstance(case, dict):
                # Dictionary
                payload = case.get("payload", {}) or case.get("case_data", {}).get("payload", {})
            else:
                payload = {}
            
            soap = payload.get("soap_note", {})
            
            if soap:
                subjective = soap.get("subjective", "").lower()
                # Extract common complaint keywords
                complaints = ["fever", "cough", "headache", "pain", "nausea", "fatigue", "shortness of breath"]
                for complaint in complaints:
                    if complaint in subjective:
                        complaint_counts[complaint] += 1
        
        # Convert to list and sort
        common_complaints = [
            {"complaint": complaint, "frequency": count}
            for complaint, count in sorted(complaint_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return common_complaints[:10]  # Top 10
    
    def _analyze_treatment_success(
        self,
        cases: List[Any],
        region: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[TreatmentSuccessMetric]:
        """Analyze treatment success rates"""
        treatment_outcomes = defaultdict(lambda: {"success": 0, "total": 0})
        
        for case in cases:
            if hasattr(case, 'case_data'):
                # RetrievalResult object
                payload = case.case_data.get("payload", {})
            elif isinstance(case, dict):
                # Dictionary
                payload = case.get("payload", {}) or case.get("case_data", {}).get("payload", {})
            else:
                payload = {}
            
            metadata = payload.get("case_metadata", {})
            
            # Extract treatment from plan
            soap = payload.get("soap_note", {})
            plan = soap.get("plan", "") if soap else ""
            
            # Simple extraction (in production, use NER)
            if "amoxicillin" in plan.lower():
                treatment = "amoxicillin"
            elif "paracetamol" in plan.lower() or "acetaminophen" in plan.lower():
                treatment = "paracetamol"
            elif "antibiotic" in plan.lower():
                treatment = "antibiotic"
            else:
                continue
            
            outcome = metadata.get("outcome", "").lower()
            treatment_outcomes[treatment]["total"] += 1
            
            if outcome in ["recovered", "improved", "success"]:
                treatment_outcomes[treatment]["success"] += 1
        
        # Calculate success rates
        success_metrics = []
        for treatment, data in treatment_outcomes.items():
            if data["total"] > 0:
                success_rate = (data["success"] / data["total"]) * 100
                success_metrics.append(TreatmentSuccessMetric(
                    treatment=treatment,
                    region=region,
                    success_rate=success_rate,
                    total_cases=data["total"],
                    successful_outcomes=data["success"],
                    time_period={"start": start_time, "end": end_time}
                ))
        
        return success_metrics
    
    def _detect_outbreaks(
        self,
        cases: List[Any],
        region: str
    ) -> List[Dict[str, Any]]:
        """Detect outbreaks in the region"""
        try:
            # Use outbreak detector
            alerts = self.outbreak_detector.detect_outbreaks(
                time_window_days=7,
                region=region,
                min_cluster_size=3
            )
            
            # Format alerts
            formatted_alerts = []
            for alert in alerts:
                formatted_alerts.append({
                    "alert_id": alert.alert_id,
                    "level": alert.level.value,
                    "message": alert.message,
                    "cluster_size": alert.cluster.size,
                    "symptoms": alert.cluster.symptoms,
                    "diagnoses": alert.cluster.diagnoses,
                    "confidence": alert.confidence
                })
            
            return formatted_alerts
            
        except Exception as e:
            logger.error(f"Error detecting outbreaks: {e}")
            return []
    
    def _generate_summary(
        self,
        disease_trends: List[DiseaseTrend],
        common_complaints: List[Dict[str, Any]],
        treatment_success: List[TreatmentSuccessMetric],
        outbreak_alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of regional health"""
        rising_diseases = [d for d in disease_trends if d.trend_direction == "rising"]
        top_complaints = common_complaints[:5]
        avg_treatment_success = sum(t.success_rate for t in treatment_success) / len(treatment_success) if treatment_success else 0
        
        return {
            "total_diseases_tracked": len(disease_trends),
            "rising_diseases_count": len(rising_diseases),
            "top_rising_diseases": [d.disease_name for d in rising_diseases[:5]],
            "top_complaints": [c["complaint"] for c in top_complaints],
            "average_treatment_success_rate": avg_treatment_success,
            "outbreak_alerts_count": len(outbreak_alerts),
            "critical_alerts": len([a for a in outbreak_alerts if a.get("level") == "critical"])
        }

