"""
Multi-Modal Embedding Generation Module

Handles combining text and image embeddings into unified multi-modal representations.
"""

import logging
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
import numpy as np

from .text_embeddings import TextEmbeddingGenerator, BioBERTEmbeddingGenerator
from .image_embeddings import ImageEmbeddingGenerator, CLIPEmbeddingGenerator

logger = logging.getLogger(__name__)


class MultimodalEmbeddingGenerator:
    """
    Multi-modal embedding generator
    
    Combines text and image embeddings into unified representations
    for storage in Qdrant.
    """
    
    def __init__(
        self,
        text_model_name: str = "dmis-lab/biobert-base-cased-v1.2",
        image_model_name: str = "openai/clip-vit-base-patch32",
        fusion_method: str = "concatenate"
    ):
        """
        Initialize multi-modal embedding generator
        
        Args:
            text_model_name: BioBERT model name for text embeddings
            image_model_name: CLIP model name for image embeddings
            fusion_method: Method to fuse embeddings ("concatenate", "average", "weighted")
        """
        self.text_generator = BioBERTEmbeddingGenerator(model_name=text_model_name)
        self.image_generator = CLIPEmbeddingGenerator(model_name=image_model_name)
        self.fusion_method = fusion_method
        logger.info(f"Multi-modal embedding generator initialized (fusion: {fusion_method})")
    
    def generate_text_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding
        
        Args:
            text: Input text
            
        Returns:
            Text embedding vector
        """
        return self.text_generator.generate_embedding(text)
    
    def generate_image_embedding(self, image_path: Union[str, Path]) -> List[float]:
        """
        Generate image embedding
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image embedding vector
        """
        return self.image_generator.generate_embedding(image_path)
    
    def generate_multimodal_embedding(
        self,
        text: Optional[str] = None,
        image_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Generate multi-modal embedding from text and/or image
        
        Args:
            text: Optional text input
            image_path: Optional image file path
            
        Returns:
            Dictionary containing:
            - "text_embedding": Text embedding (if text provided)
            - "image_embedding": Image embedding (if image provided)
            - "multimodal_embedding": Fused embedding
            - "modalities": List of available modalities
        """
        result = {
            "text_embedding": None,
            "image_embedding": None,
            "multimodal_embedding": None,
            "modalities": []
        }
        
        embeddings = []
        
        # Generate text embedding
        if text:
            text_emb = self.generate_text_embedding(text)
            result["text_embedding"] = text_emb
            result["modalities"].append("text")
            embeddings.append(("text", text_emb))
        
        # Generate image embedding
        if image_path:
            image_emb = self.generate_image_embedding(image_path)
            result["image_embedding"] = image_emb
            result["modalities"].append("image")
            embeddings.append(("image", image_emb))
        
        # Fuse embeddings
        if len(embeddings) == 0:
            logger.warning("No embeddings to fuse")
            return result
        elif len(embeddings) == 1:
            # Single modality - return as-is
            result["multimodal_embedding"] = embeddings[0][1]
        else:
            # Multiple modalities - fuse them
            result["multimodal_embedding"] = self._fuse_embeddings([emb[1] for emb in embeddings])
        
        return result
    
    def _fuse_embeddings(self, embeddings: List[List[float]]) -> List[float]:
        """
        Fuse multiple embeddings into a single vector
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            Fused embedding vector
        """
        if self.fusion_method == "concatenate":
            # Simple concatenation
            fused = []
            for emb in embeddings:
                fused.extend(emb)
            return fused
        elif self.fusion_method == "average":
            # Average pooling (requires same dimension)
            if len(set(len(emb) for emb in embeddings)) != 1:
                logger.warning("Embeddings have different dimensions, using concatenation instead")
                return self._fuse_embeddings(embeddings)  # Fallback to concatenation
            
            # Average
            fused = np.mean(embeddings, axis=0).tolist()
            return fused
        elif self.fusion_method == "weighted":
            # Weighted average (text: 0.6, image: 0.4)
            if len(embeddings) != 2:
                logger.warning("Weighted fusion requires exactly 2 embeddings, using average instead")
                return self._fuse_embeddings(embeddings)  # Fallback to average
            
            if len(set(len(emb) for emb in embeddings)) != 1:
                logger.warning("Embeddings have different dimensions, using concatenation instead")
                return self._fuse_embeddings(embeddings)  # Fallback to concatenation
            
            # Weighted average
            weights = [0.6, 0.4]  # Text, Image
            fused = np.average(embeddings, axis=0, weights=weights).tolist()
            return fused
        else:
            # Default to concatenation
            logger.warning(f"Unknown fusion method: {self.fusion_method}, using concatenation")
            fused = []
            for emb in embeddings:
                fused.extend(emb)
            return fused
    
    def get_embedding_dimension(self, modality: Optional[str] = None) -> int:
        """
        Get the dimension of embeddings
        
        Args:
            modality: Optional modality ("text", "image", or None for multimodal)
            
        Returns:
            Embedding dimension
        """
        if modality == "text":
            return self.text_generator.get_embedding_dimension()
        elif modality == "image":
            return self.image_generator.get_embedding_dimension()
        else:
            # Multi-modal dimension (concatenated)
            text_dim = self.text_generator.get_embedding_dimension()
            image_dim = self.image_generator.get_embedding_dimension()
            if self.fusion_method == "concatenate":
                return text_dim + image_dim
            else:
                # For average/weighted, use the dimension of individual embeddings
                return max(text_dim, image_dim)

