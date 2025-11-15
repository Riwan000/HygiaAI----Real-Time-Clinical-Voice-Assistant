"""
Embedding Generation Module

Handles:
- Text embeddings using BioBERT
- Image embeddings using CLIP
- Multi-modal embedding fusion
- Embedding quality validation
"""

from .text_embeddings import TextEmbeddingGenerator, BioBERTEmbeddingGenerator
from .image_embeddings import ImageEmbeddingGenerator, CLIPEmbeddingGenerator
from .multimodal_embeddings import MultimodalEmbeddingGenerator

__all__ = [
    "TextEmbeddingGenerator",
    "BioBERTEmbeddingGenerator",
    "ImageEmbeddingGenerator",
    "CLIPEmbeddingGenerator",
    "MultimodalEmbeddingGenerator",
]

