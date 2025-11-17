# Medical Knowledge Base - Regular Updates

## Overview

The medical knowledge base is designed to be updated regularly to ensure it contains the latest medical guidelines, treatment protocols, and reference information from authoritative sources.

## Update System

### Automatic Update Detection

The system tracks:
- **Last update timestamp**: When the knowledge base was last updated
- **Document versions**: Hash-based change detection for each document
- **Update frequency**: Configurable (default: 7 days)
- **Update history**: Last 50 update records

### Update Process

1. **Change Detection**: Compares document hashes to detect changes
2. **Selective Updates**: Only updates documents that have changed
3. **Version Tracking**: Maintains version history for each document
4. **Idempotent**: Safe to run multiple times

## Usage

### Manual Update

```bash
# Check status and update if needed
python scripts/update_medical_knowledge_base.py

# Force update regardless of frequency
python scripts/update_medical_knowledge_base.py --force

# Set custom update frequency (days)
python scripts/update_medical_knowledge_base.py --frequency 14
```

### Scheduled Updates

#### Option 1: Using APScheduler (Python)

```bash
# Start scheduler (updates every 7 days)
python scripts/schedule_knowledge_updates.py --interval 168

# Run update immediately and start scheduler
python scripts/schedule_knowledge_updates.py --immediate --interval 168
```

#### Option 2: Using Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add line (updates every Sunday at 2 AM)
0 2 * * 0 cd /path/to/project && python scripts/update_medical_knowledge_base.py
```

#### Option 3: Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Weekly, Sunday, 2:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `scripts/update_medical_knowledge_base.py`
7. Start in: Project directory path

### Programmatic Update

```python
from scripts.update_medical_knowledge_base import KnowledgeBaseUpdater

# Create updater
updater = KnowledgeBaseUpdater(update_frequency_days=7)

# Check status
status = updater.get_update_status()
print(f"Last update: {status['last_update']}")
print(f"Update needed: {status['update_needed']}")

# Perform update
stats = updater.update_knowledge_base(force_update=False)
print(f"Updated: {stats['documents_updated']}, New: {stats['documents_new']}")
```

## Update Tracking

### Tracking File

Updates are tracked in: `data/knowledge_base_updates.json`

```json
{
  "last_update": "2025-01-XXT00:00:00+00:00",
  "update_frequency_days": 7,
  "update_history": [
    {
      "timestamp": "2025-01-XXT00:00:00+00:00",
      "documents_checked": 9,
      "documents_updated": 2,
      "documents_new": 0,
      "documents_unchanged": 7
    }
  ],
  "document_versions": {
    "who_hypertension-management": "abc123...",
    "cdc_flu/treatment": "def456...",
    ...
  }
}
```

### Update Statistics

Each update records:
- **Timestamp**: When the update ran
- **Documents checked**: Total documents processed
- **Documents updated**: Documents that changed
- **Documents new**: New documents added
- **Documents unchanged**: Documents without changes
- **Errors**: Number of errors encountered
- **Updated documents**: List of updated document details

## Update Frequency Recommendations

### Recommended Frequencies

- **High Priority Sources** (WHO, CDC): **Weekly** (7 days)
- **Medical References**: **Bi-weekly** (14 days)
- **Curated Content**: **Monthly** (30 days) or as needed

### Current Default

- **Default frequency**: 7 days
- **Can be customized**: Via `--frequency` flag or in code

## Monitoring Updates

### Check Update Status

```python
from scripts.update_medical_knowledge_base import KnowledgeBaseUpdater

updater = KnowledgeBaseUpdater()
status = updater.get_update_status()

print(f"Last update: {status['last_update']}")
print(f"Days since update: {status['days_since_update']}")
print(f"Update needed: {status['update_needed']}")
print(f"Total documents: {status['total_documents']}")
```

### View Update History

```python
import json
from pathlib import Path

tracking_file = Path("data/knowledge_base_updates.json")
if tracking_file.exists():
    with open(tracking_file) as f:
        history = json.load(f)
        print("Recent updates:")
        for update in history["update_history"][-5:]:
            print(f"  {update['timestamp']}: {update['documents_updated']} updated")
```

## Integration with Application

### As a Service

```python
# In your main application
from scripts.schedule_knowledge_updates import start_scheduler

# Start scheduler on application startup
scheduler = start_scheduler(
    update_interval_hours=168,  # 7 days
    run_immediately=False,
    background=True
)
```

### As a Background Task

```python
# Using FastAPI background tasks
from fastapi import BackgroundTasks
from scripts.update_medical_knowledge_base import KnowledgeBaseUpdater

@app.on_event("startup")
async def startup_event():
    # Schedule regular updates
    scheduler = start_scheduler(update_interval_hours=168)
```

## Notification System

### Email Notifications (Future Enhancement)

The update system can be extended to send email notifications:
- When updates are completed
- When new documents are added
- When errors occur
- Weekly update summaries

### Logging

All updates are logged:
- **INFO**: Normal update operations
- **WARNING**: Skipped updates, unchanged documents
- **ERROR**: Update failures, errors

Check logs for:
```bash
# View recent update logs
tail -f logs/knowledge_base_updates.log
```

## Troubleshooting

### Update Not Running

1. **Check Qdrant**: Ensure Qdrant is running
2. **Check Frequency**: Verify update frequency settings
3. **Check Logs**: Review error logs
4. **Manual Test**: Run `python scripts/update_medical_knowledge_base.py --force`

### Documents Not Updating

1. **Check Hashes**: Documents only update if content changed
2. **Force Update**: Use `--force` flag to update all documents
3. **Check Sources**: Verify source URLs are accessible
4. **Review Logs**: Check for errors in update process

### Scheduler Not Working

1. **Install APScheduler**: `pip install apscheduler`
2. **Check Permissions**: Ensure script has execution permissions
3. **Check Paths**: Verify all paths are correct
4. **Use Cron/Task Scheduler**: Alternative scheduling method

## Best Practices

1. **Regular Monitoring**: Check update status weekly
2. **Backup Before Updates**: Backup Qdrant before major updates
3. **Test Updates**: Test in development before production
4. **Monitor Logs**: Review update logs regularly
5. **Version Control**: Keep tracking file in version control (optional)

## Future Enhancements

- [ ] Email notification system
- [ ] Webhook notifications
- [ ] Update dashboard/UI
- [ ] Automatic source discovery
- [ ] Multi-source aggregation
- [ ] Conflict resolution for conflicting guidelines
- [ ] Update rollback capability

