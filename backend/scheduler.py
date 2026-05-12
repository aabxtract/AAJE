"""
Scheduler — runs background jobs on a schedule.

Current jobs:
  - Daily debrief: Sends financial summaries to all traders at 8PM WAT (19:00 UTC)
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _send_debriefs():
    """Wrapper that imports and runs the debrief sender."""
    try:
        from app.agents.insight_agent import send_daily_debrief_to_all

        await send_daily_debrief_to_all()
        logger.info("Daily debriefs sent successfully")
    except Exception:
        logger.exception("Daily debrief job failed")


def start_scheduler():
    """Start the APScheduler with all registered jobs."""
    # Daily debrief at 8PM WAT (7PM UTC)
    scheduler.add_job(
        _send_debriefs,
        "cron",
        hour=19,
        minute=0,
        id="daily_debrief",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with daily debrief at 8PM WAT")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
