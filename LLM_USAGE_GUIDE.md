# LLM Usage in HygiaAI

## Overview

Yes, HygiaAI uses LLMs (Large Language Models) for **enhanced clinical reasoning** and **RAG-based insights generation**. However, LLMs are **optional** - the core system works without them.

---

## 🎯 Where LLMs Are Used

### 1. **Clinical RAG System** (`src/rag/clinical_rag.py`)

**Purpose:** Generate clinical insights, differential diagnoses, and recommendations

**Features:**
- Retrieves similar cases from Qdrant
- Uses LLM to analyze patterns and generate insights
- Provides differential diagnoses with confidence scores
- Generates treatment recommendations with citations
- Creates explainable reasoning chains

**Endpoint:** `/api/v1/clinical_memory/insights`

---

## 🤖 Supported LLM Providers

### 1. **OpenAI** (GPT-4, GPT-3.5)
```python
LLMProvider.OPENAI
Models: "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
```

### 2. **Anthropic** (Claude)
```python
LLMProvider.ANTHROPIC
Models: "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"
```

### 3. **OpenRouter** (Multiple Models)
```python
LLMProvider.OPENROUTER
Models: Any model supported by OpenRouter
```

### 4. **Ollama** (Local/Free)
```python
LLMProvider.OLLAMA
Models: "llama3.1:latest", "mistral:7b", etc.
```

---

## ⚙️ Configuration

### Environment Variables

**For OpenAI:**
```
OPENAI_API_KEY=your_openai_api_key
```

**For Anthropic:**
```
ANTHROPIC_API_KEY=your_anthropic_api_key
```

**For OpenRouter:**
```
OPENROUTER_API_KEY=your_openrouter_api_key
```

**For Ollama (Local):**
```
OLLAMA_BASE_URL=http://localhost:11434/api
```

---

## 📦 Required Dependencies

Add to `requirements.txt`:

```txt
# LLM Libraries (Optional)
openai>=1.0.0          # For OpenAI GPT models
anthropic>=0.18.0      # For Anthropic Claude models
```

**Note:** These are currently **NOT** in `requirements.txt` because LLM features are optional.

---

## 🔧 How It Works

### 1. **RAG Pipeline:**

```
User Query → Retrieve Similar Cases → Build Context → Call LLM → Parse Response → Return Insights
```

### 2. **LLM Prompt Structure:**

```python
System: "You are a clinical decision support system."
User: 
{
  "query_case": "...",
  "similar_cases": [...],
  "task": "Generate differential diagnoses and recommendations"
}
```

### 3. **LLM Response Format:**

```json
{
  "differential_diagnoses": [
    {"diagnosis": "...", "confidence": 0.85}
  ],
  "recommendations": [
    {"type": "treatment", "title": "...", "confidence": 0.9}
  ],
  "summary": "...",
  "reasoning_chain": [...]
}
```

---

## 🚀 Usage Examples

### API Endpoint:

```bash
POST /api/v1/clinical_memory/insights
{
  "query_text": "Patient presents with cough and fever",
  "options": {
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "retrieval_limit": 5
  }
}
```

### Python Code:

```python
from src.rag.clinical_rag import ClinicalRAG, LLMProvider, RAGOptions
from src.retrieval.case_retrieval import CaseRetriever

# Initialize
retriever = CaseRetriever(qdrant_storage=storage)
rag = ClinicalRAG(
    case_retriever=retriever,
    llm_provider=LLMProvider.OPENAI,
    llm_model="gpt-4",
    fallback_to_ollama=True  # Fallback to local Ollama if API fails
)

# Generate insights
insights = rag.generate_insights(
    query_text="Patient with persistent cough",
    options=RAGOptions(
        retrieval_limit=5,
        temperature=0.3  # Lower = more deterministic
    )
)
```

---

## ✅ What Works Without LLMs

The following features work **without** LLM API keys:

- ✅ **Transcription** (Deepgram)
- ✅ **Entity Extraction** (Medical NER)
- ✅ **SOAP Note Generation** (Rule-based)
- ✅ **Case Storage** (Qdrant)
- ✅ **Similar Case Retrieval** (Vector search)
- ✅ **Knowledge Base Search** (Vector search)
- ✅ **Analytics** (Pattern analysis)
- ✅ **Visualization** (Charts and trends)

---

## 🎯 What Requires LLMs

The following features **require** LLM API keys:

- 🔶 **RAG-Based Clinical Insights** (`/api/v1/clinical_memory/insights`)
  - Differential diagnoses generation
  - Treatment recommendations
  - Clinical reasoning chains
  - Evidence-based suggestions

---

## 💡 Fallback Behavior

If LLM API keys are not configured:

1. **RAG endpoints** will return an error or skip LLM reasoning
2. **Other features** continue to work normally
3. **Ollama fallback** can be enabled for local LLM usage (free)

---

## 🔒 Security & Privacy

### For Production:

1. **API Keys:** Store in environment variables, never in code
2. **Data Privacy:** LLM providers may log requests (check their policies)
3. **HIPAA Compliance:** Ensure LLM provider supports HIPAA if handling PHI
4. **Local Option:** Use Ollama for complete privacy (no data leaves your server)

---

## 📊 Cost Considerations

### OpenAI:
- GPT-4: ~$0.03 per 1K tokens (input), $0.06 per 1K tokens (output)
- GPT-3.5: ~$0.0015 per 1K tokens

### Anthropic:
- Claude Opus: ~$0.015 per 1K tokens
- Claude Sonnet: ~$0.003 per 1K tokens

### Ollama:
- **Free** (runs locally)
- Requires local GPU or CPU

### OpenRouter:
- Varies by model (often cheaper than direct APIs)

---

## 🛠️ Adding LLM Support to Requirements

To make LLM features available, add to `requirements.txt`:

```txt
# LLM Libraries (Optional - for RAG insights)
openai>=1.0.0
anthropic>=0.18.0
```

Then install:
```bash
pip install openai anthropic
```

---

## 🧪 Testing LLM Features

### 1. **Check if LLM is available:**

```python
import os
has_openai = os.getenv("OPENAI_API_KEY")
has_anthropic = os.getenv("ANTHROPIC_API_KEY")

if has_openai or has_anthropic:
    print("LLM features available!")
else:
    print("LLM features disabled - set API keys to enable")
```

### 2. **Test RAG endpoint:**

```bash
curl -X POST http://localhost:8000/api/v1/clinical_memory/insights \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Patient with fever and cough",
    "options": {
      "llm_provider": "openai",
      "llm_model": "gpt-4"
    }
  }'
```

---

## 📝 Summary

| Feature | Requires LLM? | Status |
|---------|---------------|--------|
| Transcription | ❌ No | ✅ Works |
| Entity Extraction | ❌ No | ✅ Works |
| SOAP Generation | ❌ No | ✅ Works |
| Case Storage | ❌ No | ✅ Works |
| Similar Case Retrieval | ❌ No | ✅ Works |
| Knowledge Base Search | ❌ No | ✅ Works |
| **RAG Clinical Insights** | ✅ **Yes** | 🔶 **Optional** |
| Analytics | ❌ No | ✅ Works |
| Visualization | ❌ No | ✅ Works |

---

## 🎯 Recommendation

**For Demo/Development:**
- Use **Ollama** (free, local, no API keys needed)
- Install: `ollama pull llama3.1:latest`
- Set: `OLLAMA_BASE_URL=http://localhost:11434/api`

**For Production:**
- Use **OpenAI GPT-4** or **Anthropic Claude** for best results
- Set API keys in Railway environment variables
- Consider HIPAA-compliant providers if handling PHI

---

**Current Status:** LLM features are **optional** and **not required** for core functionality. The system works great without them, but LLMs enhance clinical reasoning capabilities.

