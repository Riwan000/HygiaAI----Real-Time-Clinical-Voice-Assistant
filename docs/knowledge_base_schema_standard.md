# Qdrant Knowledge Base Schema & Embedding Standard

This document defines the standard schema, chunking policy, and embedding specifications for knowledge base documents stored in Qdrant.

## 📋 Document Payload Schema

### Required Fields

All knowledge base documents must include the following required metadata fields:

- **`title`** (string, required): Document title
- **`source`** (string, required): Source identifier (e.g., "NCBI Bookshelf", "PubMed OA", "WHO eLENA", "demo")

### Optional Metadata Fields

- **`domain`** (string, optional): Medical domain classification
  - Valid values: `pathology`, `pharmacology`, `guidelines`, `anatomy`, `surgery`, `pediatrics`, `cardiology`, `oncology`, `general`
  
- **`year`** (integer, optional): Publication year (1900-2100)

- **`embedding_type`** (string, optional): Type of embedding
  - Valid values: `text`, `image`, `multimodal`
  - Default: `text`

- **`access_type`** (string, optional): Access classification
  - Valid values: `open`, `restricted`, `private`
  - Default: `open`

- **`provenance_url`** (string, optional): Original source URL (must be valid HTTP/HTTPS URL)

- **`version`** (string, optional): Document version identifier

- **`author`** (string, optional): Document author(s)

- **`chunk_index`** (integer, optional): Index of this chunk (0-based) for chunked documents

- **`chunk_total`** (integer, optional): Total number of chunks in the document

- **`created_at`** (datetime, optional): Document creation timestamp (ISO format)

- **`updated_at`** (datetime, optional): Document last update timestamp (ISO format)

### Document Content Fields

- **`text`** (string, required): Document text content (or use `content` field)

### Example Schema

```json
{
  "id": "uuid-here",
  "vector": [0.1, 0.2, ...],  // 768-dimensional vector
  "payload": {
    "title": "Introduction to Pathology",
    "source": "demo",
    "domain": "pathology",
    "year": 2023,
    "embedding_type": "text",
    "access_type": "open",
    "provenance_url": "https://demo.hygiaai.com/pathology_intro.html",
    "version": "1.0",
    "author": "Dr. Medical Education",
    "chunk_index": 0,
    "chunk_total": 3,
    "created_at": "2023-11-12T10:00:00Z",
    "updated_at": "2023-11-12T10:00:00Z",
    "text": "Pathology is the medical specialty...",
    "doc_hash": "sha256-hash-here"
  }
}
```

## 📄 Chunking Policy

### Standard Chunking Parameters

- **Chunk Size**: 512 characters (default)
  - Minimum: 100 characters
  - Maximum: 2048 characters
  
- **Chunk Overlap**: 50 characters (default)
  - Must be less than chunk size
  - Ensures context continuity between chunks

### Chunking Strategy

1. **Text Splitting**: Documents are split into overlapping chunks
2. **Chunk Indexing**: Each chunk is assigned a sequential index (0-based)
3. **Metadata Preservation**: All metadata is preserved in each chunk
4. **Chunk Metadata**: Each chunk includes:
   - `chunk_index`: Position in the document
   - `chunk_total`: Total number of chunks
   - `chunk_start`: Character position where chunk starts
   - `chunk_end`: Character position where chunk ends

### Example Chunking

For a 1500-character document:
- Chunk 0: characters 0-512
- Chunk 1: characters 462-974 (50 char overlap)
- Chunk 2: characters 924-1436 (50 char overlap)
- Chunk 3: characters 1386-1500 (remaining text)

## 🔢 Embedding Specifications

### Text Embeddings

- **Model**: `pritamdeka/S-PubMedBert-MS-MARCO`
- **Dimension**: 768
- **Type**: Medical domain-specific BERT model
- **Usage**: Primary embedding for all text documents

### Image Embeddings (Future)

- **Model**: CLIP (Contrastive Language-Image Pre-training)
- **Dimension**: 512
- **Usage**: For multimodal documents with images

### Multi-Vector Embeddings

For documents with both text and images:
- Use named vectors in Qdrant:
  ```json
  {
    "vector": {
      "text": [0.1, 0.2, ...],  // 768-dim
      "image": [0.3, 0.4, ...]  // 512-dim
    }
  }
  ```

### Embedding Generation

1. **Text Processing**: 
   - Normalize whitespace
   - Preserve medical terminology
   - Handle special characters

2. **Embedding Generation**:
   - Generate embeddings for each chunk
   - Store embeddings with corresponding metadata
   - Ensure dimension consistency (768 for text)

## ✅ Validation Rules

### Metadata Validation

1. **Required Fields**: `title` and `source` must be present and non-empty
2. **Domain Validation**: If `domain` is provided, must be from valid domains list
3. **Year Validation**: If `year` is provided, must be between 1900 and 2100
4. **URL Validation**: If `provenance_url` is provided, must be valid HTTP/HTTPS URL
5. **Chunk Validation**: `chunk_index` must be less than `chunk_total`

### Document Validation

1. **Content Requirement**: Document must have either `text` or `content` field
2. **Text Validation**: Text content must be non-empty string

### Embedding Validation

1. **Dimension Check**: Text embeddings must be exactly 768 dimensions
2. **Type Check**: All embedding values must be numeric (int or float)
3. **Non-Empty**: Embeddings cannot be empty

### Chunking Validation

1. **Size Limits**: Chunk size must be between 100 and 2048 characters
2. **Overlap Check**: Overlap must be less than chunk size
3. **Non-Negative**: Overlap must be non-negative

## 🔍 Query Filtering

### Supported Filter Keys

- `title`: Exact match on title
- `source`: Exact match on source
- `domain`: Exact match on domain
- `year`: Range filter (e.g., `{"gte": 2020, "lte": 2023}`)
- `embedding_type`: Exact match on embedding type
- `access_type`: Exact match on access type
- `provenance_url`: Exact match on URL
- `version`: Exact match on version
- `author`: Exact match on author
- `chunk_index`: Range filter for chunk index
- `chunk_total`: Range filter for total chunks
- `created_at`: Range filter (ISO datetime strings)
- `updated_at`: Range filter (ISO datetime strings)
- `doc_hash`: Exact match on document hash

### Filter Examples

```python
# Filter by domain
filters = {"domain": "pathology"}

# Filter by year range
filters = {"year": {"gte": 2020, "lte": 2023}}

# Filter by multiple domains
filters = {"domain": {"in": ["pathology", "pharmacology"]}}

# Filter by source and domain
filters = {
    "source": "demo",
    "domain": "pathology"
}
```

## 📊 Collection Configuration

### Qdrant Collection Settings

- **Collection Name**: `knowledge_base`
- **Vector Size**: 768 (for text embeddings)
- **Distance Metric**: Cosine similarity
- **Multi-Vector Support**: Enabled (for text + image embeddings)

### Indexing

- **HNSW Index**: Enabled for fast approximate nearest neighbor search
- **Payload Indexing**: Enabled for metadata fields (title, source, domain, year)

## 🔄 Versioning & Updates

### Document Versioning

- **Version Field**: Use semantic versioning (e.g., "1.0", "1.1", "2.0")
- **Hash-Based Deduplication**: Documents are identified by content hash
- **Delta Updates**: Only new or changed documents are ingested

### Update Strategy

1. **Hash Comparison**: Compare document hash with existing documents
2. **Version Check**: If document exists, check version number
3. **Force Update**: Option to force update even if hash matches
4. **Timestamp Tracking**: Track `created_at` and `updated_at` timestamps

## 🧪 Testing & Validation

### Schema Validation Tests

- Validate required fields are present
- Validate field types and formats
- Validate embedding dimensions
- Validate chunking parameters
- Validate filter dictionaries

### Integration Tests

- Test document ingestion with valid schema
- Test query filtering with various filters
- Test chunking with different document sizes
- Test embedding generation and storage

## 📝 Best Practices

1. **Always include provenance**: Store `provenance_url` for traceability
2. **Use semantic versioning**: Track document versions properly
3. **Validate before ingestion**: Use `SchemaValidator` before storing
4. **Consistent chunking**: Use standard chunk size (512) and overlap (50)
5. **Domain classification**: Always classify documents by domain
6. **Access type marking**: Mark documents as `open`, `restricted`, or `private`
7. **Year inclusion**: Include publication year when available
8. **Author attribution**: Include author information when available

## 🔗 Related Documentation

- [Knowledge Ingestion Pipeline](../src/storage/knowledge_ingestion.py)
- [Schema Definitions](../src/storage/schema.py)
- [Schema Validator](../src/storage/schema_validator.py)
- [Qdrant Storage](../src/storage/qdrant_storage.py)

