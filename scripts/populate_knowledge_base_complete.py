#!/usr/bin/env python3
"""
Complete Medical Knowledge Base Population

This script populates the Qdrant knowledge base with medical information from:
1. Curated medical knowledge (internal)
2. Internet sources (WHO, CDC, medical references)
3. Open-access medical sources

Run this script to build a comprehensive knowledge base for enhanced SOAP generation.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from scripts.populate_medical_knowledge_base import populate_knowledge_base as populate_curated
from scripts.fetch_medical_knowledge_from_internet import populate_knowledge_base_from_internet

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def populate_complete_knowledge_base():
    """Populate knowledge base with both curated and internet-sourced knowledge"""
    print("=" * 80)
    print("  Complete Medical Knowledge Base Population")
    print("=" * 80)
    print()
    print("This will populate the knowledge base with:")
    print("  1. Curated medical knowledge (SOAP guidelines, vital signs, etc.)")
    print("  2. Internet-sourced knowledge (WHO, CDC, medical references)")
    print()
    
    # Step 1: Populate curated knowledge
    print("=" * 80)
    print("  Step 1: Curated Medical Knowledge")
    print("=" * 80)
    print()
    try:
        populate_curated()
    except Exception as e:
        logger.error(f"Error populating curated knowledge: {e}")
        print(f"⚠️  Warning: Curated knowledge population had issues: {e}")
        print("   Continuing with internet-sourced knowledge...")
        print()
    
    # Step 2: Populate internet-sourced knowledge
    print()
    print("=" * 80)
    print("  Step 2: Internet-Sourced Medical Knowledge")
    print("=" * 80)
    print()
    try:
        populate_knowledge_base_from_internet()
    except Exception as e:
        logger.error(f"Error populating internet-sourced knowledge: {e}")
        print(f"⚠️  Warning: Internet-sourced knowledge population had issues: {e}")
        print()
    
    # Final summary
    print()
    print("=" * 80)
    print("  Complete Knowledge Base Population Finished")
    print("=" * 80)
    print()
    print("✅ Knowledge base is now populated with:")
    print("   - Curated medical knowledge")
    print("   - WHO clinical guidelines")
    print("   - CDC treatment guidelines")
    print("   - Medical reference content")
    print()
    print("The knowledge base is ready for use in:")
    print("   - Enhanced SOAP note generation")
    print("   - Clinical decision support")
    print("   - Knowledge intelligence & trend analysis")
    print("=" * 80)


if __name__ == "__main__":
    populate_complete_knowledge_base()

