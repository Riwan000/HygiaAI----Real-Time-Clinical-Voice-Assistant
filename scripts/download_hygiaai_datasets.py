#!/usr/bin/env python3
"""
HygiaAI Dataset Downloader Script

Downloads all required open-access medical datasets for:
- Clinical notes (MIMIC-III / MIMIC-IV / i2b2)
- Labs + Vitals (eICU, AmsterdamUMCdb)
- Imaging (MIMIC-CXR, NIH14, CheXpert, VinDr-PCXR)
- Audio (OpenSLR)
- Knowledge base (NCBI Bookshelf, PubMed OA)
- Public health datasets (WHO GHO)

Requirements:
pip install requests wget beautifulsoup4 feedparser

NOTE:
You need PhysioNet credentials for MIMIC + eICU datasets.
Set them as environment variables:
export PN_USERNAME="your_email"
export PN_PASSWORD="your_password"
"""

import os
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import zipfile
import tarfile
import json
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# -----------------------------------------------------
# CONFIG
# -----------------------------------------------------
DATA_DIR = project_root / "hygiaai_datasets"
DATA_DIR.mkdir(exist_ok=True)

PHYSIONET_USER = os.getenv("PN_USERNAME")
PHYSIONET_PASS = os.getenv("PN_PASSWORD")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})


# -----------------------------------------------------
# Helper: Download file with streaming
# -----------------------------------------------------
def download_file(url: str, dest_folder: Path, filename: Optional[str] = None) -> Path:
    """Download file with progress"""
    dest_folder.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = url.split("/")[-1]
    
    local_path = dest_folder / filename
    
    # Skip if already exists
    if local_path.exists():
        print(f"[⊘] Already exists: {local_path.name}")
        return local_path
    
    try:
        print(f"[↓] Downloading: {filename}...")
        with session.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(local_path, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r    Progress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n[✓] Downloaded: {local_path.name}")
        return local_path
    except Exception as e:
        print(f"\n[✗] Error downloading {filename}: {e}")
        if local_path.exists():
            local_path.unlink()
        raise


# -----------------------------------------------------
# PhysioNet Login (MIMIC-III / MIMIC-IV / eICU)
# -----------------------------------------------------
def physionet_login() -> bool:
    """Login to PhysioNet for protected datasets"""
    if not PHYSIONET_USER or not PHYSIONET_PASS:
        print("[!] PhysioNet username/password not set. Skipping protected datasets.")
        print("    Set PN_USERNAME and PN_PASSWORD environment variables.")
        return False
    
    login_url = "https://physionet.org/login/"
    payload = {
        "username": PHYSIONET_USER,
        "password": PHYSIONET_PASS
    }
    
    print("[+] Logging into PhysioNet...")
    try:
        r = session.post(login_url, data=payload, timeout=30)
        if r.status_code == 200 and "login" not in r.url.lower():
            print("[✓] PhysioNet login successful.\n")
            return True
        else:
            print("[✗] PhysioNet login failed. Check credentials.")
            return False
    except Exception as e:
        print(f"[✗] PhysioNet login error: {e}")
        return False


# -----------------------------------------------------
# 1. Knowledge Base Datasets
# -----------------------------------------------------
def download_ncbi_bookshelf():
    """Download NCBI Bookshelf medical textbooks"""
    print("\n[📚] Downloading NCBI Bookshelf medical textbooks...")
    bookshelf_dir = DATA_DIR / "knowledge_base" / "ncbi_bookshelf"
    bookshelf_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample NCBI Bookshelf URLs (add more as needed)
    urls = [
        "https://www.ncbi.nlm.nih.gov/books/NBK538260/pdf/Bookshelf_NBK538260.pdf",
        "https://www.ncbi.nlm.nih.gov/books/NBK305/pdf/Bookshelf_NBK305.pdf",
    ]
    
    for url in urls:
        try:
            download_file(url, bookshelf_dir)
        except Exception as e:
            print(f"[!] Failed to download {url}: {e}")
    
    print("[✓] NCBI Bookshelf download complete\n")


def download_pubmed_oa():
    """Download PubMed Central Open Access subset"""
    print("\n[📄] Downloading PubMed Open Access subset...")
    pubmed_dir = DATA_DIR / "knowledge_base" / "pubmed_oa"
    pubmed_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample PubMed OA URL (small subset)
    url = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/oa_comm/xml/comm_use.A-B.xml.tar.gz"
    
    try:
        download_file(url, pubmed_dir)
        print("[+] Extracting PubMed OA archive...")
        tar_path = pubmed_dir / "comm_use.A-B.xml.tar.gz"
        if tar_path.exists():
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(pubmed_dir)
            print("[✓] Extraction complete")
    except Exception as e:
        print(f"[!] Failed to download PubMed OA: {e}")
    
    print("[✓] PubMed OA download complete\n")


def download_who_gho():
    """Download WHO Global Health Observatory Data"""
    print("\n[🌍] Downloading WHO Global Health data...")
    who_dir = DATA_DIR / "knowledge_base" / "who_gho"
    who_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        url = "https://ghoapi.azureedge.net/api/Indicator"
        r = session.get(url, timeout=30)
        r.raise_for_status()
        
        indicators_file = who_dir / "who_indicators.json"
        with open(indicators_file, "w", encoding="utf-8") as f:
            json.dump(r.json(), f, indent=2)
        
        print(f"[✓] Saved WHO indicators to {indicators_file.name}")
    except Exception as e:
        print(f"[!] Failed to download WHO data: {e}")
    
    print("[✓] WHO GHO download complete\n")


# -----------------------------------------------------
# 2. Patient Records Datasets
# -----------------------------------------------------
def download_mimic3():
    """Download MIMIC-III clinical notes"""
    print("\n[🏥] Downloading MIMIC-III...")
    mimic_dir = DATA_DIR / "patient_records" / "mimic-iii"
    mimic_dir.mkdir(parents=True, exist_ok=True)
    
    MIMIC3_URL = "https://physionet.org/files/mimiciii/1.4"
    
    try:
        r = session.get(MIMIC3_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Find CSV files (clinical notes tables)
        files = [a["href"] for a in soup.find_all("a") 
                if a.get("href", "").endswith((".csv.gz", ".csv"))]
        
        print(f"[+] Found {len(files)} files in MIMIC-III")
        
        # Download key tables only (to avoid huge downloads)
        key_tables = ["NOTEEVENTS", "ADMISSIONS", "PATIENTS", "ICUSTAYS"]
        for f in files:
            if any(table in f.upper() for table in key_tables):
                try:
                    download_file(f"{MIMIC3_URL}/{f}", mimic_dir)
                except Exception as e:
                    print(f"[!] Failed to download {f}: {e}")
    except Exception as e:
        print(f"[!] Failed to access MIMIC-III: {e}")
    
    print("[✓] MIMIC-III download complete\n")


def download_mimic4():
    """Download MIMIC-IV clinical notes"""
    print("\n[🏥] Downloading MIMIC-IV...")
    mimic4_dir = DATA_DIR / "patient_records" / "mimic-iv"
    mimic4_dir.mkdir(parents=True, exist_ok=True)
    
    MIMIC4_URL = "https://physionet.org/files/mimiciv/2.2"
    
    try:
        r = session.get(MIMIC4_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Find CSV files
        files = [a["href"] for a in soup.find_all("a") 
                if a.get("href", "").endswith((".csv.gz", ".csv"))]
        
        print(f"[+] Found {len(files)} files in MIMIC-IV")
        
        # Download key tables only
        key_tables = ["note", "admissions", "patients", "icustays"]
        for f in files:
            if any(table in f.lower() for table in key_tables):
                try:
                    download_file(f"{MIMIC4_URL}/{f}", mimic4_dir)
                except Exception as e:
                    print(f"[!] Failed to download {f}: {e}")
    except Exception as e:
        print(f"[!] Failed to access MIMIC-IV: {e}")
    
    print("[✓] MIMIC-IV download complete\n")


def download_eicu():
    """Download eICU Collaborative Research Database"""
    print("\n[🏥] Downloading eICU-CRD...")
    eicu_dir = DATA_DIR / "patient_records" / "eicu"
    eicu_dir.mkdir(parents=True, exist_ok=True)
    
    EICU_URL = "https://physionet.org/files/eicu-crd/2.0"
    
    try:
        r = session.get(EICU_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        files = [a["href"] for a in soup.find_all("a") 
                if a.get("href", "").endswith(".csv.gz")]
        
        print(f"[+] Found {len(files)} files in eICU")
        
        # Download key tables only
        key_tables = ["note", "patient", "admission", "vital"]
        for f in files[:10]:  # Limit to first 10 files
            if any(table in f.lower() for table in key_tables):
                try:
                    download_file(f"{EICU_URL}/{f}", eicu_dir)
                except Exception as e:
                    print(f"[!] Failed to download {f}: {e}")
    except Exception as e:
        print(f"[!] Failed to access eICU: {e}")
    
    print("[✓] eICU download complete\n")


def download_amsterdam_umcdb():
    """Download AmsterdamUMCdb metadata"""
    print("\n[🏥] Downloading Amsterdam UMC DB...")
    ams_dir = DATA_DIR / "patient_records" / "amsterdam_umcdb"
    ams_dir.mkdir(parents=True, exist_ok=True)
    
    print("[!] AmsterdamUMCdb requires manual registration.")
    print("    Visit: https://amsterdammedicaldatascience.nl/")
    print("[✓] Amsterdam UMC DB info saved\n")


def download_i2b2():
    """i2b2 Clinical Notes"""
    print("\n[🏥] i2b2 dataset information...")
    i2b2_dir = DATA_DIR / "patient_records" / "i2b2"
    i2b2_dir.mkdir(parents=True, exist_ok=True)
    
    print("[!] i2b2 requires registration and manual download.")
    print("    Visit: https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/")
    print("[✓] i2b2 info saved\n")


# -----------------------------------------------------
# 3. Imaging Datasets
# -----------------------------------------------------
def download_mimic_cxr():
    """Download MIMIC-CXR metadata"""
    print("\n[🖼️] Downloading MIMIC-CXR-JPG metadata...")
    cxr_dir = DATA_DIR / "imaging" / "mimic-cxr"
    cxr_dir.mkdir(parents=True, exist_ok=True)
    
    MIMIC_CXR_URL = "https://physionet.org/files/mimic-cxr-jpg/2.0.0"
    
    try:
        r = session.get(MIMIC_CXR_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        files = [a["href"] for a in soup.find_all("a") 
                if a.get("href", "").endswith(".csv.gz")]
        
        for f in files:
            try:
                download_file(f"{MIMIC_CXR_URL}/{f}", cxr_dir)
            except Exception as e:
                print(f"[!] Failed to download {f}: {e}")
        
        print("[!] Note: Full images must be downloaded manually due to large size.")
    except Exception as e:
        print(f"[!] Failed to access MIMIC-CXR: {e}")
    
    print("[✓] MIMIC-CXR metadata download complete\n")


def download_nih_chestxray14():
    """NIH ChestXray14 information"""
    print("\n[🖼️] NIH ChestXray14 dataset...")
    nih_dir = DATA_DIR / "imaging" / "nih_chestxray14"
    nih_dir.mkdir(parents=True, exist_ok=True)
    
    print("[!] Requires Kaggle API. Run:")
    print("    kaggle datasets download -d nih-chest-xrays/data")
    print("[✓] NIH ChestXray14 info saved\n")


def download_chexpert():
    """CheXpert information"""
    print("\n[🖼️] CheXpert dataset...")
    chex_dir = DATA_DIR / "imaging" / "chexpert"
    chex_dir.mkdir(parents=True, exist_ok=True)
    
    print("[!] Download from official website (requires form):")
    print("    https://stanfordmlgroup.github.io/competitions/chexpert/")
    print("[✓] CheXpert info saved\n")


def download_vindr():
    """VinDr-PCXR information"""
    print("\n[🖼️] VinDr-PCXR dataset...")
    vindr_dir = DATA_DIR / "imaging" / "vindr_pcxr"
    vindr_dir.mkdir(parents=True, exist_ok=True)
    
    print("[!] Download from Kaggle:")
    print("    kaggle datasets download -d vindr/vindr-pcxr")
    print("[✓] VinDr-PCXR info saved\n")


# -----------------------------------------------------
# 4. Audio Datasets
# -----------------------------------------------------
def download_openslr():
    """Download OpenSLR Medical Speech Dataset"""
    print("\n[🎤] Downloading OpenSLR Speech Dataset...")
    slr_dir = DATA_DIR / "audio" / "openslr"
    slr_dir.mkdir(parents=True, exist_ok=True)
    
    url = "https://www.openslr.org/resources/83/medical_speech.tar.gz"
    
    try:
        tar_path = download_file(url, slr_dir)
        print("[+] Extracting...")
        if tar_path.exists():
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(slr_dir)
            print("[✓] Extraction complete")
    except Exception as e:
        print(f"[!] Failed to download OpenSLR: {e}")
    
    print("[✓] OpenSLR download complete\n")


# -----------------------------------------------------
# MAIN
# -----------------------------------------------------
def main():
    """Download all datasets"""
    print("=" * 80)
    print("  HygiaAI Dataset Downloader")
    print("=" * 80)
    print()
    
    # Login to PhysioNet if credentials provided
    logged_in = physionet_login()
    
    # Knowledge Base Datasets (always available)
    print("\n" + "=" * 80)
    print("  KNOWLEDGE BASE DATASETS")
    print("=" * 80)
    download_ncbi_bookshelf()
    download_pubmed_oa()
    download_who_gho()
    
    # Patient Records Datasets (require PhysioNet login)
    if logged_in:
        print("\n" + "=" * 80)
        print("  PATIENT RECORDS DATASETS")
        print("=" * 80)
        download_mimic3()
        download_mimic4()
        download_eicu()
    else:
        print("\n[!] Skipping patient records datasets (MIMIC, eICU) - requires PhysioNet login")
    
    download_i2b2()
    download_amsterdam_umcdb()
    
    # Imaging Datasets
    if logged_in:
        print("\n" + "=" * 80)
        print("  IMAGING DATASETS")
        print("=" * 80)
        download_mimic_cxr()
    
    download_nih_chestxray14()
    download_chexpert()
    download_vindr()
    
    # Audio Datasets
    print("\n" + "=" * 80)
    print("  AUDIO DATASETS")
    print("=" * 80)
    download_openslr()
    
    # Summary
    print("\n" + "=" * 80)
    print("  DOWNLOAD SUMMARY")
    print("=" * 80)
    print(f"✓ Datasets saved to: {DATA_DIR}")
    print("\nNext steps:")
    print("1. Run ingestion scripts to populate Qdrant collections:")
    print("   - scripts/ingest_knowledge_base.py")
    print("   - scripts/ingest_patient_records.py")
    print("   - scripts/ingest_imaging_data.py (optional)")
    print("   - scripts/ingest_audio_data.py (optional)")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

