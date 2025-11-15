"""
Temporal Trend Analysis and Visualization

Analyzes temporal trends in clinical cases:
- Symptom trends over time
- Diagnosis patterns
- Treatment outcomes
- Prescription trends
- Demographic patterns
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from enum import Enum

from src.retrieval import CaseRetriever, RetrievalResult
from src.storage import QdrantStorage

logger = logging.getLogger(__name__)


class TrendGranularity(Enum):
    """Time granularity for trend analysis"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class TrendDataPoint:
    """Single data point in a trend"""
    timestamp: datetime
    value: float
    count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "count": self.count,
            "metadata": self.metadata
        }


@dataclass
class TrendData:
    """Complete trend data for visualization"""
    metric_name: str
    granularity: str
    data_points: List[TrendDataPoint] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_name": self.metric_name,
            "granularity": self.granularity,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "summary": self.summary,
            "metadata": self.metadata
        }


@dataclass
class TrendOptions:
    """Options for trend analysis"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: TrendGranularity = TrendGranularity.DAILY
    filters: Optional[Dict[str, Any]] = None  # Age group, region, etc.
    metrics: List[str] = field(default_factory=lambda: ["symptoms", "diagnoses", "outcomes"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "granularity": self.granularity.value,
            "filters": self.filters,
            "metrics": self.metrics
        }


class TemporalTrendAnalyzer:
    """
    Analyzes temporal trends in clinical cases
    
    Features:
    - Symptom trends over time
    - Diagnosis patterns
    - Treatment outcomes
    - Prescription trends
    - Demographic patterns
    - Outbreak detection signals
    """
    
    def __init__(
        self,
        qdrant_storage: QdrantStorage,
        case_retriever: Optional[CaseRetriever] = None
    ):
        """
        Initialize temporal trend analyzer
        
        Args:
            qdrant_storage: QdrantStorage instance for querying cases
            case_retriever: Optional CaseRetriever for advanced queries
        """
        self.storage = qdrant_storage
        self.case_retriever = case_retriever
        
        logger.info("Temporal trend analyzer initialized")
    
    def analyze_symptom_trends(
        self,
        options: Optional[TrendOptions] = None
    ) -> TrendData:
        """
        Analyze symptom trends over time
        
        Args:
            options: Optional trend analysis options
            
        Returns:
            TrendData with symptom frequency over time
        """
        options = options or TrendOptions()
        
        # Query cases within time range
        cases = self._query_cases_in_range(options)
        
        # Aggregate symptoms by time period
        symptom_counts = self._aggregate_by_time_period(
            cases=cases,
            extract_field="symptoms",
            granularity=options.granularity,
            options=options
        )
        
        # Generate trend data points
        data_points = []
        for timestamp, counts in sorted(symptom_counts.items()):
            total_count = sum(counts.values())
            unique_symptoms = len(counts)
            avg_per_case = total_count / len(cases) if cases else 0
            
            data_points.append(TrendDataPoint(
                timestamp=timestamp,
                value=avg_per_case,
                count=total_count,
                metadata={
                    "unique_symptoms": unique_symptoms,
                    "top_symptoms": sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
                }
            ))
        
        # Calculate summary statistics
        summary = self._calculate_summary(data_points)
        
        return TrendData(
            metric_name="symptom_trends",
            granularity=options.granularity.value,
            data_points=data_points,
            summary=summary,
            metadata={"total_cases": len(cases)}
        )
    
    def analyze_diagnosis_trends(
        self,
        options: Optional[TrendOptions] = None
    ) -> TrendData:
        """
        Analyze diagnosis trends over time
        
        Args:
            options: Optional trend analysis options
            
        Returns:
            TrendData with diagnosis frequency over time
        """
        options = options or TrendOptions()
        
        # Query cases within time range
        cases = self._query_cases_in_range(options)
        
        # Aggregate diagnoses by time period
        diagnosis_counts = self._aggregate_by_time_period(
            cases=cases,
            extract_field="diagnosis",
            granularity=options.granularity,
            options=options
        )
        
        # Generate trend data points
        data_points = []
        for timestamp, counts in sorted(diagnosis_counts.items()):
            total_count = sum(counts.values())
            unique_diagnoses = len(counts)
            
            data_points.append(TrendDataPoint(
                timestamp=timestamp,
                value=unique_diagnoses,
                count=total_count,
                metadata={
                    "unique_diagnoses": unique_diagnoses,
                    "top_diagnoses": sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
                }
            ))
        
        # Calculate summary statistics
        summary = self._calculate_summary(data_points)
        
        return TrendData(
            metric_name="diagnosis_trends",
            granularity=options.granularity.value,
            data_points=data_points,
            summary=summary,
            metadata={"total_cases": len(cases)}
        )
    
    def analyze_outcome_trends(
        self,
        options: Optional[TrendOptions] = None
    ) -> TrendData:
        """
        Analyze treatment outcome trends over time
        
        Args:
            options: Optional trend analysis options
            
        Returns:
            TrendData with outcome distribution over time
        """
        options = options or TrendOptions()
        
        # Query cases within time range
        cases = self._query_cases_in_range(options)
        
        # Aggregate outcomes by time period
        outcome_counts = self._aggregate_by_time_period(
            cases=cases,
            extract_field="outcome",
            granularity=options.granularity,
            options=options
        )
        
        # Generate trend data points
        data_points = []
        for timestamp, counts in sorted(outcome_counts.items()):
            total_count = sum(counts.values())
            
            # Calculate outcome rates
            outcome_rates = {
                outcome: (count / total_count * 100) if total_count > 0 else 0
                for outcome, count in counts.items()
            }
            
            data_points.append(TrendDataPoint(
                timestamp=timestamp,
                value=total_count,
                count=total_count,
                metadata={
                    "outcome_distribution": counts,
                    "outcome_rates": outcome_rates
                }
            ))
        
        # Calculate summary statistics
        summary = self._calculate_summary(data_points)
        
        return TrendData(
            metric_name="outcome_trends",
            granularity=options.granularity.value,
            data_points=data_points,
            summary=summary,
            metadata={"total_cases": len(cases)}
        )
    
    def detect_outbreak_signals(
        self,
        symptom_keywords: List[str],
        time_window_days: int = 7,
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect potential outbreak signals based on symptom surge
        
        Args:
            symptom_keywords: List of symptom keywords to monitor
            time_window_days: Time window in days to analyze
            threshold: Multiplier threshold for surge detection (e.g., 2.0 = 2x increase)
            
        Returns:
            Dictionary with outbreak signals and alerts
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=time_window_days)
        
        # Get recent cases
        recent_options = TrendOptions(
            start_date=start_date,
            end_date=end_date,
            granularity=TrendGranularity.DAILY
        )
        recent_cases = self._query_cases_in_range(recent_options)
        
        # Get baseline (previous period)
        baseline_start = start_date - timedelta(days=time_window_days)
        baseline_options = TrendOptions(
            start_date=baseline_start,
            end_date=start_date,
            granularity=TrendGranularity.DAILY
        )
        baseline_cases = self._query_cases_in_range(baseline_options)
        
        # Count symptom occurrences
        recent_counts = self._count_symptom_occurrences(recent_cases, symptom_keywords)
        baseline_counts = self._count_symptom_occurrences(baseline_cases, symptom_keywords)
        
        # Calculate surge ratios
        signals = []
        for symptom in symptom_keywords:
            recent_count = recent_counts.get(symptom, 0)
            baseline_count = baseline_counts.get(symptom, 0)
            
            if baseline_count > 0:
                surge_ratio = recent_count / baseline_count
                if surge_ratio >= threshold:
                    signals.append({
                        "symptom": symptom,
                        "recent_count": recent_count,
                        "baseline_count": baseline_count,
                        "surge_ratio": surge_ratio,
                        "alert_level": "high" if surge_ratio >= 3.0 else "medium"
                    })
        
        return {
            "time_window_days": time_window_days,
            "threshold": threshold,
            "signals": signals,
            "total_recent_cases": len(recent_cases),
            "total_baseline_cases": len(baseline_cases),
            "alert_count": len(signals)
        }
    
    def _query_cases_in_range(self, options: TrendOptions) -> List[Dict[str, Any]]:
        """Query cases within time range"""
        # Use dummy embedding for filter-based search
        dummy_embedding = [0.0] * self.storage.vector_size
        
        filters = {}
        if options.start_date:
            # Convert datetime to Unix timestamp for Qdrant Range filter
            start_timestamp = options.start_date.timestamp()
            filters["timestamp"] = {"gte": start_timestamp}
        if options.end_date:
            # Convert datetime to Unix timestamp for Qdrant Range filter
            end_timestamp = options.end_date.timestamp()
            if "timestamp" in filters:
                filters["timestamp"]["lte"] = end_timestamp
            else:
                filters["timestamp"] = {"lte": end_timestamp}
        
        # Apply additional filters
        if options.filters:
            filters.update(options.filters)
        
        # Search for cases
        results = self.storage.search_with_filters(
            query_embedding=dummy_embedding,
            filters=filters if filters else None,
            limit=10000  # Large limit for trend analysis
        )
        
        return results
    
    def _aggregate_by_time_period(
        self,
        cases: List[Dict[str, Any]],
        extract_field: str,
        granularity: TrendGranularity,
        options: TrendOptions
    ) -> Dict[datetime, Dict[str, int]]:
        """Aggregate cases by time period"""
        period_counts = defaultdict(lambda: defaultdict(int))
        
        for case in cases:
            payload = case.get("payload", {})
            timestamp_str = payload.get("timestamp")
            
            if not timestamp_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception:
                continue
            
            # Round to time period
            period_timestamp = self._round_to_period(timestamp, granularity)
            
            # Extract field value
            if extract_field == "symptoms":
                # Extract from medical entities
                entities = payload.get("medical_entities", [])
                for entity in entities:
                    if entity.get("entity_type") == "symptom":
                        symptom = entity.get("text", "")
                        if symptom:
                            period_counts[period_timestamp][symptom] += 1
            elif extract_field == "diagnosis":
                diagnosis = payload.get("diagnosis")
                if diagnosis:
                    period_counts[period_timestamp][diagnosis] += 1
            elif extract_field == "outcome":
                outcome = payload.get("outcome")
                if outcome:
                    period_counts[period_timestamp][outcome] += 1
        
        return dict(period_counts)
    
    def _round_to_period(self, timestamp: datetime, granularity: TrendGranularity) -> datetime:
        """Round timestamp to time period"""
        if granularity == TrendGranularity.HOURLY:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif granularity == TrendGranularity.DAILY:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TrendGranularity.WEEKLY:
            # Round to Monday
            days_since_monday = timestamp.weekday()
            return (timestamp - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TrendGranularity.MONTHLY:
            return timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TrendGranularity.YEARLY:
            return timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return timestamp
    
    def _calculate_summary(self, data_points: List[TrendDataPoint]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        if not data_points:
            return {}
        
        values = [dp.value for dp in data_points]
        counts = [dp.count for dp in data_points]
        
        return {
            "total_points": len(data_points),
            "min_value": min(values) if values else 0,
            "max_value": max(values) if values else 0,
            "avg_value": sum(values) / len(values) if values else 0,
            "total_count": sum(counts),
            "avg_count": sum(counts) / len(counts) if counts else 0
        }
    
    def _count_symptom_occurrences(
        self,
        cases: List[Dict[str, Any]],
        symptom_keywords: List[str]
    ) -> Dict[str, int]:
        """Count symptom occurrences in cases"""
        counts = defaultdict(int)
        
        for case in cases:
            payload = case.get("payload", {})
            entities = payload.get("medical_entities", [])
            
            for entity in entities:
                if entity.get("entity_type") == "symptom":
                    symptom_text = entity.get("text", "").lower()
                    for keyword in symptom_keywords:
                        if keyword.lower() in symptom_text:
                            counts[keyword] += 1
                            break
        
        return dict(counts)
    
    def generate_all_trends(
        self,
        options: Optional[TrendOptions] = None
    ) -> Dict[str, TrendData]:
        """
        Generate all trend analyses
        
        Args:
            options: Optional trend analysis options
            
        Returns:
            Dictionary of all trend data
        """
        options = options or TrendOptions()
        
        trends = {}
        
        if "symptoms" in options.metrics:
            trends["symptoms"] = self.analyze_symptom_trends(options)
        
        if "diagnoses" in options.metrics:
            trends["diagnoses"] = self.analyze_diagnosis_trends(options)
        
        if "outcomes" in options.metrics:
            trends["outcomes"] = self.analyze_outcome_trends(options)
        
        return trends

