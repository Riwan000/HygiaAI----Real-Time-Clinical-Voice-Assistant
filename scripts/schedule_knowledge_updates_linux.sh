#!/bin/bash
# Bash script to schedule knowledge base updates on Linux/Mac using cron
# Run this script to set up cron job

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UPDATE_SCRIPT="$SCRIPT_DIR/update_medical_knowledge_base.py"
PYTHON_EXE=$(which python3 || which python)

echo "Setting up Cron Job for Knowledge Base Updates"
echo "=============================================="
echo ""

# Check if cron job already exists
CRON_JOB="$PYTHON_EXE $UPDATE_SCRIPT"
CRON_ENTRY="0 2 * * 0 cd $PROJECT_ROOT && $CRON_JOB"

if crontab -l 2>/dev/null | grep -q "$UPDATE_SCRIPT"; then
    echo "⚠️  Cron job already exists for this script"
    echo ""
    echo "Current crontab entries:"
    crontab -l | grep "$UPDATE_SCRIPT"
    echo ""
    read -p "Do you want to add another entry? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 0
    fi
fi

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo ""
    echo "Cron Job Details:"
    echo "  Schedule: Every Sunday at 2:00 AM"
    echo "  Script: $UPDATE_SCRIPT"
    echo "  Working Directory: $PROJECT_ROOT"
    echo ""
    echo "To view your crontab:"
    echo "  crontab -l"
    echo ""
    echo "To edit your crontab:"
    echo "  crontab -e"
    echo ""
    echo "To remove this cron job:"
    echo "  crontab -l | grep -v '$UPDATE_SCRIPT' | crontab -"
    echo ""
else
    echo "❌ Error adding cron job"
    exit 1
fi

