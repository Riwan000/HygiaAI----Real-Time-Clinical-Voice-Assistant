# Knowledge Base Regular Updates - Quick Setup Guide

## Overview

The medical knowledge base can be automatically updated on a regular schedule to ensure it always contains the latest medical guidelines and information.

## Quick Setup

### Option 1: Windows Task Scheduler (Recommended for Windows)

```powershell
# Run as Administrator
.\scripts\schedule_knowledge_updates_windows.ps1
```

This will:
- Create a scheduled task that runs every Sunday at 2:00 AM
- Automatically update the knowledge base
- Run in the background

**To customize:**
- Edit the script to change the schedule
- Or use Task Scheduler GUI to modify the task

### Option 2: Linux/Mac Cron

```bash
# Make script executable
chmod +x scripts/schedule_knowledge_updates_linux.sh

# Run the setup script
./scripts/schedule_knowledge_updates_linux.sh
```

This will:
- Add a cron job that runs every Sunday at 2:00 AM
- Automatically update the knowledge base

### Option 3: Python APScheduler (Cross-platform)

```bash
# Install APScheduler (optional)
pip install apscheduler

# Start scheduler
python scripts/schedule_knowledge_updates.py --interval 168 --immediate
```

This will:
- Run updates every 7 days (168 hours)
- Run immediately on start
- Continue running in background

## Manual Updates

### Check Update Status

```bash
python scripts/update_medical_knowledge_base.py
```

### Force Update

```bash
python scripts/update_medical_knowledge_base.py --force
```

### Set Custom Frequency

```bash
python scripts/update_medical_knowledge_base.py --frequency 14  # Every 14 days
```

## Update Frequency Recommendations

- **Weekly (7 days)**: Recommended for WHO/CDC guidelines
- **Bi-weekly (14 days)**: For medical references
- **Monthly (30 days)**: For curated content

## Verification

After setting up, verify it's working:

```bash
# Check update status
python -c "from scripts.update_medical_knowledge_base import KnowledgeBaseUpdater; updater = KnowledgeBaseUpdater(); print(updater.get_update_status())"
```

## Update Tracking

Updates are tracked in: `data/knowledge_base_updates.json`

This file contains:
- Last update timestamp
- Document versions (hashes)
- Update history
- Update statistics

## Troubleshooting

### Updates Not Running

1. **Check Qdrant**: Ensure Qdrant is running
2. **Check Logs**: Review error messages
3. **Manual Test**: Run `python scripts/update_medical_knowledge_base.py --force`

### Task Scheduler Not Working (Windows)

1. **Run as Admin**: Script must run as Administrator
2. **Check Task**: Open Task Scheduler and verify task exists
3. **Check Paths**: Ensure Python and script paths are correct

### Cron Not Working (Linux/Mac)

1. **Check Permissions**: Ensure script is executable
2. **Check Crontab**: Run `crontab -l` to verify entry
3. **Check Logs**: Check system logs for errors

## Integration with Application

You can integrate the updater into your FastAPI application:

```python
from scripts.update_medical_knowledge_base import KnowledgeBaseUpdater
from scripts.schedule_knowledge_updates import start_scheduler

# On application startup
@app.on_event("startup")
async def startup_event():
    # Start scheduled updates
    scheduler = start_scheduler(
        update_interval_hours=168,  # 7 days
        run_immediately=False,
        background=True
    )
```

## Monitoring

### Check Last Update

```python
from scripts.update_medical_knowledge_base import KnowledgeBaseUpdater

updater = KnowledgeBaseUpdater()
status = updater.get_update_status()

print(f"Last update: {status['last_update']}")
print(f"Days since update: {status['days_since_update']}")
print(f"Update needed: {status['update_needed']}")
```

### View Update History

The update history is stored in `data/knowledge_base_updates.json` and includes:
- Timestamp of each update
- Number of documents updated
- Number of new documents
- List of updated documents

## Best Practices

1. **Regular Monitoring**: Check update status weekly
2. **Backup**: Backup Qdrant before major updates
3. **Test First**: Test updates in development
4. **Monitor Logs**: Review update logs regularly
5. **Version Control**: Keep tracking file in version control (optional)

## Next Steps

1. ✅ Set up scheduled updates using one of the methods above
2. ✅ Verify updates are running correctly
3. ✅ Monitor update status regularly
4. ✅ Review update logs for any issues

