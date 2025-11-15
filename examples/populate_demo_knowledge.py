#!/usr/bin/env python3
"""
Populate Demo Knowledge Base

Collects and stores sample medical knowledge for the demo.
"""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.collector import (
    KnowledgeCollector,
    MedicalSource,
    CrawlerConfig
)
from src.storage.qdrant_storage import QdrantStorage
from src.storage.knowledge_ingestion import KnowledgeIngestionPipeline
from src.embeddings.text_embeddings import TextEmbeddingGenerator
from src.collector import ParsedDocument
from src.storage.schema import KnowledgeBaseMetadata, EmbeddingType, AccessType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_documents():
    """Create sample medical documents for demo"""
    return [
        {
            "url": "https://demo.hygiaai.com/pathology_intro.html",
            "title": "Introduction to Pathology",
            "text": """
            Pathology is the medical specialty concerned with the study of disease. It involves 
            the examination of tissues, organs, and bodily fluids to diagnose diseases and 
            understand their causes and mechanisms.
            
            Pathologists use various techniques including:
            - Microscopy: Examining tissue samples under a microscope
            - Molecular biology: Analyzing DNA, RNA, and proteins
            - Immunohistochemistry: Using antibodies to identify specific proteins
            - Cytology: Examining individual cells
            
            Common pathological conditions include:
            - Inflammation: The body's response to injury or infection
            - Infection: Invasion by microorganisms
            - Neoplasia: Abnormal growth of cells (benign or malignant)
            - Degenerative diseases: Progressive deterioration of tissues
            
            Understanding pathology is essential for accurate diagnosis and effective treatment 
            planning. Pathologists work closely with clinicians to provide diagnostic information 
            that guides patient care.
            """,
            "source": "demo",
            "author": "Dr. Medical Education",
            "year": 2023,
            "file_type": "html",
            "provenance_url": "https://demo.hygiaai.com/pathology_intro.html"
        },
        {
            "url": "https://demo.hygiaai.com/pharmacology_basics.html",
            "title": "Pharmacology Fundamentals",
            "text": """
            Pharmacology is the study of how drugs interact with biological systems. It encompasses 
            both pharmacokinetics (what the body does to the drug) and pharmacodynamics (what the 
            drug does to the body).
            
            Key concepts in pharmacology:
            - Absorption: How drugs enter the bloodstream
            - Distribution: How drugs move throughout the body
            - Metabolism: How drugs are broken down
            - Excretion: How drugs are removed from the body
            
            Drug interactions can occur at various levels:
            - Pharmacokinetic interactions: Affect drug absorption, distribution, metabolism, or excretion
            - Pharmacodynamic interactions: Affect drug action at the target site
            - Drug-drug interactions: When multiple drugs interact
            - Drug-food interactions: When food affects drug absorption or metabolism
            
            Understanding pharmacology is crucial for safe and effective medication use. Healthcare 
            providers must consider patient factors, drug properties, and potential interactions when 
            prescribing medications.
            """,
            "source": "demo",
            "author": "Dr. Pharmacy Expert",
            "year": 2023,
            "file_type": "html",
            "provenance_url": "https://demo.hygiaai.com/pharmacology_basics.html"
        },
        {
            "url": "https://demo.hygiaai.com/clinical_guidelines.html",
            "title": "Clinical Practice Guidelines",
            "text": """
            Clinical practice guidelines are systematically developed statements to assist 
            practitioners and patients in making decisions about appropriate healthcare. They are 
            based on the best available evidence and expert consensus.
            
            Guidelines serve several important purposes:
            - Standardize care across different healthcare settings
            - Improve patient outcomes through evidence-based recommendations
            - Reduce variations in practice
            - Provide a framework for quality improvement
            
            Guidelines should be:
            - Based on systematic review of evidence
            - Developed by multidisciplinary teams
            - Regularly updated as new evidence emerges
            - Transparent about methodology and conflicts of interest
            
            Healthcare providers should use guidelines as a tool to inform clinical decision-making, 
            while also considering individual patient circumstances and preferences.
            """,
            "source": "demo",
            "author": "Clinical Guidelines Committee",
            "year": 2023,
            "file_type": "html",
            "provenance_url": "https://demo.hygiaai.com/clinical_guidelines.html"
        },
        {
            "url": "https://demo.hygiaai.com/diagnosis_principles.html",
            "title": "Principles of Medical Diagnosis",
            "text": """
            Medical diagnosis is the process of determining which disease or condition explains a 
            patient's symptoms and signs. It involves gathering information through history-taking, 
            physical examination, and diagnostic tests.
            
            The diagnostic process typically involves:
            1. History taking: Gathering information about symptoms, medical history, and risk factors
            2. Physical examination: Observing and examining the patient
            3. Diagnostic testing: Ordering appropriate laboratory tests, imaging, or other studies
            4. Differential diagnosis: Considering multiple possible diagnoses
            5. Final diagnosis: Reaching a conclusion based on all available information
            
            Common diagnostic errors include:
            - Premature closure: Stopping the diagnostic process too early
            - Anchoring bias: Relying too heavily on initial information
            - Confirmation bias: Seeking information that confirms initial suspicions
            - Availability bias: Overestimating the likelihood of easily recalled diagnoses
            
            Accurate diagnosis is essential for effective treatment and optimal patient outcomes.
            """,
            "source": "demo",
            "author": "Dr. Diagnostic Medicine",
            "year": 2023,
            "file_type": "html",
            "provenance_url": "https://demo.hygiaai.com/diagnosis_principles.html"
        },
        {
            "url": "https://demo.hygiaai.com/treatment_protocols.html",
            "title": "Treatment Protocols and Standards",
            "text": """
            Treatment protocols are standardized approaches to managing specific medical conditions. 
            They help ensure consistent, evidence-based care across different healthcare settings.
            
            Treatment protocols typically include:
            - Indications for treatment
            - Contraindications and precautions
            - Dosage and administration guidelines
            - Monitoring requirements
            - Expected outcomes and success criteria
            - Management of adverse effects
            
            Common treatment modalities include:
            - Pharmacological therapy: Using medications
            - Surgical intervention: Performing procedures
            - Physical therapy: Rehabilitation and exercise
            - Behavioral interventions: Counseling and therapy
            - Lifestyle modifications: Diet, exercise, and other changes
            
            Treatment should be individualized based on:
            - Patient characteristics (age, comorbidities, preferences)
            - Disease severity and stage
            - Available resources and expertise
            - Patient response to initial treatment
            
            Regular monitoring and adjustment of treatment plans are essential for optimal outcomes.
            """,
            "source": "demo",
            "author": "Treatment Standards Committee",
            "year": 2023,
            "file_type": "html",
            "provenance_url": "https://demo.hygiaai.com/treatment_protocols.html"
        },
        {
            "url": "https://demo.hygiaai.com/patient_safety.html",
            "title": "Patient Safety in Clinical Practice",
            "text": """
            Patient safety is a fundamental principle of healthcare that focuses on preventing harm 
            to patients during the provision of healthcare services. It involves identifying, 
            preventing, and managing risks that could lead to patient harm.
            
            Key areas of patient safety include:
            - Medication safety: Preventing medication errors
            - Infection prevention: Reducing healthcare-associated infections
            - Surgical safety: Preventing surgical errors and complications
            - Diagnostic safety: Reducing diagnostic errors
            - Communication: Ensuring clear and accurate information exchange
            
            Common safety measures include:
            - Checklists and protocols
            - Electronic health records
            - Barcode medication administration
            - Hand hygiene protocols
            - Time-out procedures before surgery
            
            Healthcare providers must be vigilant about patient safety and continuously work to 
            improve systems and processes that protect patients from harm.
            """,
            "source": "demo",
            "author": "Patient Safety Institute",
            "year": 2023,
            "file_type": "html",
            "provenance_url": "https://demo.hygiaai.com/patient_safety.html"
        }
    ]


def populate_knowledge_base():
    """Populate knowledge base with demo documents"""
    print("=" * 80)
    print("  Populating Demo Knowledge Base")
    print("=" * 80)
    print()
    
    try:
        # Initialize Qdrant storage
        print("Initializing Qdrant storage...")
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="knowledge_base",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        print("✓ Qdrant storage initialized")
        
        # Initialize embedding generator
        print("Initializing text embedding generator...")
        embedding_gen = TextEmbeddingGenerator()
        print("✓ Text embedding generator initialized")
        
        # Create ingestion pipeline
        print("Creating knowledge ingestion pipeline...")
        ingestion_pipeline = KnowledgeIngestionPipeline(
            qdrant_storage=storage,
            text_embedding_generator=embedding_gen.generate_embedding,
            chunk_size=512,
            chunk_overlap=50
        )
        print("✓ Knowledge ingestion pipeline created")
        
        # Create collector
        print("Creating knowledge collector...")
        collector = KnowledgeCollector(
            storage_directory="data/demo_collected",
            ingestion_pipeline=ingestion_pipeline
        )
        print("✓ Knowledge collector created")
        print()
        
        # Get demo documents
        print("Preparing demo documents...")
        demo_documents = create_demo_documents()
        print(f"✓ Prepared {len(demo_documents)} demo documents")
        print()
        
        # Ingest documents
        print("Ingesting documents into Qdrant...")
        print()
        
        ingested_count = 0
        total_chunks = 0
        
        for i, doc_data in enumerate(demo_documents, 1):
            try:
                print(f"[{i}/{len(demo_documents)}] Processing: {doc_data['title']}")
                
                # Infer domain
                parsed_doc = ParsedDocument(
                    url=doc_data["url"],
                    title=doc_data["title"],
                    content=doc_data.get("text", doc_data.get("content", "")),
                    source=doc_data["source"],
                    domain=doc_data["source"]
                )
                domain = collector._infer_domain(parsed_doc)
                
                # Create metadata
                metadata = KnowledgeBaseMetadata(
                    title=doc_data["title"],
                    source="demo",
                    domain=domain,
                    year=doc_data["year"],
                    embedding_type=EmbeddingType.TEXT,
                    access_type=AccessType.OPEN,
                    provenance_url=doc_data["provenance_url"],
                    author=doc_data["author"]
                )
                
                # Ingest document
                point_ids = ingestion_pipeline.ingest_document(
                    doc_data,
                    metadata=metadata
                )
                
                if point_ids:
                    ingested_count += 1
                    total_chunks += len(point_ids)
                    print(f"  ✓ Ingested successfully: {len(point_ids)} chunks")
                    print(f"  Domain: {domain or 'general'}")
                else:
                    print(f"  ✗ Failed to ingest")
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        # Summary
        print("=" * 80)
        print("  Ingestion Summary")
        print("=" * 80)
        print(f"Documents processed: {len(demo_documents)}")
        print(f"Documents ingested: {ingested_count}")
        print(f"Total chunks created: {total_chunks}")
        print()
        
        # Verify collection
        print("Verifying collection...")
        collection_info = storage.get_collection_info()
        if collection_info:
            points_count = collection_info.get("points_count", 0)
            print(f"✓ Collection now contains {points_count} points")
        print()
        
        print("=" * 80)
        print("  Knowledge Base Population Complete!")
        print("=" * 80)
        print()
        print("The knowledge base is now ready for the demo.")
        print("You can query it using the retrieval and RAG modules.")
        
    except Exception as e:
        print(f"\n✗ Error populating knowledge base: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: Make sure Qdrant is running on localhost:6333")


if __name__ == "__main__":
    populate_knowledge_base()

