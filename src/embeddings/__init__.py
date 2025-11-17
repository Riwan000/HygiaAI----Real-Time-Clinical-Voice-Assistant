"""
Embedding Generation Module

Handles:
- Text embeddings using BioBERT
- Image embeddings using CLIP
- Audio embeddings using AudioCLIP (wav2vec2)
- Multi-modal embedding fusion
- Embedding quality validation
"""

from .text_embeddings import TextEmbeddingGenerator, BioBERTEmbeddingGenerator
from .image_embeddings import ImageEmbeddingGenerator, CLIPEmbeddingGenerator
from .audio_embeddings import AudioEmbeddingGenerator, AudioCLIPEmbeddingGenerator
from .multimodal_embeddings import MultimodalEmbeddingGenerator

__all__ = [
    "TextEmbeddingGenerator",
    "BioBERTEmbeddingGenerator",
    "ImageEmbeddingGenerator",
    "CLIPEmbeddingGenerator",
    "AudioEmbeddingGenerator",
    "AudioCLIPEmbeddingGenerator",
    "MultimodalEmbeddingGenerator",
]

