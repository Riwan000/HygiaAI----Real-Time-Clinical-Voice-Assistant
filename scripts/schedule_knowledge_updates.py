#!/usr/bin/env python3
"""
Schedule Regular Knowledge Base Updates

Sets up automated scheduling for knowledge base updates using APScheduler.
Can run as a service or be integrated into the main application.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import logging
from datetime import datetime, timezone

from scripts.update_medical_knowledge_base import KnowledgeBaseUpdater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import APScheduler
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not available. Install with: pip install apscheduler")


def run_update():
    """Run knowledge base update"""
    try:
        updater = KnowledgeBaseUpdater()
        stats = updater.update_knowledge_base(force_update=False, check_changes=True)
        
        logger.info(f"Update completed: {stats['documents_updated']} updated, {stats['documents_new']} new")
        return stats
    except Exception as e:
        logger.error(f"Error during scheduled update: {e}")
        return None


def start_scheduler(
    update_interval_hours: int = 168,  # 7 days default
    run_immediately: bool = False,
    background: bool = True
):
    """
    Start scheduler for regular updates
    
    Args:
        update_interval_hours: Hours between updates (default: 168 = 7 days)
        run_immediately: Run update immediately on start
        background: Run scheduler in background (default: True)
    """
    if not APSCHEDULER_AVAILABLE:
        logger.error("APScheduler not available. Cannot start scheduler.")
        logger.info("Install with: pip install apscheduler")
        return None
    
    # Create scheduler
    if background:
        scheduler = BackgroundScheduler()
    else:
        scheduler = BlockingScheduler()
    
    # Add job
    trigger = IntervalTrigger(hours=update_interval_hours)
    scheduler.add_job(
        run_update,
        trigger=trigger,
        id='knowledge_base_update',
        name='Medical Knowledge Base Update',
        replace_existing=True
    )
    
    # Run immediately if requested
    if run_immediately:
        logger.info("Running initial update...")
        run_update()
    
    # Start scheduler
    scheduler.start()
    logger.info(f"Scheduler started. Updates will run every {update_interval_hours} hours.")
    
    return scheduler


def create_cron_schedule():
    """Create cron schedule configuration for manual setup"""
    cron_config = """
# Medical Knowledge Base Update Schedule
# Add this to your crontab (crontab -e on Linux/Mac)
# Or use Task Scheduler on Windows

# Update every Sunday at 2 AM
0 2 * * 0 cd /path/to/project && python scripts/update_medical_knowledge_base.py

# Or update every 7 days at 2 AM
0 2 */7 * * cd /path/to/project && python scripts/update_medical_knowledge_base.py

# Or update daily at 3 AM (for more frequent updates)
0 3 * * * cd /path/to/project && python scripts/update_medical_knowledge_base.py
"""
    
    cron_file = Path(project_root) / "docs" / "cron_schedule_example.txt"
    cron_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(cron_file, 'w') as f:
        f.write(cron_config)
    
    logger.info(f"Cron schedule example saved to: {cron_file}")
    return cron_file


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Schedule knowledge base updates")
    parser.add_argument(
        "--interval",
        type=int,
        default=168,
        help="Update interval in hours (default: 168 = 7 days)"
    )
    parser.add_argument(
        "--immediate",
        action="store_true",
        help="Run update immediately"
    )
    parser.add_argument(
        "--background",
        action="store_true",
        default=True,
        help="Run scheduler in background (default: True)"
    )
    parser.add_argument(
        "--cron",
        action="store_true",
        help="Generate cron schedule example"
    )
    
    args = parser.parse_args()
    
    if args.cron:
        create_cron_schedule()
        print("✅ Cron schedule example created")
        print("   See: docs/cron_schedule_example.txt")
    else:
        if APSCHEDULER_AVAILABLE:
            scheduler = start_scheduler(
                update_interval_hours=args.interval,
                run_immediately=args.immediate,
                background=args.background
            )
            
            if scheduler:
                if args.background:
                    print("✅ Scheduler running in background")
                    print("   Press Ctrl+C to stop")
                    try:
                        import time
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        scheduler.shutdown()
                        print("\n✅ Scheduler stopped")
                else:
                    print("✅ Scheduler running (blocking)")
                    print("   Press Ctrl+C to stop")
        else:
            print("⚠️  APScheduler not available")
            print("   Install with: pip install apscheduler")
            print("   Or use cron/Task Scheduler with update_medical_knowledge_base.py")

