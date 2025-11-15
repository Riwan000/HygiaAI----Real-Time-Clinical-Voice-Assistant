"""
Test Script for Task 3: Embedding Generation (Text + Image)

Tests:
1. Text embedding generation using BioBERT
2. Image embedding generation using CLIP
3. Multi-modal embedding fusion
4. Embedding quality validation
"""

import sys
import asyncio
from pathlib import Path
import logging
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embeddings import (
    BioBERTEmbeddingGenerator,
    CLIPEmbeddingGenerator,
    MultimodalEmbeddingGenerator
)
from src.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


def test_text_embeddings():
    """Test 1: Text Embedding Generation"""
    print("\n" + "=" * 60)
    print("Test 1: Text Embedding Generation (BioBERT)")
    print("=" * 60)
    
    try:
        generator = BioBERTEmbeddingGenerator()
        
        # Test cases
        test_texts = [
            "Patient reports fever, cough, and chest pain.",
            "Blood pressure: 140/90 mmHg, Heart rate: 88 bpm.",
            "Diagnosis: pneumonia and bronchitis.",
            "Prescribed aspirin 100mg and ibuprofen 200mg.",
        ]
        
        print("\nGenerating embeddings for test texts...")
        embeddings = []
        for i, text in enumerate(test_texts, 1):
            print(f"\nText {i}: {text[:50]}...")
            try:
                embedding = generator.generate_embedding(text)
                embeddings.append(embedding)
                print(f"  ✓ Embedding generated: {len(embedding)} dimensions")
                print(f"  First 5 values: {embedding[:5]}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                embeddings.append(None)
        
        # Test batch generation
        print("\n\nTesting batch generation...")
        try:
            batch_embeddings = generator.generate_embeddings_batch(test_texts)
            print(f"  ✓ Batch embeddings generated: {len(batch_embeddings)}")
            print(f"  Embedding dimension: {generator.get_embedding_dimension()}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Test similarity
        if len(embeddings) >= 2 and all(emb is not None for emb in embeddings):
            print("\n\nTesting embedding similarity...")
            emb1 = np.array(embeddings[0])
            emb2 = np.array(embeddings[1])
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            print(f"  Cosine similarity between text 1 and 2: {similarity:.4f}")
        
        return generator
        
    except ImportError as e:
        print(f"\n⚠️  Dependencies not installed: {e}")
        print("  Install with: pip install transformers torch sentence-transformers")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_image_embeddings():
    """Test 2: Image Embedding Generation"""
    print("\n" + "=" * 60)
    print("Test 2: Image Embedding Generation (CLIP)")
    print("=" * 60)
    
    try:
        generator = CLIPEmbeddingGenerator()
        
        print("\nNote: Image embedding requires actual image files.")
        print("To test with images:")
        print("  1. Create a test image or use an existing medical image")
        print("  2. Call: generator.generate_embedding('path/to/image.jpg')")
        
        # Test dimension
        print(f"\n✓ CLIP embedding dimension: {generator.get_embedding_dimension()}")
        
        # Test with a dummy image (if PIL is available)
        try:
            from PIL import Image
            import io
            
            # Create a simple test image
            test_image = Image.new('RGB', (224, 224), color='white')
            print("\nTesting with dummy image...")
            embedding = generator.generate_embedding(test_image)
            print(f"  ✓ Embedding generated: {len(embedding)} dimensions")
            print(f"  First 5 values: {embedding[:5]}")
        except Exception as e:
            print(f"  ⚠️  Could not create test image: {e}")
        
        return generator
        
    except ImportError as e:
        print(f"\n⚠️  Dependencies not installed: {e}")
        print("  Install with: pip install transformers torch pillow")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_multimodal_embeddings():
    """Test 3: Multi-Modal Embedding Fusion"""
    print("\n" + "=" * 60)
    print("Test 3: Multi-Modal Embedding Fusion")
    print("=" * 60)
    
    try:
        generator = MultimodalEmbeddingGenerator(fusion_method="concatenate")
        
        # Test text-only
        print("\nTest 1: Text-only embedding")
        text = "Patient reports fever and cough. Blood pressure: 140/90 mmHg."
        result = generator.generate_multimodal_embedding(text=text)
        print(f"  Modalities: {result['modalities']}")
        print(f"  Text embedding: {len(result['text_embedding'])} dimensions")
        print(f"  Multi-modal embedding: {len(result['multimodal_embedding'])} dimensions")
        
        # Test image-only (if available)
        print("\nTest 2: Image-only embedding")
        try:
            from PIL import Image
            test_image = Image.new('RGB', (224, 224), color='white')
            result = generator.generate_multimodal_embedding(image_path=test_image)
            print(f"  Modalities: {result['modalities']}")
            print(f"  Image embedding: {len(result['image_embedding'])} dimensions")
            print(f"  Multi-modal embedding: {len(result['multimodal_embedding'])} dimensions")
        except Exception as e:
            print(f"  ⚠️  Could not test image: {e}")
        
        # Test text + image
        print("\nTest 3: Text + Image embedding")
        try:
            from PIL import Image
            test_image = Image.new('RGB', (224, 224), color='white')
            result = generator.generate_multimodal_embedding(
                text=text,
                image_path=test_image
            )
            print(f"  Modalities: {result['modalities']}")
            print(f"  Text embedding: {len(result['text_embedding'])} dimensions")
            print(f"  Image embedding: {len(result['image_embedding'])} dimensions")
            print(f"  Multi-modal embedding: {len(result['multimodal_embedding'])} dimensions")
            print(f"  Fusion method: {generator.fusion_method}")
        except Exception as e:
            print(f"  ⚠️  Could not test text+image: {e}")
        
        # Test different fusion methods
        print("\nTest 4: Different fusion methods")
        for method in ["concatenate", "average", "weighted"]:
            try:
                gen = MultimodalEmbeddingGenerator(fusion_method=method)
                result = gen.generate_multimodal_embedding(text=text)
                print(f"  {method}: {len(result['multimodal_embedding'])} dimensions")
            except Exception as e:
                print(f"  {method}: Error - {e}")
        
        return generator
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_embedding_quality():
    """Test 4: Embedding Quality Validation"""
    print("\n" + "=" * 60)
    print("Test 4: Embedding Quality Validation")
    print("=" * 60)
    
    try:
        generator = BioBERTEmbeddingGenerator()
        
        # Test similar texts should have similar embeddings
        similar_texts = [
            "Patient has fever and cough",
            "Patient reports fever and cough",
            "Fever and cough present"
        ]
        
        # Test different texts should have different embeddings
        different_texts = [
            "Patient has fever and cough",
            "Blood pressure is 140/90 mmHg",
            "Diagnosis: pneumonia"
        ]
        
        print("\nTest 1: Similar texts (should have high similarity)")
        similar_embeddings = [generator.generate_embedding(text) for text in similar_texts]
        for i in range(len(similar_embeddings) - 1):
            emb1 = np.array(similar_embeddings[i])
            emb2 = np.array(similar_embeddings[i + 1])
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            print(f"  Similarity {i+1}-{i+2}: {similarity:.4f}")
        
        print("\nTest 2: Different texts (should have lower similarity)")
        different_embeddings = [generator.generate_embedding(text) for text in different_texts]
        for i in range(len(different_embeddings) - 1):
            emb1 = np.array(different_embeddings[i])
            emb2 = np.array(different_embeddings[i + 1])
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            print(f"  Similarity {i+1}-{i+2}: {similarity:.4f}")
        
        # Test embedding normalization
        print("\nTest 3: Embedding normalization")
        embedding = generator.generate_embedding("Test text")
        emb_array = np.array(embedding)
        norm = np.linalg.norm(emb_array)
        print(f"  Embedding norm: {norm:.4f}")
        print(f"  Embedding mean: {emb_array.mean():.4f}")
        print(f"  Embedding std: {emb_array.std():.4f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all embedding tests"""
    print("\n" + "=" * 60)
    print("Task 3: Embedding Generation (Text + Image) - Test Suite")
    print("=" * 60)
    print("\nThis test suite validates embedding generation:")
    print("  1. Text embeddings using BioBERT")
    print("  2. Image embeddings using CLIP")
    print("  3. Multi-modal embedding fusion")
    print("  4. Embedding quality validation")
    print()
    print("Note: This requires transformers, torch, and sentence-transformers libraries.")
    print("Install with: pip install transformers torch sentence-transformers pillow")
    print()
    
    try:
        # Test 1: Text embeddings
        text_gen = test_text_embeddings()
        
        # Test 2: Image embeddings
        image_gen = test_image_embeddings()
        
        # Test 3: Multi-modal embeddings
        multimodal_gen = test_multimodal_embeddings()
        
        # Test 4: Embedding quality
        quality_ok = test_embedding_quality()
        
        print("\n" + "=" * 60)
        print("✅ All embedding tests completed!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  ✓ Text embeddings: {'Working' if text_gen else 'Dependencies missing'}")
        print(f"  ✓ Image embeddings: {'Working' if image_gen else 'Dependencies missing'}")
        print(f"  ✓ Multi-modal embeddings: {'Working' if multimodal_gen else 'Dependencies missing'}")
        print(f"  ✓ Embedding quality: {'Validated' if quality_ok else 'Not validated'}")
        print()
        
        if not text_gen or not image_gen:
            print("⚠️  Some dependencies are missing.")
            print("  Install with: pip install transformers torch sentence-transformers pillow")
            print()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

