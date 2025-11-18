"""
Embedding Generation Module

Handles:
- Text embeddings using BioBERT
- Image embeddings using CLIP
- Audio embeddings using AudioCLIP (wav2vec2)
- Multi-modal embedding fusion
- Embedding quality validation
"""

# Lazy imports to avoid blocking startup if transformers/torch have version issues
# These will be imported on-demand when actually used

def __getattr__(name):
    """Lazy import for embedding generators"""
    if name == "TextEmbeddingGenerator":
        from .text_embeddings import TextEmbeddingGenerator
        return TextEmbeddingGenerator
    if name == "BioBERTEmbeddingGenerator":
        from .text_embeddings import BioBERTEmbeddingGenerator
        return BioBERTEmbeddingGenerator
    if name == "ImageEmbeddingGenerator":
        from .image_embeddings import ImageEmbeddingGenerator
        return ImageEmbeddingGenerator
    if name == "CLIPEmbeddingGenerator":
        from .image_embeddings import CLIPEmbeddingGenerator
        return CLIPEmbeddingGenerator
    if name == "AudioEmbeddingGenerator":
        from .audio_embeddings import AudioEmbeddingGenerator
        return AudioEmbeddingGenerator
    if name == "AudioCLIPEmbeddingGenerator":
        from .audio_embeddings import AudioCLIPEmbeddingGenerator
        return AudioCLIPEmbeddingGenerator
    if name == "MultimodalEmbeddingGenerator":
        from .multimodal_embeddings import MultimodalEmbeddingGenerator
        return MultimodalEmbeddingGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "TextEmbeddingGenerator",
    "BioBERTEmbeddingGenerator",
    "ImageEmbeddingGenerator",
    "CLIPEmbeddingGenerator",
    "AudioEmbeddingGenerator",
    "AudioCLIPEmbeddingGenerator",
    "MultimodalEmbeddingGenerator",
]

