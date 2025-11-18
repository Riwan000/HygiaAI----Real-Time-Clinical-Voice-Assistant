#!/usr/bin/env python3
"""
Ingest Knowledge Base Data into Qdrant

Populates the 'clinical_kb_collection' with:
- NCBI Bookshelf textbooks
- PubMed Central Open Access articles
- WHO Global Health Observatory data
- Medical ontologies

This collection is SEPARATE from patient records.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings import BioBERTEmbeddingGenerator
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType
from src.utils.file_processor import FileProcessor
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_knowledge_base():
    """Ingest all knowledge base data into clinical_kb_collection"""
    
    print("=" * 80)
    print("  Ingest Knowledge Base into Qdrant")
    print("=" * 80)
    print()
    print("Collection: clinical_kb_collection")
    print("Content: NCBI Bookshelf, PubMed OA, WHO GHO, Ontologies")
    print()
    
    # Initialize Qdrant storage for KNOWLEDGE BASE collection
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        knowledge_storage = QdrantStorage(
            url=qdrant_url,
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="clinical_kb_collection",  # SEPARATE collection
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print(f"✓ Connected to Qdrant Cloud: {qdrant_url}")
    else:
        knowledge_storage = QdrantStorage(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="clinical_kb_collection",  # SEPARATE collection
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print(f"✓ Connected to Qdrant Local: {os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6334')}")
    
    # Initialize embedding generator
    print("Initializing embedding generator...")
    embedder = BioBERTEmbeddingGenerator()
    
    # Initialize ingestion pipeline
    ingestion_pipeline = KnowledgeIngestionPipeline(
        qdrant_storage=knowledge_storage,
        text_embedding_generator=lambda text: embedder.generate_embedding(text),
        chunk_size=512,
        chunk_overlap=50,
        enforce_open_access=False  # Allow all knowledge base content
    )
    
    print()
    
    # Data directory
    data_dir = project_root / "hygiaai_datasets" / "knowledge_base"
    
    ingested_count = 0
    total_chunks = 0
    
    # 1. Process NCBI Bookshelf PDFs
    print("📚 Processing NCBI Bookshelf...")
    ncbi_dir = data_dir / "ncbi_bookshelf"
    if ncbi_dir.exists():
        pdf_files = list(ncbi_dir.glob("*.pdf"))
        print(f"   Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            try:
                print(f"   Processing: {pdf_file.name}")
                with open(pdf_file, 'rb') as f:
                    file_content = f.read()
                
                processed = FileProcessor.process_file(pdf_file.name, file_content)
                
                document = {
                    "title": processed.get("title", pdf_file.stem),
                    "text": processed.get("text", processed.get("content", "")),
                    "content": processed.get("text", processed.get("content", "")),
                    "source": "NCBI Bookshelf",
                    "domain": "guidelines",
                    "year": datetime.now(timezone.utc).year,
                    "provenance_url": f"https://hygiaai.local/knowledge/ncbi/{pdf_file.name}",
                    "author": "NCBI",
                    "version": "1.0"
                }
                
                metadata = KnowledgeBaseMetadata(
                    title=document["title"],
                    source="NCBI Bookshelf",
                    domain="guidelines",
                    year=datetime.now(timezone.utc).year,
                    embedding_type=EmbeddingType.TEXT,
                    access_type=AccessType.OPEN,
                    provenance_url=document["provenance_url"],
                    author="NCBI",
                    version="1.0"
                )
                
                point_ids = ingestion_pipeline.ingest_document(document, metadata=metadata)
                if point_ids:
                    ingested_count += 1
                    total_chunks += len(point_ids)
                    print(f"      ✓ Ingested ({len(point_ids)} chunks)")
            except Exception as e:
                print(f"      ✗ Error: {e}")
    else:
        print("   ⚠️  NCBI Bookshelf directory not found. Run download script first.")
    
    print()
    
    # 2. Process PubMed OA XML files
    print("📄 Processing PubMed Open Access...")
    pubmed_dir = data_dir / "pubmed_oa"
    if pubmed_dir.exists():
        xml_files = list(pubmed_dir.glob("*.xml"))
        print(f"   Found {len(xml_files)} XML files")
        
        # Process first few files as sample
        for xml_file in xml_files[:5]:  # Limit to first 5 for demo
            try:
                print(f"   Processing: {xml_file.name}")
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple XML parsing (can be enhanced)
                # Extract title and abstract
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'xml')
                
                title = soup.find('article-title')
                abstract = soup.find('abstract')
                
                if title and abstract:
                    text_content = f"{title.get_text()}\n\n{abstract.get_text()}"
                    
                    document = {
                        "title": title.get_text()[:200],
                        "text": text_content,
                        "content": text_content,
                        "source": "PubMed Central OA",
                        "domain": "pathology",
                        "year": datetime.now(timezone.utc).year,
                        "provenance_url": f"https://hygiaai.local/knowledge/pubmed/{xml_file.name}",
                        "author": "PubMed",
                        "version": "1.0"
                    }
                    
                    metadata = KnowledgeBaseMetadata(
                        title=document["title"],
                        source="PubMed Central OA",
                        domain="pathology",
                        year=datetime.now(timezone.utc).year,
                        embedding_type=EmbeddingType.TEXT,
                        access_type=AccessType.OPEN,
                        provenance_url=document["provenance_url"],
                        author="PubMed",
                        version="1.0"
                    )
                    
                    point_ids = ingestion_pipeline.ingest_document(document, metadata=metadata)
                    if point_ids:
                        ingested_count += 1
                        total_chunks += len(point_ids)
                        print(f"      ✓ Ingested ({len(point_ids)} chunks)")
            except Exception as e:
                print(f"      ✗ Error: {e}")
    else:
        print("   ⚠️  PubMed OA directory not found. Run download script first.")
    
    print()
    
    # 3. Process WHO GHO data
    print("🌍 Processing WHO Global Health Observatory...")
    who_dir = data_dir / "who_gho"
    if who_dir.exists():
        json_file = who_dir / "who_indicators.json"
        if json_file.exists():
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    who_data = json.load(f)
                
                # Process indicators
                if 'value' in who_data:
                    indicators = who_data['value']
                    print(f"   Found {len(indicators)} indicators")
                    
                    # Create document from indicators
                    text_content = "\n".join([
                        f"{ind.get('IndicatorName', '')}: {ind.get('Value', '')}"
                        for ind in indicators[:100]  # Limit to first 100
                    ])
                    
                    document = {
                        "title": "WHO Global Health Observatory Indicators",
                        "text": text_content,
                        "content": text_content,
                        "source": "WHO GHO",
                        "domain": "guidelines",
                        "year": datetime.now(timezone.utc).year,
                        "provenance_url": "https://ghoapi.azureedge.net/api/Indicator",
                        "author": "WHO",
                        "version": "1.0"
                    }
                    
                    metadata = KnowledgeBaseMetadata(
                        title=document["title"],
                        source="WHO GHO",
                        domain="guidelines",
                        year=datetime.now(timezone.utc).year,
                        embedding_type=EmbeddingType.TEXT,
                        access_type=AccessType.OPEN,
                        provenance_url=document["provenance_url"],
                        author="WHO",
                        version="1.0"
                    )
                    
                    point_ids = ingestion_pipeline.ingest_document(document, metadata=metadata)
                    if point_ids:
                        ingested_count += 1
                        total_chunks += len(point_ids)
                        print(f"      ✓ Ingested ({len(point_ids)} chunks)")
            except Exception as e:
                print(f"      ✗ Error: {e}")
    else:
        print("   ⚠️  WHO GHO directory not found. Run download script first.")
    
    # Summary
    print()
    print("=" * 80)
    print("  Summary")
    print("=" * 80)
    print(f"✅ Documents ingested: {ingested_count}")
    print(f"✅ Total chunks created: {total_chunks}")
    print(f"✅ Collection: clinical_kb_collection")
    print()
    print("Knowledge base collection is ready for RAG queries!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        ingest_knowledge_base()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

