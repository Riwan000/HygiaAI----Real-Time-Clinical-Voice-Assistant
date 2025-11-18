# 🦠 Outbreak Detection Demo Guide

Complete guide for demonstrating HygiaAI's outbreak detection and notification features.

## 🎯 Overview

HygiaAI's outbreak detection system automatically identifies clusters of similar cases that may indicate a disease outbreak. It uses advanced clustering algorithms to detect patterns in:
- **Symptoms** (e.g., fever, cough, diarrhea)
- **Diagnoses** (e.g., pneumonia, gastroenteritis)
- **Geographic regions** (e.g., Kerala, Tamil Nadu)
- **Time windows** (recent cases vs. baseline)

---

## 🚀 Quick Start Demo

### Prerequisites

1. **Backend Server Running**
   ```bash
   python run_server.py
   ```
   Server should be accessible at `http://localhost:8000`

2. **Qdrant Running**
   ```bash
   docker run -d -p 6334:6334 qdrant/qdrant
   ```

3. **Frontend Running**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend should be accessible at `http://localhost:5173` (or assigned port)

4. **Sample Data Populated**
   - You need cases with similar symptoms/diagnoses in the same region
   - Cases should be within a recent time window (last 7-30 days)

---

## 📊 Step 1: Populate Outbreak Scenario Data

To demonstrate outbreak detection, you need multiple cases with:
- **Similar symptoms** (e.g., fever, cough, body aches)
- **Same or similar diagnoses** (e.g., "Dengue Fever", "Acute Gastroenteritis")
- **Same region** (e.g., "Kerala", "Tamil Nadu")
- **Recent timestamps** (within last 7-30 days)

### Option A: Use Existing COVID Patient Script

The `populate_covid_patients.py` script creates 50 COVID-19 patients with similar symptoms:

```bash
python scripts/populate_covid_patients.py
```

This creates:
- 50 COVID-19 patients with fever, cough, fatigue, etc.
- 30 patients with COVID-like symptoms (flu, pneumonia)
- Cases distributed across Indian regions
- Recent timestamps (within last 180 days)

### Option B: Create Custom Outbreak Scenario

Create a script to populate outbreak data:

```python
# Example: Create 10 cases with Dengue-like symptoms in Kerala
# All cases within last 7 days with similar symptoms
```

**Key Requirements:**
- Minimum 3 cases with similar symptoms/diagnoses
- Same region
- Recent timestamps (within detection window)
- Similar symptom patterns

---

## 🎬 Step 2: Access Outbreak Detection

### Method 1: Via Analytics Dashboard (Recommended)

1. **Navigate to Analytics Page**
   - Open frontend: `http://localhost:5173`
   - Click on **"Analytics"** in the navigation menu

2. **Select a Region**
   - In the filters section, select a region from the dropdown
   - Choose a region where you populated outbreak data (e.g., "Kerala", "Tamil Nadu")

3. **Set Time Range**
   - Set time range to include recent cases (last 7-30 days)
   - Outbreak detection analyzes cases within this window

4. **View Outbreak Alerts**
   - If outbreaks are detected, they appear at the top of the page
   - Alerts show:
     - **Disease/Symptom** name
     - **Severity level** (high/medium/low)
     - **Case count** (number of cases in cluster)
     - **Region** where outbreak detected
     - **Recommendations** for action

### Method 2: Via API Directly

You can also test outbreak detection via API:

```bash
# Basic outbreak detection (surge-based)
curl -X POST "http://localhost:8000/api/v1/visualization/outbreak/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "symptom_keywords": ["fever", "cough"],
    "time_window_days": 7,
    "threshold": 2.0
  }'

# Advanced outbreak detection (clustering-based)
curl -X POST "http://localhost:8000/api/v1/visualization/outbreak/detect-advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "dbscan",
    "time_window_days": 7,
    "min_cluster_size": 3,
    "threshold": 2.0,
    "symptom_keywords": ["fever", "cough", "body aches"],
    "region_filter": "Kerala"
  }'
```

---

## 🎯 Step 3: Demonstrate Features

### Feature 1: Outbreak Alert Display

**What to Show:**
- Outbreak alerts appear automatically when detected
- Color-coded by severity:
  - 🔴 **Red** = High severity (critical outbreak)
  - 🟡 **Yellow** = Medium severity (monitor closely)
  - 🔵 **Blue** = Low severity (informational)

**Demo Script:**
> "The system automatically detected a cluster of 8 cases with fever and cough in Kerala within the last 7 days. This represents a 3.2x increase compared to the baseline, triggering a medium-severity alert."

### Feature 2: Alert Details

**What to Show:**
- Click on an alert to see details:
  - Number of cases
  - Symptoms involved
  - Diagnoses
  - Time period
  - Recommendations

**Demo Script:**
> "Each alert provides actionable information. For this Dengue outbreak, the system recommends: 'Monitor closely, consider vector control measures, and alert public health authorities if cases exceed 10.'"

### Feature 3: Dismiss Alerts

**What to Show:**
- Click the "X" button on alerts to dismiss them
- Useful when alerts are resolved or false positives

**Demo Script:**
> "Clinicians can dismiss alerts once they've been addressed or if they're false positives. This helps keep the dashboard focused on active concerns."

### Feature 4: Filter by Region

**What to Show:**
- Change region filter to see different outbreaks
- Different regions may have different outbreak patterns

**Demo Script:**
> "By filtering to Tamil Nadu, we can see a different pattern - an increase in gastroenteritis cases. This regional filtering helps identify location-specific health trends."

---

## 🔧 Step 4: Understanding Detection Methods

HygiaAI supports multiple outbreak detection methods:

### 1. Surge-Based Detection (Default)
- Compares recent case counts to baseline
- Simple and fast
- Good for obvious spikes

### 2. DBSCAN Clustering
- Density-based clustering
- Identifies dense clusters of similar cases
- Good for irregular outbreak patterns

### 3. K-Means Clustering
- Centroid-based clustering
- Groups cases into predefined clusters
- Good for known outbreak types

### 4. Hierarchical Clustering
- Nested cluster structure
- Shows outbreak relationships
- Good for complex patterns

### 5. Anomaly Detection
- Statistical outlier detection
- Identifies unusual patterns
- Good for novel outbreaks

### 6. Spatial-Temporal Clustering
- Combines location and time
- Most sophisticated method
- Good for tracking spread

---

## 📋 Demo Checklist

### Before Demo:
- [ ] Backend server running
- [ ] Qdrant database running
- [ ] Frontend running
- [ ] Outbreak scenario data populated (minimum 3 similar cases)
- [ ] Cases have recent timestamps (within last 7-30 days)
- [ ] Cases are in the same region
- [ ] Cases have similar symptoms/diagnoses

### During Demo:
- [ ] Navigate to Analytics page
- [ ] Select region with outbreak data
- [ ] Set appropriate time range
- [ ] Show outbreak alerts appearing
- [ ] Explain alert details (severity, cases, recommendations)
- [ ] Demonstrate dismissing alerts
- [ ] Show filtering by different regions
- [ ] Explain detection methods (if technical audience)

---

## 💡 Tips for Effective Demo

### 1. **Prepare Realistic Data**
- Use actual disease names (Dengue, Gastroenteritis, etc.)
- Include realistic symptoms
- Use real Indian regions
- Set recent timestamps

### 2. **Explain the Value**
- Emphasize early detection
- Show how it helps rural clinics
- Highlight automated monitoring
- Connect to public health response

### 3. **Show Real-Time Detection**
- Demonstrate that alerts appear automatically
- Show how new cases trigger updates
- Explain continuous monitoring

### 4. **Address Common Questions**
- **Q: How accurate is it?**
  - A: Uses multiple algorithms, configurable thresholds
- **Q: Can it detect new diseases?**
  - A: Anomaly detection can identify unusual patterns
- **Q: What about false positives?**
  - A: Configurable thresholds, dismissible alerts, clinician review

---

## 🐛 Troubleshooting

### No Outbreak Alerts Appearing?

1. **Check Data Requirements:**
   - Minimum 3 cases with similar symptoms
   - Cases within detection time window (default: 7 days)
   - Cases in same region
   - Similar symptom patterns

2. **Check Detection Settings:**
   - Time window may be too short
   - Threshold may be too high
   - Min cluster size may be too large

3. **Check Region Filter:**
   - Make sure region filter matches data region
   - Try different regions

4. **Check Backend Logs:**
   ```bash
   # Check if cases are being retrieved
   # Check if clustering is running
   # Check for errors
   ```

### Alerts Not Updating?

- Refresh the page
- Check if new cases were added
- Verify timestamps are recent
- Check backend API response

### False Positives?

- Adjust detection threshold
- Increase min cluster size
- Use more specific symptom keywords
- Review case data quality

---

## 📚 Related Documentation

- [Analytics Dashboard Guide](FRONTEND_DEMO_GUIDE.md)
- [API Documentation](README_API.md)
- [Outbreak Detector Code](../src/outbreak/outbreak_detector.py)
- [Regional Analytics](../src/knowledge_intelligence/regional_analytics.py)

---

## 🎬 Sample Demo Script

### Opening (30 seconds)
> "HygiaAI includes automated outbreak detection that helps rural clinics identify disease clusters early. Let me show you how it works."

### Main Demo (2-3 minutes)
1. **Navigate to Analytics** (10 seconds)
   > "I'll open the Analytics dashboard where outbreak alerts appear automatically."

2. **Select Region** (10 seconds)
   > "I'll filter to Kerala, where we've seen several cases recently."

3. **Show Alerts** (30 seconds)
   > "Here we can see the system detected a cluster of 8 cases with fever and cough. The alert shows medium severity, meaning we should monitor closely."

4. **Explain Details** (30 seconds)
   > "Each alert includes the number of cases, symptoms involved, and recommendations. For this cluster, the system recommends monitoring and considering vector control measures."

5. **Show Filtering** (20 seconds)
   > "By changing the region filter, we can see different patterns. Tamil Nadu shows an increase in gastroenteritis cases."

6. **Demonstrate Dismissal** (10 seconds)
   > "Clinicians can dismiss alerts once addressed, keeping the dashboard focused on active concerns."

### Closing (20 seconds)
> "This automated detection helps rural clinics identify outbreaks early, enabling faster response and better public health outcomes. The system continuously monitors cases and alerts clinicians to potential issues."

---

## ✅ Success Criteria

A successful demo should show:
- ✅ Outbreak alerts appearing automatically
- ✅ Clear severity indicators
- ✅ Actionable recommendations
- ✅ Easy filtering by region
- ✅ Dismissible alerts
- ✅ Real-time updates

---

**Last Updated:** 2024
**Version:** 1.0

