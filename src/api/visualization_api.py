"""
FastAPI endpoints for visualization data

Provides REST API endpoints for:
- Temporal trend data
- Case map visualization
- Dashboard data
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field

from src.visualization import (
    TemporalTrendAnalyzer,
    TrendOptions,
    TrendGranularity,
    CaseMapGenerator,
    MapOptions,
    MapProjection
)
from src.storage import QdrantStorage
from src.retrieval import CaseRetriever

router = APIRouter(prefix="/api/visualization", tags=["visualization"])


# Dependency injection
def get_qdrant_storage() -> QdrantStorage:
    """Get Qdrant storage instance"""
    return QdrantStorage(
        host="localhost",
        port=6333,
        enable_encryption=False,
        enable_deidentification=False
    )


def get_case_retriever() -> CaseRetriever:
    """Get case retriever instance"""
    storage = get_qdrant_storage()
    return CaseRetriever(qdrant_storage=storage)


def get_trend_analyzer() -> TemporalTrendAnalyzer:
    """Get trend analyzer instance"""
    storage = get_qdrant_storage()
    retriever = get_case_retriever()
    return TemporalTrendAnalyzer(
        qdrant_storage=storage,
        case_retriever=retriever
    )


def get_case_map_generator() -> CaseMapGenerator:
    """Get case map generator instance"""
    storage = get_qdrant_storage()
    retriever = get_case_retriever()
    return CaseMapGenerator(
        qdrant_storage=storage,
        case_retriever=retriever
    )


# Request/Response models
class TrendRequest(BaseModel):
    """Request model for trend analysis"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: str = "daily"  # hourly, daily, weekly, monthly, yearly
    filters: Optional[Dict[str, Any]] = None
    metrics: List[str] = Field(default_factory=lambda: ["symptoms", "diagnoses", "outcomes"])


class CaseMapRequest(BaseModel):
    """Request model for case map generation"""
    query_case_id: Optional[str] = None
    limit: int = 100
    projection_method: str = "simple_2d"  # umap, pca, tsne, simple_2d
    dimensions: int = 2  # 2 or 3
    cluster_cases: bool = True
    num_clusters: Optional[int] = None


class OutbreakDetectionRequest(BaseModel):
    """Request model for outbreak detection"""
    symptom_keywords: List[str]
    time_window_days: int = 7
    threshold: float = 2.0


class AdvancedOutbreakDetectionRequest(BaseModel):
    """Request model for advanced outbreak detection"""
    method: str = "dbscan"  # surge_based, dbscan, kmeans, hierarchical, anomaly_detection, spatial_temporal
    time_window_days: int = 7
    min_cluster_size: int = 3
    threshold: float = 2.0
    symptom_keywords: Optional[List[str]] = None
    diagnosis_keywords: Optional[List[str]] = None
    eps: float = 0.5  # For DBSCAN
    min_samples: int = 3  # For DBSCAN
    num_clusters: Optional[int] = None  # For K-means/hierarchical
    anomaly_threshold: float = 0.95  # For anomaly detection
    region_filter: Optional[str] = None


@router.get("/trends/symptoms")
async def get_symptom_trends(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("daily"),
    analyzer: TemporalTrendAnalyzer = Depends(get_trend_analyzer)
):
    """Get symptom trends over time"""
    try:
        granularity_enum = TrendGranularity(granularity)
        options = TrendOptions(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity_enum
        )
        
        trend_data = analyzer.analyze_symptom_trends(options)
        return trend_data.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/diagnoses")
async def get_diagnosis_trends(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("daily"),
    analyzer: TemporalTrendAnalyzer = Depends(get_trend_analyzer)
):
    """Get diagnosis trends over time"""
    try:
        granularity_enum = TrendGranularity(granularity)
        options = TrendOptions(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity_enum
        )
        
        trend_data = analyzer.analyze_diagnosis_trends(options)
        return trend_data.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/outcomes")
async def get_outcome_trends(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("daily"),
    analyzer: TemporalTrendAnalyzer = Depends(get_trend_analyzer)
):
    """Get treatment outcome trends over time"""
    try:
        granularity_enum = TrendGranularity(granularity)
        options = TrendOptions(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity_enum
        )
        
        trend_data = analyzer.analyze_outcome_trends(options)
        return trend_data.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends/all")
async def get_all_trends(
    request: TrendRequest,
    analyzer: TemporalTrendAnalyzer = Depends(get_trend_analyzer)
):
    """Get all trend analyses"""
    try:
        granularity_enum = TrendGranularity(request.granularity)
        options = TrendOptions(
            start_date=request.start_date,
            end_date=request.end_date,
            granularity=granularity_enum,
            filters=request.filters,
            metrics=request.metrics
        )
        
        trends = analyzer.generate_all_trends(options)
        return {
            metric: trend.to_dict()
            for metric, trend in trends.items()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outbreak/detect")
async def detect_outbreak_signals(
    request: OutbreakDetectionRequest,
    analyzer: TemporalTrendAnalyzer = Depends(get_trend_analyzer)
):
    """Detect potential outbreak signals (legacy method - uses surge-based detection)"""
    try:
        signals = analyzer.detect_outbreak_signals(
            symptom_keywords=request.symptom_keywords,
            time_window_days=request.time_window_days,
            threshold=request.threshold
        )
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outbreak/detect-advanced")
async def detect_outbreak_advanced(
    request: AdvancedOutbreakDetectionRequest,
    storage: QdrantStorage = Depends(get_qdrant_storage),
    retriever: CaseRetriever = Depends(get_case_retriever)
):
    """Advanced outbreak detection using clustering algorithms"""
    try:
        from src.outbreak import OutbreakDetector, DetectionMethod, OutbreakDetectionOptions
        
        detector = OutbreakDetector(
            qdrant_storage=storage,
            case_retriever=retriever
        )
        
        # Map method string to enum
        method_map = {
            "surge_based": DetectionMethod.SURGE_BASED,
            "dbscan": DetectionMethod.DBSCAN,
            "kmeans": DetectionMethod.KMEANS,
            "hierarchical": DetectionMethod.HIERARCHICAL,
            "anomaly_detection": DetectionMethod.ANOMALY_DETECTION,
            "spatial_temporal": DetectionMethod.SPATIAL_TEMPORAL
        }
        
        detection_method = method_map.get(request.method.lower(), DetectionMethod.DBSCAN)
        
        options = OutbreakDetectionOptions(
            method=detection_method,
            time_window_days=request.time_window_days,
            min_cluster_size=request.min_cluster_size,
            threshold=request.threshold,
            symptom_keywords=request.symptom_keywords,
            diagnosis_keywords=request.diagnosis_keywords,
            eps=request.eps,
            min_samples=request.min_samples,
            num_clusters=request.num_clusters,
            anomaly_threshold=request.anomaly_threshold,
            region_filter=request.region_filter
        )
        
        result = detector.detect_outbreaks(options)
        
        # Convert to dict for JSON response
        return {
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "level": alert.level.value,
                    "message": alert.message,
                    "confidence": alert.confidence,
                    "recommended_actions": alert.recommended_actions,
                    "cluster": {
                        "cluster_id": alert.cluster.cluster_id,
                        "size": alert.cluster.size,
                        "symptoms": alert.cluster.symptoms,
                        "diagnoses": alert.cluster.diagnoses
                    },
                    "detected_at": alert.detected_at.isoformat(),
                    "metadata": alert.metadata
                }
                for alert in result.alerts
            ],
            "clusters": [
                {
                    "cluster_id": cluster.cluster_id,
                    "size": cluster.size,
                    "symptoms": cluster.symptoms,
                    "diagnoses": cluster.diagnoses,
                    "density_score": cluster.density_score,
                    "anomaly_score": cluster.anomaly_score
                }
                for cluster in result.clusters
            ],
            "total_cases_analyzed": result.total_cases_analyzed,
            "anomaly_cases": result.anomaly_cases,
            "detection_method": result.detection_method,
            "detection_time": result.detection_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/case-map")
async def generate_case_map(
    request: CaseMapRequest,
    generator: CaseMapGenerator = Depends(get_case_map_generator)
):
    """Generate case map visualization data"""
    try:
        projection_enum = MapProjection(request.projection_method)
        options = MapOptions(
            projection_method=projection_enum,
            dimensions=request.dimensions,
            cluster_cases=request.cluster_cases,
            num_clusters=request.num_clusters
        )
        
        map_data = generator.generate_case_map(
            query_case_id=request.query_case_id,
            limit=request.limit,
            options=options
        )
        return map_data.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/case-map/similarity/{case_id}")
async def generate_similarity_map(
    case_id: str,
    limit: int = Query(50),
    generator: CaseMapGenerator = Depends(get_case_map_generator)
):
    """Generate similarity map centered around a case"""
    try:
        map_data = generator.generate_similarity_map(
            query_case_id=case_id,
            limit=limit
        )
        return map_data.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    analyzer: TemporalTrendAnalyzer = Depends(get_trend_analyzer),
    generator: CaseMapGenerator = Depends(get_case_map_generator)
):
    """Get dashboard summary data"""
    try:
        # Get recent trends (last 30 days)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        
        options = TrendOptions(
            start_date=start_date,
            end_date=end_date,
            granularity=TrendGranularity.DAILY
        )
        
        # Get all trends
        trends = analyzer.generate_all_trends(options)
        
        # Get case map overview
        map_options = MapOptions(
            projection_method=MapProjection.SIMPLE_2D,
            dimensions=2,
            cluster_cases=True,
            limit=100
        )
        case_map = generator.generate_case_map(
            limit=100,
            options=map_options
        )
        
        return {
            "trends": {
                metric: trend.to_dict()
                for metric, trend in trends.items()
            },
            "case_map": case_map.to_dict(),
            "summary": {
                "total_cases": case_map.metadata.get("total_cases", 0),
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

