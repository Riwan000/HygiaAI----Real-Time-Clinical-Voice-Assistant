# Google Gemini API Setup Guide

Complete guide to setting up and using Google Gemini API in HygiaAI.

---

## 🎯 Overview

HygiaAI now uses **Google Gemini** as the exclusive LLM provider for clinical reasoning and RAG-based insights.

---

## 🔑 Getting Your Gemini API Key

### Step 1: Get API Key

1. **Go to [Google AI Studio](https://makersuite.google.com/app/apikey)**
2. **Sign in** with your Google account
3. **Click "Create API Key"**
4. **Copy your API key** (starts with `AIza...`)

### Step 2: Set Environment Variable

**Local Development (.env file):**
```
GOOGLE_API_KEY=AIzaSyYour_Api_Key_Here
```

**Railway Deployment:**
- Go to Railway Dashboard → Your Backend Service → Variables
- Add: `GOOGLE_API_KEY=AIzaSyYour_Api_Key_Here`

---

## 📦 Installation

The `google-generativeai` package is already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install directly:
```bash
pip install google-generativeai>=0.3.0
```

---

## 🤖 Available Gemini Models

### Recommended Models:

1. **`gemini-1.5-pro`** (Default - Best for complex reasoning)
   - Best for: Clinical insights, differential diagnoses
   - Context: 1M tokens
   - Cost: Higher

2. **`gemini-1.5-flash`** (Fast & Cost-effective)
   - Best for: Quick responses, lower cost
   - Context: 1M tokens
   - Cost: Lower

3. **`gemini-pro`** (Legacy - Still supported)
   - Best for: General use
   - Context: 32K tokens
   - Cost: Medium

### Model Selection:

**For Production:**
```python
llm_model="gemini-1.5-pro"  # Best quality
```

**For Cost Optimization:**
```python
llm_model="gemini-1.5-flash"  # Faster, cheaper
```

---

## 💻 Code Usage

### Basic Usage:

```python
from src.rag.clinical_rag import ClinicalRAG, LLMProvider, RAGOptions
from src.retrieval.case_retrieval import CaseRetriever

# Initialize
retriever = CaseRetriever(qdrant_storage=storage)
rag = ClinicalRAG(
    case_retriever=retriever,
    llm_provider=LLMProvider.GEMINI,
    llm_model="gemini-1.5-pro"
)

# Generate insights
insights = rag.generate_insights(
    query_text="Patient with persistent cough and fever",
    options=RAGOptions(
        retrieval_limit=5,
        temperature=0.3  # Lower = more deterministic
    )
)
```

### API Endpoint:

```bash
POST /api/v1/clinical_memory/insights
{
  "query_text": "Patient presents with cough and fever",
  "options": {
    "llm_provider": "gemini",
    "llm_model": "gemini-1.5-pro",
    "retrieval_limit": 5
  }
}
```

---

## ⚙️ Configuration

### Environment Variables:

**Required:**
```
GOOGLE_API_KEY=AIzaSyYour_Api_Key_Here
```

**Optional (for model selection):**
- Default model is `gemini-1.5-pro`
- Can be changed in code or API request

### Default Settings:

```python
llm_provider = LLMProvider.GEMINI
llm_model = "gemini-1.5-pro"
temperature = 0.3  # Lower for medical accuracy
max_tokens = 2000
```

---

## 💰 Pricing

### Gemini 1.5 Pro:
- **Input:** $1.25 per 1M tokens
- **Output:** $5.00 per 1M tokens

### Gemini 1.5 Flash:
- **Input:** $0.075 per 1M tokens
- **Output:** $0.30 per 1M tokens

### Free Tier:
- **60 requests per minute**
- **1,500 requests per day**
- Great for demos and development!

---

## 🔒 Security

### Best Practices:

1. **Never commit API keys** to version control
2. **Use environment variables** only
3. **Rotate keys** regularly
4. **Monitor usage** in Google Cloud Console

### API Key Storage:

- ✅ `.env` file (local development)
- ✅ Railway environment variables (production)
- ❌ Never in source code
- ❌ Never in git repository

---

## 🧪 Testing

### Test Connection:

```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

response = model.generate_content("Hello, Gemini!")
print(response.text)
```

### Test RAG Endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/clinical_memory/insights \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Patient with fever and cough",
    "options": {
      "llm_provider": "gemini",
      "llm_model": "gemini-1.5-pro"
    }
  }'
```

---

## 🐛 Troubleshooting

### Error: "GOOGLE_API_KEY environment variable required"

**Solution:**
1. Check `.env` file exists and has `GOOGLE_API_KEY`
2. Verify API key is correct
3. Restart your application

### Error: "Google Generative AI library not available"

**Solution:**
```bash
pip install google-generativeai
```

### Error: "API key not valid"

**Solution:**
1. Verify API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Check for typos in environment variable
3. Ensure API key hasn't been revoked

### Error: "Quota exceeded"

**Solution:**
1. Check usage in Google Cloud Console
2. Upgrade to paid tier if needed
3. Use `gemini-1.5-flash` for lower costs

---

## 📊 Comparison with Other Providers

| Feature | Gemini | OpenAI | Anthropic |
|---------|--------|--------|-----------|
| **Free Tier** | ✅ Yes (60/min) | ❌ No | ❌ No |
| **Cost** | 💰 Low | 💰💰 Medium | 💰💰💰 High |
| **Context Window** | 1M tokens | 128K tokens | 200K tokens |
| **Speed** | ⚡ Fast | ⚡⚡ Very Fast | ⚡ Medium |
| **Medical Reasoning** | ✅ Excellent | ✅ Excellent | ✅ Excellent |

---

## ✅ Quick Start Checklist

- [ ] Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- [ ] Add `GOOGLE_API_KEY` to `.env` file (local) or Railway (production)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Test connection with simple Python script
- [ ] Test RAG endpoint with curl or Postman
- [ ] Monitor usage in Google Cloud Console

---

## 🎯 Benefits of Gemini

1. **Free Tier Available** - 60 requests/minute, 1,500/day
2. **Large Context Window** - 1M tokens (great for long medical histories)
3. **Cost Effective** - Lower pricing than competitors
4. **Fast Responses** - Quick generation times
5. **Excellent Medical Reasoning** - Strong performance on clinical tasks

---

## 📚 Additional Resources

- [Google AI Studio](https://makersuite.google.com/app/apikey) - Get API key
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini Models Guide](https://ai.google.dev/models/gemini)
- [Pricing Information](https://ai.google.dev/pricing)

---

**Updated:** All LLM functionality now uses Google Gemini exclusively.

