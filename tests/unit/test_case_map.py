"""
Unit tests for Case Map Visualization Module

Tests:
- Case map generation
- Embedding projection
- Clustering
- Similarity mapping
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.visualization.case_map import (
    CaseMapGenerator,
    CaseMapData,
    CaseMapPoint,
    MapOptions,
    MapProjection
)
from src.storage import QdrantStorage
from src.retrieval import CaseRetriever


class TestMapOptions:
    """Test MapOptions dataclass"""
    
    def test_default_options(self):
        """Test default map options"""
        options = MapOptions()
        
        assert options.projection_method == MapProjection.SIMPLE_2D
        assert options.dimensions == 2
        assert options.cluster_cases is True
        assert options.num_clusters is None
        assert options.include_metadata is True
        assert options.similarity_threshold == 0.7
    
    def test_custom_options(self):
        """Test custom map options"""
        options = MapOptions(
            projection_method=MapProjection.PCA,
            dimensions=3,
            cluster_cases=False,
            num_clusters=5,
            include_metadata=False,
            similarity_threshold=0.8
        )
        
        assert options.projection_method == MapProjection.PCA
        assert options.dimensions == 3
        assert options.cluster_cases is False
        assert options.num_clusters == 5
        assert options.include_metadata is False
        assert options.similarity_threshold == 0.8


class TestCaseMapGenerator:
    """Test CaseMapGenerator class"""
    
    @patch('src.visualization.case_map.QdrantStorage')
    def test_initialization(self, mock_storage_class):
        """Test case map generator initialization"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        generator = CaseMapGenerator(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        assert generator.storage == mock_storage
        assert generator.case_retriever is None
    
    @patch('src.visualization.case_map.QdrantStorage')
    def test_simple_2d_projection(self, mock_storage_class):
        """Test simple 2D projection"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        generator = CaseMapGenerator(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        # Create test embeddings
        embeddings = [
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0],
            [3.0, 4.0, 5.0, 6.0]
        ]
        embeddings_array = np.array(embeddings)
        
        projected = generator._simple_2d_projection(embeddings_array, dimensions=2)
        
        assert len(projected) == 3
        assert len(projected[0]) == 2
        # Check normalization (values should be in [-1, 1] range)
        assert all(-1 <= coord <= 1 for point in projected for coord in point)
    
    @patch('src.visualization.case_map.QdrantStorage')
    def test_pca_projection(self, mock_storage_class):
        """Test PCA projection"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        generator = CaseMapGenerator(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        # Create test embeddings
        embeddings = [
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0],
            [3.0, 4.0, 5.0, 6.0]
        ]
        embeddings_array = np.array(embeddings)
        
        projected = generator._pca_projection(embeddings_array, dimensions=2)
        
        assert len(projected) == 3
        assert len(projected[0]) == 2
        # Check normalization (values should be in [-1, 1] range)
        assert all(-1 <= coord <= 1 for point in projected for coord in point)
    
    @patch('src.visualization.case_map.QdrantStorage')
    def test_cluster_cases(self, mock_storage_class):
        """Test case clustering"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        generator = CaseMapGenerator(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        # Create test points and embeddings
        points = [
            CaseMapPoint(case_id=f"case-{i}", x=0.0, y=0.0)
            for i in range(10)
        ]
        
        # Create embeddings with clear clusters
        embeddings = []
        for i in range(10):
            if i < 5:
                # First cluster
                embeddings.append([1.0 + i*0.1, 1.0 + i*0.1, 0.0, 0.0])
            else:
                # Second cluster
                embeddings.append([-1.0 - (i-5)*0.1, -1.0 - (i-5)*0.1, 0.0, 0.0])
        
        clusters, assignments = generator._cluster_cases(
            points=points,
            embeddings=embeddings,
            num_clusters=2
        )
        
        assert len(clusters) == 2
        assert len(assignments) == 10
        # Check that points are assigned to clusters
        assert all(assignments[i] in [0, 1] for i in range(10))
    
    @patch('src.visualization.case_map.QdrantStorage')
    def test_generate_case_map(self, mock_storage_class):
        """Test case map generation"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        # Mock search results
        mock_storage.search_with_filters.return_value = [
            {
                "id": f"case-{i}",
                "vector": [0.1 * i] * 384,
                "score": 0.9 - i * 0.1,
                "payload": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "diagnosis": "pneumonia"
                }
            }
            for i in range(5)
        ]
        
        generator = CaseMapGenerator(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        options = MapOptions(
            projection_method=MapProjection.SIMPLE_2D,
            dimensions=2,
            cluster_cases=False
        )
        
        map_data = generator.generate_case_map(
            limit=5,
            options=options
        )
        
        assert len(map_data.points) == 5
        assert map_data.projection_method == "simple_2d"
        assert all(point.x is not None and point.y is not None for point in map_data.points)
    
    @patch('src.visualization.case_map.QdrantStorage')
    def test_generate_case_map_with_clustering(self, mock_storage_class):
        """Test case map generation with clustering"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_storage.vector_size = 384
        
        # Mock search results
        mock_storage.search_with_filters.return_value = [
            {
                "id": f"case-{i}",
                "vector": [0.1 * i] * 384,
                "score": 0.9 - i * 0.1,
                "payload": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "diagnosis": "pneumonia"
                }
            }
            for i in range(10)
        ]
        
        generator = CaseMapGenerator(
            qdrant_storage=mock_storage,
            case_retriever=None
        )
        
        options = MapOptions(
            projection_method=MapProjection.SIMPLE_2D,
            dimensions=2,
            cluster_cases=True,
            num_clusters=2
        )
        
        map_data = generator.generate_case_map(
            limit=10,
            options=options
        )
        
        assert len(map_data.points) == 10
        assert len(map_data.clusters) > 0
        # Check that points have cluster IDs
        assert all(point.cluster_id is not None for point in map_data.points)


class TestCaseMapData:
    """Test CaseMapData dataclass"""
    
    def test_to_dict(self):
        """Test converting case map data to dictionary"""
        point = CaseMapPoint(
            case_id="case-1",
            x=0.5,
            y=0.3,
            z=0.1,
            similarity_score=0.9,
            cluster_id=0,
            metadata={"diagnosis": "pneumonia"}
        )
        
        map_data = CaseMapData(
            points=[point],
            clusters={0: {"cluster_id": 0, "size": 1}},
            metadata={"total_cases": 1},
            projection_method="simple_2d"
        )
        
        map_dict = map_data.to_dict()
        
        assert len(map_dict["points"]) == 1
        assert map_dict["points"][0]["case_id"] == "case-1"
        assert map_dict["points"][0]["x"] == 0.5
        assert map_dict["points"][0]["y"] == 0.3
        assert map_dict["points"][0]["z"] == 0.1
        assert map_dict["points"][0]["similarity_score"] == 0.9
        assert map_dict["points"][0]["cluster_id"] == 0
        assert len(map_dict["clusters"]) == 1
        assert map_dict["projection_method"] == "simple_2d"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

