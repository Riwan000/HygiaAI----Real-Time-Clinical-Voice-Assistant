# Knowledge Base File Upload Feature

## ✅ Feature Complete

The knowledge base now supports **file browsing and upload** with automatic Qdrant integration.

---

## 🎯 Features

### 1. **File Upload**
- Upload PDF, DOCX, TXT, and MD files
- Automatic text extraction
- Chunking and embedding generation
- Storage in Qdrant knowledge base

### 2. **File Processing**
- **PDF**: Extracts text from all pages, preserves metadata
- **DOCX**: Extracts paragraphs and document properties
- **TXT/MD**: Reads plain text files

### 3. **Metadata Support**
- Domain classification
- Source attribution
- Year/Author information
- Automatic metadata extraction from files

---

## 📋 How to Use

### Frontend (Knowledge Browser)

1. **Open Knowledge Base Page**
   - Navigate to the Knowledge page in the app

2. **Click "Upload File" Button**
   - Green button next to the search bar

3. **Select File**
   - Choose PDF, DOCX, TXT, or MD file
   - File size limit: 20MB (configurable)

4. **Fill Optional Metadata**
   - **Domain**: Select from existing domains or choose new one
   - **Source**: Enter source name (e.g., "Medical Journal")
   - **Year**: Publication year
   - **Author**: Author name

5. **Upload**
   - Click "Upload" button
   - Progress bar shows upload status
   - Success message appears when complete

6. **Automatic Refresh**
   - Knowledge base automatically refreshes after upload
   - New document appears in search results

---

## 🔧 Backend API

### Endpoint: `POST /api/v1/clinical_memory/knowledge/upload`

**Request:**
```http
POST /api/v1/clinical_memory/knowledge/upload
Content-Type: multipart/form-data

file: <file>
domain: "clinical_reference" (optional)
source: "User Upload" (optional)
year: 2024 (optional)
author: "Dr. Smith" (optional)
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully uploaded and processed filename.pdf",
  "document_id": "uuid-here",
  "chunks_created": 5,
  "title": "Document Title",
  "domain": "clinical_reference",
  "source": "User Upload"
}
```

---

## 📦 Supported File Types

| Format | Extension | Status |
|--------|-----------|--------|
| PDF    | `.pdf`    | ✅ Full support |
| Word   | `.docx`, `.doc` | ✅ Full support |
| Text   | `.txt`, `.md` | ✅ Full support |

---

## 🔄 Processing Pipeline

1. **File Upload** → Backend receives file
2. **Text Extraction** → FileProcessor extracts text content
3. **Chunking** → Document split into 512-character chunks
4. **Embedding** → BioBERT generates embeddings for each chunk
5. **Storage** → Chunks stored in Qdrant knowledge base
6. **Indexing** → Immediately searchable

---

## 📁 Files Created/Modified

### Backend:
- ✅ `src/utils/file_processor.py` - File processing utilities
- ✅ `src/api/clinical_memory_api.py` - Upload endpoint added
- ✅ `requirements.txt` - Added PyPDF2

### Frontend:
- ✅ `frontend/src/components/KnowledgeBrowser.tsx` - Upload UI added
- ✅ `frontend/src/services/clinicalMemoryService.ts` - Upload method added

---

## 🧪 Testing

### Test File Upload:

```bash
curl -X POST http://localhost:8000/api/v1/clinical_memory/knowledge/upload \
  -F "file=@test_document.pdf" \
  -F "domain=clinical_reference" \
  -F "source=Test Upload" \
  -F "year=2024"
```

### Expected Response:
```json
{
  "success": true,
  "message": "Successfully uploaded and processed test_document.pdf",
  "document_id": "...",
  "chunks_created": 3,
  "title": "Test Document",
  "domain": "clinical_reference",
  "source": "Test Upload"
}
```

---

## ⚙️ Configuration

### File Size Limits:
- Default: 20MB (configurable in backend)

### Chunking:
- Chunk size: 512 characters
- Overlap: 50 characters
- Configurable in `KnowledgeIngestionPipeline`

### Embedding:
- Model: BioBERT (768 dimensions)
- Generated automatically for each chunk

---

## 🎨 UI Features

- **Upload Modal**: Clean, accessible modal dialog
- **Progress Bar**: Real-time upload progress
- **Error Handling**: Clear error messages
- **Success Feedback**: Confirmation with chunk count
- **Auto-refresh**: Knowledge base updates automatically

---

## 🔒 Security

- File type validation (whitelist only)
- File size limits
- Content sanitization
- No executable files allowed

---

## 📝 Next Steps

1. **Test the feature:**
   - Upload a PDF or DOCX file
   - Verify it appears in search results
   - Check that content is searchable

2. **Optional Enhancements:**
   - Batch file upload
   - Drag-and-drop interface
   - File preview before upload
   - Progress tracking for large files

---

**✅ Feature is ready to use!**

