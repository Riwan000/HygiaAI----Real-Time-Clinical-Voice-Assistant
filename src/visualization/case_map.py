"""
Case Map Visualization

Generates data for visualizing similar cases in 2D/3D space:
- UMAP-based dimensionality reduction
- Clustering visualization
- Similarity-based case mapping
- Interactive case exploration
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum

import numpy as np

from src.retrieval import CaseRetriever, RetrievalResult
from src.storage import QdrantStorage

logger = logging.getLogger(__name__)

# Optional UMAP for dimensionality reduction
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logger.warning("UMAP library not available. Install with: pip install umap-learn")


class MapProjection(Enum):
    """Map projection methods"""
    UMAP = "umap"
    PCA = "pca"
    TSNE = "tsne"
    SIMPLE_2D = "simple_2d"  # Simple 2D projection without external libraries


@dataclass
class CaseMapPoint:
    """Single point in case map"""
    case_id: str
    x: float
    y: float
    z: Optional[float] = None
    similarity_score: Optional[float] = None
    cluster_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "case_id": self.case_id,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "similarity_score": self.similarity_score,
            "cluster_id": self.cluster_id,
            "metadata": self.metadata
        }


@dataclass
class CaseMapData:
    """Complete case map data for visualization"""
    points: List[CaseMapPoint] = field(default_factory=list)
    clusters: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    projection_method: str = "simple_2d"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "points": [p.to_dict() for p in self.points],
            "clusters": self.clusters,
            "metadata": self.metadata,
            "projection_method": self.projection_method
        }


@dataclass
class MapOptions:
    """Options for case map generation"""
    projection_method: MapProjection = MapProjection.SIMPLE_2D
    dimensions: int = 2  # 2D or 3D
    cluster_cases: bool = True
    num_clusters: Optional[int] = None  # Auto-detect if None
    include_metadata: bool = True
    similarity_threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "projection_method": self.projection_method.value,
            "dimensions": self.dimensions,
            "cluster_cases": self.cluster_cases,
            "num_clusters": self.num_clusters,
            "include_metadata": self.include_metadata,
            "similarity_threshold": self.similarity_threshold
        }


class CaseMapGenerator:
    """
    Generates case map visualization data
    
    Features:
    - 2D/3D case mapping using dimensionality reduction
    - Clustering of similar cases
    - Interactive case exploration
    - Similarity-based visualization
    """
    
    def __init__(
        self,
        qdrant_storage: QdrantStorage,
        case_retriever: Optional[CaseRetriever] = None
    ):
        """
        Initialize case map generator
        
        Args:
            qdrant_storage: QdrantStorage instance
            case_retriever: Optional CaseRetriever for advanced queries
        """
        self.storage = qdrant_storage
        self.case_retriever = case_retriever
        
        logger.info("Case map generator initialized")
    
    def generate_case_map(
        self,
        query_case_id: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        limit: int = 100,
        options: Optional[MapOptions] = None
    ) -> CaseMapData:
        """
        Generate case map visualization data
        
        Args:
            query_case_id: Optional query case ID to center map around
            query_embedding: Optional query embedding
            limit: Maximum number of cases to include
            options: Optional map generation options
            
        Returns:
            CaseMapData with points and clusters
        """
        options = options or MapOptions()
        
        # Retrieve cases
        if query_case_id or query_embedding:
            # Retrieve similar cases
            if self.case_retriever and query_embedding:
                results = self.case_retriever.retrieve_similar_cases(
                    query_embedding=query_embedding,
                    options=None  # Use default options
                )
            else:
                # Use storage directly
                if query_embedding:
                    results = self.storage.search_similar(
                        query_embedding=query_embedding,
                        limit=limit
                    )
                else:
                    # Get all cases (limited)
                    dummy_embedding = [0.0] * self.storage.vector_size
                    results = self.storage.search_with_filters(
                        query_embedding=dummy_embedding,
                        filters=None,
                        limit=limit
                    )
        else:
            # Get all cases directly from Qdrant
            try:
                # Use scroll to get all points with vectors
                scroll_result = self.storage.client.scroll(
                    collection_name=self.storage.collection_name,
                    limit=limit,
                    with_payload=True,
                    with_vectors=True
                )
                results = []
                for point in scroll_result[0]:  # scroll_result is (points, next_page_offset)
                    results.append({
                        "id": point.id,
                        "score": 1.0,  # No similarity score for scroll
                        "payload": point.payload,
                        "vector": point.vector
                    })
            except Exception as e:
                logger.warning(f"Could not scroll collection: {e}, falling back to search")
                # Fallback to search
                dummy_embedding = [0.0] * self.storage.vector_size
                results = self.storage.search_with_filters(
                    query_embedding=dummy_embedding,
                    filters=None,
                    limit=limit
                )
        
        # Extract embeddings and metadata
        embeddings = []
        case_metadata = []
        case_ids = []
        
        for result in results:
            if isinstance(result, dict):
                # Raw Qdrant result
                payload = result.get("payload", {})
                case_id = result.get("id", "")
                embedding = result.get("vector")
                
                # If vector not in result, retrieve it separately
                if not embedding and case_id:
                    try:
                        point = self.storage.client.retrieve(
                            collection_name=self.storage.collection_name,
                            ids=[case_id]
                        )
                        if point and len(point) > 0:
                            embedding = point[0].vector
                    except Exception as e:
                        logger.warning(f"Could not retrieve vector for case {case_id}: {e}")
                
                if embedding:
                    embeddings.append(embedding)
                    case_metadata.append({
                        "case_id": case_id,
                        "score": result.get("score", 0.0),
                        "metadata": payload
                    })
                    case_ids.append(case_id)
            else:
                # RetrievalResult object
                # Note: RetrievalResult doesn't store embeddings directly
                # We'd need to retrieve them separately or store them
                pass
        
        if not embeddings:
            logger.warning("No embeddings found for case map generation")
            return CaseMapData(projection_method=options.projection_method.value)
        
        # Project to 2D/3D
        projected_points = self._project_embeddings(
            embeddings=embeddings,
            dimensions=options.dimensions,
            method=options.projection_method
        )
        
        # Generate map points
        points = []
        for i, (coords, metadata) in enumerate(zip(projected_points, case_metadata)):
            point = CaseMapPoint(
                case_id=metadata["case_id"],
                x=coords[0],
                y=coords[1],
                z=coords[2] if len(coords) > 2 else None,
                similarity_score=metadata.get("score"),
                metadata=metadata.get("metadata", {}) if options.include_metadata else {}
            )
            points.append(point)
        
        # Cluster cases if requested
        clusters = {}
        cluster_assignments = {}
        if options.cluster_cases:
            clusters, cluster_assignments = self._cluster_cases(
                points=points,
                embeddings=embeddings,
                num_clusters=options.num_clusters
            )
            # Assign cluster IDs to points
            for i, point in enumerate(points):
                point.cluster_id = cluster_assignments.get(i)
        
        return CaseMapData(
            points=points,
            clusters=clusters,
            metadata={
                "total_cases": len(points),
                "query_case_id": query_case_id,
                "dimensions": options.dimensions
            },
            projection_method=options.projection_method.value
        )
    
    def _project_embeddings(
        self,
        embeddings: List[List[float]],
        dimensions: int,
        method: MapProjection
    ) -> List[List[float]]:
        """Project embeddings to lower dimensions"""
        embeddings_array = np.array(embeddings)
        
        if method == MapProjection.UMAP:
            if UMAP_AVAILABLE:
                reducer = umap.UMAP(n_components=dimensions, random_state=42)
                projected = reducer.fit_transform(embeddings_array)
                return projected.tolist()
            else:
                logger.warning("UMAP not available, falling back to simple 2D projection")
                return self._simple_2d_projection(embeddings_array, dimensions)
        
        elif method == MapProjection.PCA:
            # Simple PCA implementation
            return self._pca_projection(embeddings_array, dimensions)
        
        elif method == MapProjection.TSNE:
            # Would require scikit-learn
            logger.warning("t-SNE not implemented, falling back to simple 2D projection")
            return self._simple_2d_projection(embeddings_array, dimensions)
        
        else:  # SIMPLE_2D
            return self._simple_2d_projection(embeddings_array, dimensions)
    
    def _simple_2d_projection(
        self,
        embeddings_array: np.ndarray,
        dimensions: int
    ) -> List[List[float]]:
        """Simple 2D/3D projection using first few principal components"""
        # Use first N dimensions as projection
        if dimensions == 2:
            projected = embeddings_array[:, :2]
        elif dimensions == 3:
            projected = embeddings_array[:, :3]
        else:
            projected = embeddings_array[:, :dimensions]
        
        # Normalize to [-1, 1] range
        for i in range(projected.shape[1]):
            col = projected[:, i]
            col_min, col_max = col.min(), col.max()
            if col_max > col_min:
                projected[:, i] = 2 * (col - col_min) / (col_max - col_min) - 1
        
        return projected.tolist()
    
    def _pca_projection(
        self,
        embeddings_array: np.ndarray,
        dimensions: int
    ) -> List[List[float]]:
        """Simple PCA projection"""
        # Center the data
        mean = embeddings_array.mean(axis=0)
        centered = embeddings_array - mean
        
        # Compute covariance matrix
        cov = np.cov(centered.T)
        
        # Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        
        # Sort by eigenvalue (descending)
        idx = eigenvalues.argsort()[::-1]
        eigenvectors = eigenvectors[:, idx]
        
        # Project to lower dimensions
        projected = centered @ eigenvectors[:, :dimensions]
        
        # Normalize to [-1, 1] range
        for i in range(projected.shape[1]):
            col = projected[:, i]
            col_min, col_max = col.min(), col.max()
            if col_max > col_min:
                projected[:, i] = 2 * (col - col_min) / (col_max - col_min) - 1
        
        return projected.tolist()
    
    def _cluster_cases(
        self,
        points: List[CaseMapPoint],
        embeddings: List[List[float]],
        num_clusters: Optional[int] = None
    ) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, int]]:
        """Cluster cases using K-means (simple implementation)"""
        if not embeddings:
            return {}, {}
        
        # Simple K-means clustering
        embeddings_array = np.array(embeddings)
        
        # Auto-determine number of clusters if not specified
        if num_clusters is None:
            num_clusters = min(10, max(2, len(points) // 10))
        
        # Initialize centroids randomly
        centroids = embeddings_array[np.random.choice(len(embeddings_array), num_clusters, replace=False)]
        
        # Simple K-means iteration
        for _ in range(10):  # Max iterations
            # Assign points to nearest centroid
            distances = np.sqrt(((embeddings_array[:, np.newaxis] - centroids) ** 2).sum(axis=2))
            assignments = distances.argmin(axis=1)
            
            # Update centroids
            new_centroids = np.array([
                embeddings_array[assignments == i].mean(axis=0)
                for i in range(num_clusters)
            ])
            
            # Check convergence
            if np.allclose(centroids, new_centroids):
                break
            
            centroids = new_centroids
        
        # Build cluster dictionary and assignments
        clusters = {}
        cluster_assignments = {}
        for i, point in enumerate(points):
            cluster_id = int(assignments[i])
            cluster_assignments[i] = cluster_id
            
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    "cluster_id": cluster_id,
                    "case_ids": [],
                    "size": 0,
                    "centroid": centroids[cluster_id].tolist()
                }
            clusters[cluster_id]["case_ids"].append(point.case_id)
            clusters[cluster_id]["size"] += 1
        
        return clusters, cluster_assignments
    
    def generate_similarity_map(
        self,
        query_case_id: str,
        limit: int = 50
    ) -> CaseMapData:
        """
        Generate similarity map centered around a query case
        
        Args:
            query_case_id: Query case ID
            limit: Maximum number of similar cases
            
        Returns:
            CaseMapData with query case at center
        """
        # Retrieve query case embedding
        # This would require fetching the case from Qdrant
        # For now, use a simplified approach
        
        if self.case_retriever:
            # Use retriever to find similar cases
            results = self.case_retriever.retrieve_similar_cases(
                query_text="",  # Empty query, will use filters
                options=None
            )
        else:
            # Fallback: get all cases
            dummy_embedding = [0.0] * self.storage.vector_size
            results = self.storage.search_with_filters(
                query_embedding=dummy_embedding,
                filters=None,
                limit=limit
            )
        
        # Generate map with query case highlighted
        options = MapOptions(
            projection_method=MapProjection.SIMPLE_2D,
            dimensions=2,
            cluster_cases=True
        )
        
        map_data = self.generate_case_map(
            query_case_id=query_case_id,
            limit=limit,
            options=options
        )
        
        # Mark query case in metadata
        map_data.metadata["query_case_id"] = query_case_id
        map_data.metadata["query_case_highlighted"] = True
        
        return map_data

