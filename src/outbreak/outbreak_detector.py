"""
Advanced Outbreak Detection Module

Implements clustering-based outbreak detection with multiple algorithms:
- DBSCAN for density-based clustering
- K-means for centroid-based clustering
- Hierarchical clustering for nested patterns
- Anomaly detection using statistical methods
- Spatial and temporal clustering
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from collections import defaultdict
import numpy as np

from src.storage import QdrantStorage
from src.retrieval import CaseRetriever

logger = logging.getLogger(__name__)

# Optional scikit-learn for advanced clustering
try:
    from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.neighbors import LocalOutlierFactor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")


class DetectionMethod(Enum):
    """Outbreak detection methods"""
    SURGE_BASED = "surge_based"  # Simple surge detection (existing)
    DBSCAN = "dbscan"  # Density-based clustering
    KMEANS = "kmeans"  # Centroid-based clustering
    HIERARCHICAL = "hierarchical"  # Hierarchical clustering
    ANOMALY_DETECTION = "anomaly_detection"  # Statistical anomaly detection
    SPATIAL_TEMPORAL = "spatial_temporal"  # Combined spatial and temporal clustering


class AlertLevel(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OutbreakCluster:
    """Represents a detected outbreak cluster"""
    cluster_id: int
    case_ids: List[str]
    size: int
    centroid: Optional[List[float]] = None
    symptoms: List[str] = field(default_factory=list)
    diagnoses: List[str] = field(default_factory=list)
    time_range: Optional[Tuple[datetime, datetime]] = None
    spatial_center: Optional[Tuple[float, float]] = None  # (lat, lon) if available
    density_score: float = 0.0
    anomaly_score: float = 0.0


@dataclass
class OutbreakAlert:
    """Outbreak alert with details"""
    alert_id: str
    level: AlertLevel
    cluster: OutbreakCluster
    message: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutbreakDetectionOptions:
    """Options for outbreak detection"""
    method: DetectionMethod = DetectionMethod.DBSCAN
    time_window_days: int = 7
    min_cluster_size: int = 3
    max_cluster_size: Optional[int] = None
    threshold: float = 2.0  # Surge threshold for surge-based method
    eps: float = 0.5  # DBSCAN epsilon parameter
    min_samples: int = 3  # DBSCAN min_samples parameter
    num_clusters: Optional[int] = None  # For K-means/hierarchical
    anomaly_threshold: float = 0.95  # For anomaly detection
    spatial_enabled: bool = False  # Enable spatial clustering if coordinates available
    symptom_keywords: Optional[List[str]] = None
    diagnosis_keywords: Optional[List[str]] = None
    region_filter: Optional[str] = None


@dataclass
class OutbreakDetectionResult:
    """Result of outbreak detection analysis"""
    alerts: List[OutbreakAlert] = field(default_factory=list)
    clusters: List[OutbreakCluster] = field(default_factory=list)
    total_cases_analyzed: int = 0
    anomaly_cases: List[str] = field(default_factory=list)
    detection_method: str = ""
    detection_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class OutbreakDetector:
    """
    Advanced outbreak detection system
    
    Features:
    - Multiple clustering algorithms (DBSCAN, K-means, hierarchical)
    - Anomaly detection using statistical methods
    - Spatial and temporal clustering
    - Configurable alert thresholds
    - Alert generation with recommendations
    """
    
    def __init__(
        self,
        qdrant_storage: QdrantStorage,
        case_retriever: Optional[CaseRetriever] = None
    ):
        """
        Initialize outbreak detector
        
        Args:
            qdrant_storage: QdrantStorage instance
            case_retriever: Optional CaseRetriever for advanced queries
        """
        self.storage = qdrant_storage
        self.case_retriever = case_retriever
        
        if not SKLEARN_AVAILABLE:
            logger.warning(
                "scikit-learn not available. Advanced clustering methods will be limited. "
                "Install with: pip install scikit-learn"
            )
        
        logger.info("Outbreak detector initialized")
    
    def detect_outbreaks(
        self,
        options: Optional[OutbreakDetectionOptions] = None
    ) -> OutbreakDetectionResult:
        """
        Detect outbreaks using specified method
        
        Args:
            options: Detection options
            
        Returns:
            OutbreakDetectionResult with alerts and clusters
        """
        options = options or OutbreakDetectionOptions()
        
        # Retrieve cases within time window
        cases = self._retrieve_cases(options)
        
        if not cases:
            logger.warning("No cases found for outbreak detection")
            return OutbreakDetectionResult(
                total_cases_analyzed=0,
                detection_method=options.method.value
            )
        
        # Extract features for clustering
        features, case_metadata = self._extract_features(cases, options)
        
        if len(features) < options.min_cluster_size:
            logger.warning(f"Insufficient cases for clustering: {len(features)} < {options.min_cluster_size}")
            return OutbreakDetectionResult(
                total_cases_analyzed=len(cases),
                detection_method=options.method.value
            )
        
        # Apply detection method
        if options.method == DetectionMethod.SURGE_BASED:
            result = self._detect_surge_based(cases, options)
        elif options.method == DetectionMethod.DBSCAN:
            result = self._detect_dbscan(features, case_metadata, options)
        elif options.method == DetectionMethod.KMEANS:
            result = self._detect_kmeans(features, case_metadata, options)
        elif options.method == DetectionMethod.HIERARCHICAL:
            result = self._detect_hierarchical(features, case_metadata, options)
        elif options.method == DetectionMethod.ANOMALY_DETECTION:
            result = self._detect_anomalies(features, case_metadata, options)
        elif options.method == DetectionMethod.SPATIAL_TEMPORAL:
            result = self._detect_spatial_temporal(cases, features, case_metadata, options)
        else:
            logger.error(f"Unknown detection method: {options.method}")
            result = OutbreakDetectionResult(
                total_cases_analyzed=len(cases),
                detection_method=options.method.value
            )
        
        result.total_cases_analyzed = len(cases)
        result.detection_method = options.method.value
        
        # Generate alerts from clusters
        result.alerts = self._generate_alerts(result.clusters, options)
        
        return result
    
    def _retrieve_cases(self, options: OutbreakDetectionOptions) -> List[Dict[str, Any]]:
        """Retrieve cases within time window"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=options.time_window_days)
        
        # Build filters - use Unix timestamps for Qdrant Range filter
        filters = {
            "timestamp": {
                "gte": start_date.timestamp(),
                "lte": end_date.timestamp()
            }
        }
        
        if options.region_filter:
            filters["region"] = options.region_filter
        
        # Retrieve cases
        dummy_embedding = [0.0] * self.storage.vector_size
        
        # Retrieve all cases and filter by timestamp in Python
        # This is more reliable since timestamps are stored as ISO strings in Qdrant
        filters_no_time = {k: v for k, v in filters.items() if k != "timestamp"}
        results = self.storage.search_with_filters(
            query_embedding=dummy_embedding,
            filters=filters_no_time if filters_no_time else None,
            limit=10000
        )
        
        # Filter by timestamp in Python (since Qdrant stores timestamps as ISO strings)
        filtered_results = []
        for result in results:
            payload = result.get("payload", {})
            timestamp_str = payload.get("timestamp")
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
                    if start_date <= timestamp <= end_date:
                        filtered_results.append(result)
                except Exception as e:
                    logger.debug(f"Error parsing timestamp {timestamp_str}: {e}")
                    continue
        
        results = filtered_results
        
        return results
    
    def _extract_features(
        self,
        cases: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Extract features from cases for clustering
        
        Features:
        - Symptom vectors (binary or count)
        - Diagnosis vectors
        - Temporal features (day of week, hour, etc.)
        - Spatial features (if available)
        - Embedding vectors (if available)
        """
        features_list = []
        case_metadata = []
        
        for case in cases:
            payload = case.get("payload", {})
            case_id = case.get("id", "")
            
            # Extract symptoms
            symptoms = []
            entities = payload.get("medical_entities", [])
            for entity in entities:
                if entity.get("entity_type") == "symptom":
                    symptoms.append(entity.get("text", "").lower())
            
            # Extract diagnoses
            diagnoses = []
            diagnosis = payload.get("diagnosis")
            if diagnosis:
                diagnoses.append(diagnosis.lower())
            for entity in entities:
                if entity.get("entity_type") == "diagnosis":
                    diagnoses.append(entity.get("text", "").lower())
            
            # Extract temporal features
            timestamp_str = payload.get("timestamp")
            temporal_features = []
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    temporal_features = [
                        timestamp.hour / 24.0,  # Normalized hour
                        timestamp.weekday() / 7.0,  # Normalized day of week
                        (timestamp - datetime.now(timezone.utc)).total_seconds() / (7 * 24 * 3600)  # Days ago (normalized)
                    ]
                except Exception:
                    temporal_features = [0.0, 0.0, 0.0]
            else:
                temporal_features = [0.0, 0.0, 0.0]
            
            # Build feature vector
            # Symptom features (if keywords provided)
            symptom_features = []
            if options.symptom_keywords:
                for keyword in options.symptom_keywords:
                    symptom_features.append(1.0 if keyword.lower() in [s.lower() for s in symptoms] else 0.0)
            else:
                # Use all symptoms (simplified - would need vocabulary in production)
                symptom_features = [1.0 if s else 0.0 for s in symptoms[:10]]  # Limit to first 10
            
            # Diagnosis features
            diagnosis_features = []
            if options.diagnosis_keywords:
                for keyword in options.diagnosis_keywords:
                    diagnosis_features.append(1.0 if keyword.lower() in [d.lower() for d in diagnoses] else 0.0)
            else:
                diagnosis_features = [1.0 if d else 0.0 for d in diagnoses[:5]]  # Limit to first 5
            
            # Combine features
            feature_vector = temporal_features + symptom_features + diagnosis_features
            
            # Pad or truncate to fixed size
            target_size = 20  # Fixed feature size
            if len(feature_vector) < target_size:
                feature_vector.extend([0.0] * (target_size - len(feature_vector)))
            else:
                feature_vector = feature_vector[:target_size]
            
            features_list.append(feature_vector)
            case_metadata.append({
                "case_id": case_id,
                "symptoms": symptoms,
                "diagnoses": diagnoses,
                "timestamp": timestamp_str,
                "payload": payload
            })
        
        return np.array(features_list), case_metadata
    
    def _detect_surge_based(
        self,
        cases: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> OutbreakDetectionResult:
        """Surge-based detection (existing method)"""
        # This is similar to TemporalTrendAnalyzer.detect_outbreak_signals
        # but integrated into the new system
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=options.time_window_days)
        baseline_start = start_date - timedelta(days=options.time_window_days)
        
        # Count symptoms in recent and baseline periods
        recent_symptom_counts = {}
        baseline_symptom_counts = {}
        
        symptom_keywords = options.symptom_keywords or []
        
        for case in cases:
            try:
                payload = case.get("payload", {})
                timestamp_str = payload.get("timestamp")
                if not timestamp_str:
                    continue
                
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                entities = payload.get("medical_entities", [])
                for entity in entities:
                    if entity.get("entity_type") == "symptom":
                        symptom = entity.get("text", "").lower()
                        if symptom_keywords:
                            for keyword in symptom_keywords:
                                if keyword.lower() in symptom:
                                    if start_date <= timestamp <= end_date:
                                        recent_symptom_counts[keyword] = recent_symptom_counts.get(keyword, 0) + 1
                                    elif baseline_start <= timestamp < start_date:
                                        baseline_symptom_counts[keyword] = baseline_symptom_counts.get(keyword, 0) + 1
                        else:
                            if start_date <= timestamp <= end_date:
                                recent_symptom_counts[symptom] = recent_symptom_counts.get(symptom, 0) + 1
                            elif baseline_start <= timestamp < start_date:
                                baseline_symptom_counts[symptom] = baseline_symptom_counts.get(symptom, 0) + 1
            except Exception:
                continue
        
        # Detect surges
        clusters = []
        for symptom, recent_count in recent_symptom_counts.items():
            baseline_count = baseline_symptom_counts.get(symptom, 0)
            if baseline_count > 0:
                surge_ratio = recent_count / baseline_count
                if surge_ratio >= options.threshold:
                    # Create cluster for this symptom surge
                    cluster = OutbreakCluster(
                        cluster_id=len(clusters),
                        case_ids=[],  # Would need to track case IDs
                        size=recent_count,
                        symptoms=[symptom],
                        density_score=surge_ratio,
                        anomaly_score=surge_ratio
                    )
                    clusters.append(cluster)
        
        return OutbreakDetectionResult(clusters=clusters)
    
    def _detect_dbscan(
        self,
        features: np.ndarray,
        case_metadata: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> OutbreakDetectionResult:
        """DBSCAN density-based clustering"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, falling back to simple clustering")
            return self._detect_simple_clustering(features, case_metadata, options)
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Apply DBSCAN
        dbscan = DBSCAN(eps=options.eps, min_samples=options.min_samples)
        cluster_labels = dbscan.fit_predict(features_scaled)
        
        # Build clusters
        clusters = []
        noise_cases = []
        
        unique_labels = set(cluster_labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # -1 is noise in DBSCAN
        
        for label in unique_labels:
            cluster_indices = np.where(cluster_labels == label)[0]
            if len(cluster_indices) >= options.min_cluster_size:
                case_ids = [case_metadata[i]["case_id"] for i in cluster_indices]
                cluster_symptoms = []
                cluster_diagnoses = []
                
                for i in cluster_indices:
                    cluster_symptoms.extend(case_metadata[i]["symptoms"])
                    cluster_diagnoses.extend(case_metadata[i]["diagnoses"])
                
                # Calculate centroid
                cluster_features = features_scaled[cluster_indices]
                centroid = cluster_features.mean(axis=0).tolist()
                
                # Calculate density score
                density_score = len(cluster_indices) / (len(features) + 1)
                
                cluster = OutbreakCluster(
                    cluster_id=int(label),
                    case_ids=case_ids,
                    size=len(cluster_indices),
                    centroid=centroid,
                    symptoms=list(set(cluster_symptoms)),
                    diagnoses=list(set(cluster_diagnoses)),
                    density_score=density_score,
                    anomaly_score=density_score
                )
                clusters.append(cluster)
        
        # Noise points are potential anomalies
        noise_indices = np.where(cluster_labels == -1)[0]
        anomaly_cases = [case_metadata[i]["case_id"] for i in noise_indices]
        
        return OutbreakDetectionResult(
            clusters=clusters,
            anomaly_cases=anomaly_cases
        )
    
    def _detect_kmeans(
        self,
        features: np.ndarray,
        case_metadata: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> OutbreakDetectionResult:
        """K-means clustering"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, falling back to simple clustering")
            return self._detect_simple_clustering(features, case_metadata, options)
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Determine number of clusters
        num_clusters = options.num_clusters or min(10, max(2, len(features) // 10))
        
        # Apply K-means
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # Build clusters
        clusters = []
        for label in range(num_clusters):
            cluster_indices = np.where(cluster_labels == label)[0]
            if len(cluster_indices) >= options.min_cluster_size:
                case_ids = [case_metadata[i]["case_id"] for i in cluster_indices]
                cluster_symptoms = []
                cluster_diagnoses = []
                
                for i in cluster_indices:
                    cluster_symptoms.extend(case_metadata[i]["symptoms"])
                    cluster_diagnoses.extend(case_metadata[i]["diagnoses"])
                
                cluster = OutbreakCluster(
                    cluster_id=int(label),
                    case_ids=case_ids,
                    size=len(cluster_indices),
                    centroid=kmeans.cluster_centers_[label].tolist(),
                    symptoms=list(set(cluster_symptoms)),
                    diagnoses=list(set(cluster_diagnoses)),
                    density_score=len(cluster_indices) / len(features)
                )
                clusters.append(cluster)
        
        return OutbreakDetectionResult(clusters=clusters)
    
    def _detect_hierarchical(
        self,
        features: np.ndarray,
        case_metadata: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> OutbreakDetectionResult:
        """Hierarchical clustering"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, falling back to simple clustering")
            return self._detect_simple_clustering(features, case_metadata, options)
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Determine number of clusters
        num_clusters = options.num_clusters or min(10, max(2, len(features) // 10))
        
        # Apply hierarchical clustering
        hierarchical = AgglomerativeClustering(n_clusters=num_clusters)
        cluster_labels = hierarchical.fit_predict(features_scaled)
        
        # Build clusters (similar to K-means)
        clusters = []
        for label in range(num_clusters):
            cluster_indices = np.where(cluster_labels == label)[0]
            if len(cluster_indices) >= options.min_cluster_size:
                case_ids = [case_metadata[i]["case_id"] for i in cluster_indices]
                cluster_symptoms = []
                cluster_diagnoses = []
                
                for i in cluster_indices:
                    cluster_symptoms.extend(case_metadata[i]["symptoms"])
                    cluster_diagnoses.extend(case_metadata[i]["diagnoses"])
                
                cluster_features = features_scaled[cluster_indices]
                centroid = cluster_features.mean(axis=0).tolist()
                
                cluster = OutbreakCluster(
                    cluster_id=int(label),
                    case_ids=case_ids,
                    size=len(cluster_indices),
                    centroid=centroid,
                    symptoms=list(set(cluster_symptoms)),
                    diagnoses=list(set(cluster_diagnoses)),
                    density_score=len(cluster_indices) / len(features)
                )
                clusters.append(cluster)
        
        return OutbreakDetectionResult(clusters=clusters)
    
    def _detect_anomalies(
        self,
        features: np.ndarray,
        case_metadata: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> OutbreakDetectionResult:
        """Anomaly detection using Local Outlier Factor"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, cannot perform anomaly detection")
            return OutbreakDetectionResult()
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Apply Local Outlier Factor
        lof = LocalOutlierFactor(n_neighbors=min(20, len(features) - 1), contamination=0.1)
        outlier_labels = lof.fit_predict(features_scaled)
        outlier_scores = -lof.negative_outlier_factor_  # Convert to positive scores
        
        # Identify anomalies
        anomaly_indices = np.where(outlier_labels == -1)[0]
        anomaly_cases = []
        
        for i in anomaly_indices:
            if outlier_scores[i] >= options.anomaly_threshold:
                anomaly_cases.append(case_metadata[i]["case_id"])
        
        # Group anomalies into clusters if they're similar
        clusters = []
        if len(anomaly_indices) >= options.min_cluster_size:
            # Simple clustering of anomalies
            anomaly_features = features_scaled[anomaly_indices]
            dbscan = DBSCAN(eps=options.eps, min_samples=2)
            anomaly_cluster_labels = dbscan.fit_predict(anomaly_features)
            
            for label in set(anomaly_cluster_labels):
                if label != -1:  # Skip noise
                    cluster_anomaly_indices = anomaly_indices[np.where(anomaly_cluster_labels == label)[0]]
                    case_ids = [case_metadata[i]["case_id"] for i in cluster_anomaly_indices]
                    
                    cluster = OutbreakCluster(
                        cluster_id=len(clusters),
                        case_ids=case_ids,
                        size=len(cluster_anomaly_indices),
                        anomaly_score=outlier_scores[cluster_anomaly_indices].mean(),
                        density_score=len(cluster_anomaly_indices) / len(features)
                    )
                    clusters.append(cluster)
        
        return OutbreakDetectionResult(
            clusters=clusters,
            anomaly_cases=anomaly_cases
        )
    
    def _detect_spatial_temporal(
        self,
        cases: List[Dict[str, Any]],
        features: np.ndarray,
        case_metadata: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> OutbreakDetectionResult:
        """Spatial-temporal clustering (combines spatial and temporal features)"""
        # This would require geographic coordinates in case data
        # For now, use temporal features enhanced with basic spatial if available
        # In production, would use actual lat/lon coordinates
        
        # Use DBSCAN on enhanced features
        return self._detect_dbscan(features, case_metadata, options)
    
    def _detect_simple_clustering(
        self,
        features: np.ndarray,
        case_metadata: List[Dict[str, Any]],
        options: OutbreakDetectionOptions
    ) -> OutbreakDetectionResult:
        """Simple clustering fallback when scikit-learn is not available"""
        # Simple distance-based clustering
        clusters = []
        
        # Group cases by similar symptoms/diagnoses
        symptom_groups = {}
        for i, metadata in enumerate(case_metadata):
            key = tuple(sorted(set(metadata["symptoms"][:3])))  # Use top 3 symptoms as key
            if key not in symptom_groups:
                symptom_groups[key] = []
            symptom_groups[key].append(i)
        
        cluster_id = 0
        for key, indices in symptom_groups.items():
            if len(indices) >= options.min_cluster_size:
                case_ids = [case_metadata[i]["case_id"] for i in indices]
                cluster_symptoms = []
                for i in indices:
                    cluster_symptoms.extend(case_metadata[i]["symptoms"])
                
                cluster = OutbreakCluster(
                    cluster_id=cluster_id,
                    case_ids=case_ids,
                    size=len(indices),
                    symptoms=list(set(cluster_symptoms)),
                    density_score=len(indices) / len(features)
                )
                clusters.append(cluster)
                cluster_id += 1
        
        return OutbreakDetectionResult(clusters=clusters)
    
    def _generate_alerts(
        self,
        clusters: List[OutbreakCluster],
        options: OutbreakDetectionOptions
    ) -> List[OutbreakAlert]:
        """Generate alerts from detected clusters"""
        alerts = []
        
        for cluster in clusters:
            # Determine alert level
            if cluster.density_score >= 0.3 or cluster.anomaly_score >= 3.0:
                level = AlertLevel.CRITICAL
            elif cluster.density_score >= 0.2 or cluster.anomaly_score >= 2.0:
                level = AlertLevel.HIGH
            elif cluster.density_score >= 0.1 or cluster.anomaly_score >= 1.5:
                level = AlertLevel.MEDIUM
            else:
                level = AlertLevel.LOW
            
            # Generate message
            symptom_str = ", ".join(cluster.symptoms[:3]) if cluster.symptoms else "unknown symptoms"
            message = f"Outbreak cluster detected: {cluster.size} cases with {symptom_str}"
            
            # Recommended actions
            recommended_actions = [
                "Review cluster cases for common patterns",
                "Check if cases are geographically clustered",
                "Verify if cases share common exposures",
                "Consider enhanced surveillance for similar cases"
            ]
            
            if level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
                recommended_actions.append("Notify public health authorities")
                recommended_actions.append("Consider isolation protocols")
            
            alert = OutbreakAlert(
                alert_id=f"alert-{cluster.cluster_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                level=level,
                cluster=cluster,
                message=message,
                confidence=min(1.0, cluster.density_score + cluster.anomaly_score / 5.0),
                recommended_actions=recommended_actions,
                metadata={
                    "cluster_size": cluster.size,
                    "density_score": cluster.density_score,
                    "anomaly_score": cluster.anomaly_score
                }
            )
            alerts.append(alert)
        
        return alerts

