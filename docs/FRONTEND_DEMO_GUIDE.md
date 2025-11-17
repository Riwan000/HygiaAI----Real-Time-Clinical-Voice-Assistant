# HygiaAI Frontend Demo Guide

This guide provides step-by-step instructions for demonstrating the completed frontend features.

## 🎯 Completed Features Ready for Demo

### ✅ Task 79.6: SOAP Note Viewer
- Expand/collapse sections (S/O/A/P)
- Patient and clinician information display
- PDF export (backend API integration)
- Copy to clipboard
- Print functionality
- Manual editing with save/cancel
- Version history panel
- Annotations/comments support

### ✅ Task 79.7: Outbreak & Trend Visualization UI
- Interactive time-series trend charts
- Disease cluster bubble maps
- Clinic-level heatmaps
- Outbreak alert notifications
- Comprehensive filter system
- Chart export (PNG, SVG)

---

## 🚀 Quick Start for Demo

### Prerequisites

1. **Backend Server Running**
   ```bash
   python run_server.py
   ```
   Server should be accessible at `http://localhost:8000`

2. **Qdrant Running** (for analytics data)
   ```bash
   docker run -d -p 6334:6334 qdrant/qdrant
   ```

3. **Frontend Running**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend should be accessible at `http://localhost:3000` (or the port Vite assigns)

---

## 📋 Demo Scenarios

### Demo 1: SOAP Note Viewer

**Location:** Navigate to `/soap-notes` in the frontend

**Steps:**
1. The page shows a list of SOAP notes on the left
2. Click on any SOAP note to view details
3. **Demonstrate Features:**
   - Click section headers to expand/collapse (Subjective, Objective, Assessment, Plan)
   - Click "Expand All" / "Collapse All" button
   - Click edit icon (pencil) to enter edit mode
   - Make changes and click checkmark to save or X to cancel
   - Click copy icon to copy SOAP note to clipboard
   - Click download icon to export as PDF (requires backend running)
   - Click print icon to print the note
   - Toggle annotations panel (chat icon) to view/add comments
   - Toggle version history (clock icon) to see version tracking

**Expected Behavior:**
- All sections expand/collapse smoothly
- PDF export downloads a properly formatted PDF (matching backend format)
- Edit mode allows inline editing
- All actions provide visual feedback

**Backend Requirements:**
- FastAPI server running on port 8000
- `reportlab` installed for PDF generation
- Endpoint: `POST /api/v1/clinical_memory/soap/export/pdf`

---

### Demo 2: Analytics & Visualization Dashboard

**Location:** Navigate to `/analytics` in the frontend

**Steps:**
1. **Filters Section:**
   - Adjust time range (start/end dates)
   - Select region from dropdown
   - Select disease type
   - Choose time granularity (daily/weekly/monthly/seasonal)
   - Click "Reset Filters" to restore defaults

2. **Outbreak Alerts:**
   - If any outbreaks detected, they appear at the top
   - Color-coded by severity (red=high, yellow=medium, blue=low)
   - Shows disease name, case count, region, and recommendations
   - Click X to dismiss alerts

3. **Trend Chart:**
   - Interactive time-series chart showing cases over time
   - Hover over data points for detailed information
   - Zoom and pan using Plotly controls
   - Export as PNG or SVG using buttons

4. **Cluster Map:**
   - Bubble chart showing disease clusters
   - Size indicates case count
   - Color intensity shows cluster size
   - Click clusters for interaction (currently logs to console)
   - Export as PNG or SVG

5. **Heatmap:**
   - Clinic-level disease pattern visualization
   - Color intensity shows case counts
   - Hover for detailed information
   - Export as PNG or SVG

**Expected Behavior:**
- Charts load with real data from backend
- Filters update charts in real-time
- All charts are interactive (zoom, pan, hover)
- Export buttons download charts successfully

**Backend Requirements:**
- FastAPI server running
- Qdrant running with case data
- Endpoints:
  - `POST /api/v1/clinical_memory/temporal_clustering`
  - `POST /api/v1/clinical_memory/regional_analytics`

---

## 🧪 Testing with Mock Data

If backend is not available, you can test the UI with mock data by modifying the components temporarily.

### Mock SOAP Notes Data

Edit `frontend/src/pages/SOAPNotes.tsx` and update the `mockNotes` array with sample data:

```typescript
const mockNotes: SOAPNoteItem[] = [
  {
    id: '1',
    case_id: 'case_001',
    patient_id: 'patient_001',
    soap_note: {
      subjective: 'Patient presents with persistent cough for 2 weeks...',
      objective: 'Vital signs: BP 120/80, HR 88, Temp 37.5°C...',
      assessment: 'Acute bronchitis, likely viral etiology...',
      plan: '1. Symptomatic treatment with cough suppressants\n2. Rest and hydration...',
      metadata: {
        generated_at: new Date().toISOString(),
        entity_count: 12,
        transcript_length: 450,
      },
    },
    metadata: {
      age_group: 'adult',
      region: 'Rural Kerala',
      diagnosis: 'Acute Bronchitis',
      timestamp: new Date().toISOString(),
    },
    generated_at: new Date().toISOString(),
  },
  // Add more mock notes...
];
```

### Mock Analytics Data

Edit `frontend/src/pages/Analytics.tsx` and add mock data in the `fetchAnalyticsData` function:

```typescript
// Mock trend data
const mockTrendData: TrendDataPoint[] = [
  { date: '2024-01-01', value: 10, label: 'Fever' },
  { date: '2024-01-08', value: 15, label: 'Cough' },
  { date: '2024-01-15', value: 20, label: 'Fever' },
  // Add more...
];

// Mock cluster data
const mockClusters: ClusterData[] = [
  {
    cluster_id: 'cluster_1',
    time_window: '2024-01-01',
    case_count: 25,
    characteristics: {
      symptoms: ['fever', 'cough'],
      diagnoses: ['Acute Bronchitis'],
      locations: ['Rural Kerala'],
    },
  },
  // Add more...
];
```

---

## 📸 Screenshot Checklist

For documentation, capture screenshots of:

- [ ] SOAP Notes list view
- [ ] SOAP Note viewer with all sections expanded
- [ ] SOAP Note in edit mode
- [ ] PDF export (downloaded file)
- [ ] Analytics dashboard with filters
- [ ] Trend chart with hover tooltip
- [ ] Cluster map with multiple clusters
- [ ] Heatmap visualization
- [ ] Outbreak alert (high severity)
- [ ] Chart export (PNG/SVG)

---

## 🐛 Troubleshooting

### PDF Export Fails
- **Check:** Backend server is running (`python run_server.py`)
- **Check:** `reportlab` is installed (`pip install reportlab`)
- **Check:** Browser console for network errors
- **Check:** API endpoint is accessible: `http://localhost:8000/api/v1/clinical_memory/soap/export/pdf`

### Charts Not Loading
- **Check:** Backend server is running
- **Check:** Qdrant is running and accessible
- **Check:** Browser console for API errors
- **Check:** Network tab for failed requests

### No Data in Analytics
- **Check:** Qdrant has case data stored
- **Check:** Filters match available data
- **Check:** Time range includes data dates
- **Check:** Region filter matches stored regions

### Charts Not Interactive
- **Check:** Plotly.js is installed (`npm list plotly.js`)
- **Check:** Browser console for JavaScript errors
- **Check:** Chart container has proper dimensions

---

## 📝 Demo Script

### Opening Statement
"Today I'll demonstrate HygiaAI's clinical documentation and analytics features. This system helps rural doctors manage patient cases, generate structured SOAP notes, and identify disease trends and outbreaks."

### Part 1: SOAP Note Management (5 minutes)
1. Show SOAP notes list
2. Select a note and demonstrate viewer
3. Show expand/collapse functionality
4. Demonstrate editing capability
5. Export PDF and show formatted output
6. Show annotations and version history

### Part 2: Analytics Dashboard (5 minutes)
1. Show analytics dashboard
2. Adjust filters and show real-time updates
3. Demonstrate trend chart interactivity
4. Show cluster map and explain clustering
5. Show heatmap for clinic-level patterns
6. Demonstrate outbreak alerts
7. Export a chart

### Closing
"These features enable doctors to efficiently document cases, identify patterns, and respond quickly to outbreaks. The system integrates seamlessly with our Qdrant-based clinical memory system."

---

## 🎬 Video Demo Checklist

If creating a video demo:

- [ ] Start with overview of completed features
- [ ] Show SOAP note viewer with all features
- [ ] Demonstrate PDF export and show downloaded file
- [ ] Show analytics dashboard with real data
- [ ] Demonstrate filter interactions
- [ ] Show chart exports
- [ ] Highlight key features (expand/collapse, editing, alerts)
- [ ] End with summary of capabilities

---

## 📊 Sample Data for Demo

### Sample SOAP Notes
See `frontend/src/pages/SOAPNotes.tsx` for sample data structure.

### Sample Analytics Data
The system will fetch real data from Qdrant. To populate sample data:
1. Run ingestion scripts to add cases to Qdrant
2. Use the multimodal ingestion API
3. Or modify components to use mock data (see above)

---

## 🔗 Related Documentation

- [Frontend README](../frontend/README.md)
- [API Documentation](../README_API.md)
- [Quick Start Guide](../QUICK_START_GUIDE.md)

---

## ✅ Feature Completion Status

| Feature | Status | Demo Ready | Notes |
|---------|--------|------------|-------|
| SOAP Note Viewer | ✅ Complete | ✅ Yes | PDF export requires backend |
| Trend Charts | ✅ Complete | ✅ Yes | Requires backend + Qdrant data |
| Cluster Maps | ✅ Complete | ✅ Yes | Requires backend + Qdrant data |
| Heatmaps | ✅ Complete | ✅ Yes | Requires backend + Qdrant data |
| Outbreak Alerts | ✅ Complete | ✅ Yes | Requires backend + Qdrant data |
| Analytics Filters | ✅ Complete | ✅ Yes | Fully functional |
| Chart Export | ✅ Complete | ✅ Yes | PNG/SVG working |

---

**Last Updated:** 2024-11-17
**Version:** 1.0.0

