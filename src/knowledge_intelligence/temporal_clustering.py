"""
Cross-Patient Temporal Clustering Service

Identifies clusters by time (week/month/season), location, symptom similarity, and lab pattern similarity.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import numpy as np

from ..storage.qdrant_storage import QdrantStorage
from ..retrieval.case_retrieval import CaseRetriever, RetrievalOptions
from ..visualization.temporal_trends import TemporalTrendAnalyzer

logger = logging.getLogger(__name__)

# Optional scikit-learn for clustering
try:
    from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")


@dataclass
class TemporalCluster:
    """Represents a temporal cluster of cases"""
    cluster_id: int
    case_ids: List[str]
    time_window: Tuple[datetime, datetime]
    characteristics: Dict[str, Any] = field(default_factory=dict)
    symptoms: List[str] = field(default_factory=list)
    diagnoses: List[str] = field(default_factory=list)
    lab_patterns: Dict[str, Any] = field(default_factory=dict)
    locations: List[str] = field(default_factory=list)
    size: int = 0
    density_score: float = 0.0


@dataclass
class TemporalClusteringResult:
    """Result of temporal clustering analysis"""
    clusters: List[TemporalCluster]
    time_granularity: str  # "weekly", "monthly", "seasonal"
    total_cases_analyzed: int
    clusters_by_time_window: Dict[str, List[int]] = field(default_factory=dict)
    pattern_insights: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TemporalClusteringService:
    """
    Cross-Patient Temporal Clustering Service
    
    Identifies clusters by:
    - Time (week/month/season)
    - Location
    - Symptom similarity
    - Lab pattern similarity
    """
    
    def __init__(
        self,
        qdrant_storage: Optional[QdrantStorage] = None,
        collection_name: str = "hygiaai_cases"
    ):
        """
        Initialize temporal clustering service
        
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
        
        logger.info("Temporal clustering service initialized")
    
    def cluster_by_temporal_window(
        self,
        time_granularity: str = "weekly",  # "weekly", "monthly", "seasonal"
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        region: Optional[str] = None,
        min_cluster_size: int = 3
    ) -> TemporalClusteringResult:
        """
        Cluster cases by temporal windows
        
        Args:
            time_granularity: Time granularity for clustering
            start_time: Start time for analysis
            end_time: End time for analysis
            region: Optional region filter
            min_cluster_size: Minimum cases per cluster
            
        Returns:
            TemporalClusteringResult with clusters and insights
        """
        try:
            # Set default time range if not provided
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            if start_time is None:
                if time_granularity == "weekly":
                    start_time = end_time - timedelta(weeks=4)
                elif time_granularity == "monthly":
                    start_time = end_time - timedelta(days=90)
                elif time_granularity == "seasonal":
                    start_time = end_time - timedelta(days=365)
                else:
                    start_time = end_time - timedelta(days=30)
            
            # Retrieve cases in time window
            options = RetrievalOptions(limit=1000)
            if region:
                options.region = region
            options.time_range = {"gte": start_time, "lte": end_time}
            
            retrieved_results = self.case_retriever.retrieve_similar_cases(
                query_text="",  # Get all cases in time range
                options=options
            )
            
            if len(retrieved_results) < min_cluster_size:
                logger.warning(f"Insufficient cases for clustering: {len(retrieved_results)}")
                return TemporalClusteringResult(
                    clusters=[],
                    time_granularity=time_granularity,
                    total_cases_analyzed=len(retrieved_results)
                )
            
            # Group cases by time windows
            cases_by_window = self._group_by_time_window(
                retrieved_results,
                time_granularity
            )
            
            # Perform clustering within each time window
            all_clusters = []
            clusters_by_window = {}
            
            for window_key, cases in cases_by_window.items():
                if len(cases) >= min_cluster_size:
                    window_clusters = self._cluster_cases_in_window(
                        cases,
                        window_key,
                        min_cluster_size
                    )
                    all_clusters.extend(window_clusters)
                    clusters_by_window[window_key] = [c.cluster_id for c in window_clusters]
            
            # Generate pattern insights
            pattern_insights = self._generate_pattern_insights(all_clusters)
            
            logger.info(f"Temporal clustering complete: {len(all_clusters)} clusters found")
            
            return TemporalClusteringResult(
                clusters=all_clusters,
                time_granularity=time_granularity,
                total_cases_analyzed=len(retrieved_results),
                clusters_by_time_window=clusters_by_window,
                pattern_insights=pattern_insights
            )
            
        except Exception as e:
            logger.error(f"Error in temporal clustering: {e}")
            return TemporalClusteringResult(
                clusters=[],
                time_granularity=time_granularity,
                total_cases_analyzed=0
            )
    
    def _group_by_time_window(
        self,
        cases: List[Any],
        granularity: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group cases by time window"""
        windows = defaultdict(list)
        
        for case in cases:
            # Extract timestamp from case
            timestamp_str = None
            if hasattr(case, 'case_data'):
                # RetrievalResult object
                payload = case.case_data.get("payload", {})
                timestamp_str = payload.get("timestamp")
            elif isinstance(case, dict):
                # Dictionary
                payload = case.get("payload", {})
                timestamp_str = payload.get("timestamp") or case.get("timestamp")
            
            if not timestamp_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except:
                continue
            
            # Determine window key based on granularity
            if granularity == "weekly":
                # Week of year
                week_num = timestamp.isocalendar()[1]
                year = timestamp.year
                window_key = f"{year}-W{week_num:02d}"
            elif granularity == "monthly":
                window_key = f"{timestamp.year}-{timestamp.month:02d}"
            elif granularity == "seasonal":
                # Season: Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
                quarter = (timestamp.month - 1) // 3 + 1
                window_key = f"{timestamp.year}-Q{quarter}"
            else:
                # Daily
                window_key = timestamp.strftime("%Y-%m-%d")
            
            # Convert RetrievalResult to dict if needed
            if hasattr(case, 'to_dict'):
                case_dict = case.to_dict()
            elif hasattr(case, 'case_data'):
                case_dict = {
                    "case_id": case.case_id,
                    "score": case.score,
                    "case_data": case.case_data,
                    "metadata": case.metadata.dict() if case.metadata and hasattr(case.metadata, 'dict') else None
                }
            else:
                case_dict = case
            windows[window_key].append(case_dict)
        
        return dict(windows)
    
    def _cluster_cases_in_window(
        self,
        cases: List[Dict[str, Any]],
        window_key: str,
        min_cluster_size: int
    ) -> List[TemporalCluster]:
        """Cluster cases within a time window"""
        if not SKLEARN_AVAILABLE or len(cases) < min_cluster_size:
            return []
        
        try:
            # Extract embeddings
            embeddings = []
            case_ids = []
            
            for case in cases:
                # Try to get embedding from case
                vector = case.get("vector") or case.get("embedding")
                if vector and len(vector) == 768:
                    embeddings.append(vector)
                    case_ids.append(case.get("case_id") or case.get("id", ""))
            
            if len(embeddings) < min_cluster_size:
                return []
            
            # Normalize embeddings
            scaler = StandardScaler()
            embeddings_scaled = scaler.fit_transform(embeddings)
            
            # Perform DBSCAN clustering
            dbscan = DBSCAN(eps=0.5, min_samples=min_cluster_size)
            cluster_labels = dbscan.fit_predict(embeddings_scaled)
            
            # Group cases by cluster
            clusters_dict = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                if label != -1:  # -1 is noise in DBSCAN
                    clusters_dict[label].append((case_ids[i], cases[i]))
            
            # Create TemporalCluster objects
            temporal_clusters = []
            for cluster_id, cluster_cases in clusters_dict.items():
                # Extract characteristics
                symptoms = []
                diagnoses = []
                locations = []
                
                for case_id, case_data in cluster_cases:
                    # Handle both dict and RetrievalResult formats
                    if isinstance(case_data, dict):
                        payload = case_data.get("payload", {}) or case_data.get("case_data", {}).get("payload", {})
                    else:
                        payload = {}
                    
                    metadata = payload.get("case_metadata", {})
                    
                    # Extract symptoms from SOAP
                    soap = payload.get("soap_note", {})
                    if soap:
                        subjective = soap.get("subjective", "")
                        # Simple extraction (in production, use NER)
                        if "fever" in subjective.lower():
                            symptoms.append("fever")
                        if "cough" in subjective.lower():
                            symptoms.append("cough")
                    
                    # Extract diagnosis
                    diagnosis = metadata.get("diagnosis")
                    if diagnosis:
                        diagnoses.append(diagnosis)
                    
                    # Extract location
                    location = metadata.get("region")
                    if location:
                        locations.append(location)
                
                # Determine time window
                timestamps = []
                for case_id, case_data in cluster_cases:
                    # Handle both dict and RetrievalResult formats
                    if isinstance(case_data, dict):
                        payload = case_data.get("payload", {}) or case_data.get("case_data", {}).get("payload", {})
                        ts = payload.get("timestamp") or case_data.get("timestamp")
                    else:
                        ts = None
                    
                    if ts:
                        try:
                            timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                        except:
                            pass
                
                time_window = (
                    min(timestamps) if timestamps else datetime.now(timezone.utc),
                    max(timestamps) if timestamps else datetime.now(timezone.utc)
                )
                
                cluster = TemporalCluster(
                    cluster_id=int(cluster_id),
                    case_ids=[cid for cid, _ in cluster_cases],
                    time_window=time_window,
                    symptoms=list(set(symptoms)),
                    diagnoses=list(set(diagnoses)),
                    locations=list(set(locations)),
                    size=len(cluster_cases),
                    density_score=len(cluster_cases) / len(cases) if cases else 0.0,
                    characteristics={
                        "window": window_key,
                        "symptom_count": len(set(symptoms)),
                        "diagnosis_count": len(set(diagnoses))
                    }
                )
                temporal_clusters.append(cluster)
            
            return temporal_clusters
            
        except Exception as e:
            logger.error(f"Error clustering cases in window {window_key}: {e}")
            return []
    
    def _generate_pattern_insights(
        self,
        clusters: List[TemporalCluster]
    ) -> List[Dict[str, Any]]:
        """Generate insights from clusters"""
        insights = []
        
        # Find clusters with high symptom/diagnosis similarity
        for cluster in clusters:
            if cluster.size >= 5:  # Significant cluster
                insight = {
                    "type": "temporal_cluster",
                    "cluster_id": cluster.cluster_id,
                    "size": cluster.size,
                    "time_window": {
                        "start": cluster.time_window[0].isoformat(),
                        "end": cluster.time_window[1].isoformat()
                    },
                    "common_symptoms": cluster.symptoms[:5],  # Top 5
                    "common_diagnoses": cluster.diagnoses[:5],
                    "locations": cluster.locations,
                    "density_score": cluster.density_score
                }
                insights.append(insight)
        
        return insights

