# NCBI Knowledge Base Scraper

This script scrapes open-access medical content from NCBI Bookshelf and PubMed Central (PMC) to populate the HygiaAI knowledge base.

## Sources

### 1. NCBI Bookshelf (Open-Access Textbooks)
- **Clinical Methods**: History, Physical, and Laboratory Examinations
- **StatPearls**: Comprehensive clinical reference
- **Specialty Textbooks**: Lab interpretation, treatment guidelines, and clinical methods across multiple specialties

### 2. PubMed Central Open Access
- Thousands of open-access clinical research papers
- Full-text articles with abstracts and body content
- Filtered for open-access content only

## Features

- ✅ Uses official NCBI Entrez E-utilities API
- ✅ Respects rate limiting (3 req/sec without API key, 10 req/sec with key)
- ✅ Chunks, embeds, and stores in Qdrant knowledge base
- ✅ Progress tracking and error handling
- ✅ Configurable limits and source selection

## Setup

### 1. Install Dependencies

```bash
pip install beautifulsoup4 lxml
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Qdrant Configuration
QDRANT_URL=https://your-qdrant-cloud-url
QDRANT_API_KEY=your-qdrant-api-key
# OR for local Qdrant:
QDRANT_HOST=localhost
QDRANT_PORT=6334

# Optional: NCBI API Key (recommended for higher rate limits)
NCBI_API_KEY=your-ncbi-api-key

# Configuration Options
MAX_PMC_ARTICLES=500          # Maximum PMC articles to fetch (default: 500)
SCRAPE_BOOKSHELF=true         # Scrape NCBI Bookshelf (default: true)
SCRAPE_PMC=true               # Scrape PubMed Central (default: true)
```

### 3. Get NCBI API Key (Optional but Recommended)

1. Go to https://www.ncbi.nlm.nih.gov/account/settings/
2. Create an account or log in
3. Generate an API key
4. Add it to your `.env` file as `NCBI_API_KEY`

**Benefits of API key:**
- Higher rate limit: 10 requests/second (vs 3 without key)
- More reliable access
- Better for large-scale scraping

## Usage

### Basic Usage

```bash
python scripts/scrape_ncbi_knowledge_base.py
```

### Configuration via Environment Variables

```bash
# Scrape only Bookshelf
SCRAPE_PMC=false python scripts/scrape_ncbi_knowledge_base.py

# Scrape only PMC (limit to 100 articles)
MAX_PMC_ARTICLES=100 SCRAPE_BOOKSHELF=false python scripts/scrape_ncbi_knowledge_base.py

# Scrape more PMC articles
MAX_PMC_ARTICLES=1000 python scripts/scrape_ncbi_knowledge_base.py
```

## What Gets Scraped

### NCBI Bookshelf
- **28+ open-access medical textbooks**
- Covers: Clinical Methods, Lab Interpretation, Treatment Guidelines
- Domains: Internal Medicine, Surgery, Pediatrics, Cardiology, etc.

### PubMed Central
- **Open-access clinical research papers**
- Full text including abstract and body
- Filtered for open-access content only
- Default limit: 500 articles (configurable)

## Output

The script will:
1. Search and fetch content from NCBI sources
2. Process and chunk documents
3. Generate embeddings using BioBERT
4. Store in Qdrant knowledge base collection: `hygiaai_knowledge_base`

Each document includes:
- Title, content, source, domain
- Year, author, provenance URL
- Proper metadata for retrieval

## Rate Limiting

The script automatically respects NCBI rate limits:
- **Without API key**: 0.4 seconds between requests (3 req/sec)
- **With API key**: 0.35 seconds between requests (10 req/sec)

## Troubleshooting

### "Connection timeout" errors
- Check your internet connection
- NCBI servers may be slow; the script will retry
- Consider using an NCBI API key for better reliability

### "Insufficient content" warnings
- Some books/articles may have limited text content
- The script skips documents with <500 characters
- This is normal and expected

### "Failed to initialize BioBERT"
- Ensure `transformers` and `torch` are installed
- First run will download the BioBERT model (~500MB)
- Ensure you have sufficient disk space

### Qdrant connection errors
- Verify `QDRANT_URL` and `QDRANT_API_KEY` are correct
- For local Qdrant, ensure it's running on the specified host/port
- Check Qdrant collection exists: `hygiaai_knowledge_base`

## Example Output

```
================================================================================
  NCBI Knowledge Base Scraper
  Scraping NCBI Bookshelf and PubMed Central Open Access
================================================================================

Initializing Qdrant storage...
✓ Qdrant storage initialized
Initializing BioBERT embedding generator...
✓ BioBERT embedding generator initialized
Initializing knowledge ingestion pipeline...
✓ Knowledge ingestion pipeline initialized

================================================================================
SCRAPING NCBI BOOKSHELF
================================================================================
Fetching NCBI Bookshelf open-access books...
✓ Found 28 open-access books on NCBI Bookshelf
   Fetching book: Clinical Methods: The History, Physical, and Laboratory Examinations (NBK430685)
   Fetching book: StatPearls (NBK557860)
...

================================================================================
SCRAPING PUBMED CENTRAL OPEN ACCESS
================================================================================
Searching PMC for open-access articles (max: 500)...
   Retrieved 100 PMC IDs (total: 100)
   Retrieved 100 PMC IDs (total: 200)
...
✓ Found 500 open-access PMC articles

Fetching full text for 500 PMC articles...
   Progress: 10/500 articles fetched
   Progress: 20/500 articles fetched
...

================================================================================
INGESTING DOCUMENTS INTO KNOWLEDGE BASE
================================================================================

Ingesting 528 documents into knowledge base...

✓ [1/528] Ingested: Clinical Methods: The History, Physical, and Laboratory... (45 chunks)
✓ [2/528] Ingested: StatPearls... (120 chunks)
...

================================================================================
  SCRAPING COMPLETE
================================================================================
Total documents scraped: 528
Successfully ingested: 525
Failed: 3
```

## Notes

- **First run**: BioBERT model download may take several minutes
- **Large datasets**: Scraping 500+ PMC articles can take 30-60 minutes
- **Storage**: Ensure sufficient Qdrant storage space
- **Legal**: All content is open-access and properly attributed with provenance URLs

## Next Steps

After scraping, you can:
1. Search the knowledge base via the API: `GET /api/v1/clinical_memory/knowledge/search`
2. Use it for RAG-based clinical insights
3. Query it for treatment guidelines and clinical methods
4. Run the script periodically to update with new content

