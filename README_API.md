# Running the HygiaAI API Server

## Quick Start

### Option 1: Using the run script (Recommended)
```bash
python run_server.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn src.api.main:app --reload --port 8000
```

### Option 3: Using Python module
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

## Access the API

Once the server is running, you can access:

- **API Documentation (Swagger UI)**: http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health
- **Root Endpoint**: http://127.0.0.1:8000/

## Available Endpoints

### Visualization API
- `/api/visualization/trends` - Temporal trend analysis
- `/api/visualization/case-map` - Case map visualization
- `/api/visualization/outbreak/detect` - Outbreak detection
- `/api/visualization/outbreak/detect-advanced` - Advanced outbreak detection

### EHR API
- `/api/ehr/import/hl7` - Import HL7 messages
- `/api/ehr/export/hl7` - Export HL7 messages
- `/api/ehr/import/fhir` - Import FHIR resources
- `/api/ehr/export/fhir` - Export FHIR resources

### Compliance API
- `/api/compliance/audit/logs` - Get audit logs
- `/api/compliance/access/check` - Check access permissions
- `/api/compliance/gdpr/request` - GDPR data subject requests
- `/api/compliance/reports` - Generate compliance reports

## Troubleshooting

### ModuleNotFoundError: No module named 'api'
**Solution**: Use `src.api.main:app` instead of `api.main:app`

### Port already in use
**Solution**: Change the port:
```bash
uvicorn src.api.main:app --reload --port 8001
```

### Import errors
**Solution**: Make sure you're in the project root directory and all dependencies are installed:
```bash
pip install -r requirements.txt
```

