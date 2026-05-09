"""
APScheduler — scheduled background tasks.

Jobs:
  - Daily debriefs: runs every minute, checks per-user debrief time
  - Weekly summary: every Monday 8 AM WAT
  - Mono pending reminders: every 15 minutes for unlinked accounts
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

scheduler = AsyncIOScheduler()


def start_scheduler():
    # Daily debriefs — runs every minute, checks per user
    scheduler.add_job(
        run_daily_debriefs,
        CronTrigger(minute="*"),
        id="daily_debriefs",
        replace_existing=True,
    )

    # Weekly summary — every Monday 8am WAT
    scheduler.add_job(
        run_weekly_summaries,
        CronTrigger(day_of_week="mon", hour=8),
        id="weekly_summaries",
        replace_existing=True,
    )

    # Mono pending reminders — every 15 minutes
    scheduler.add_job(
        send_mono_reminders,
        CronTrigger(minute="*/15"),
        id="mono_reminders",
        replace_existing=True,
    )

    scheduler.start()
    print("Scheduler started")


async def run_daily_debriefs():
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.user import User
    from app.services.notifier import send_daily_debrief

    now_time = datetime.now().strftime("%H:%M")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.onboarding_complete == True)
        )
        users = result.scalars().all()

        for user in users:
            user_time = str(user.daily_debrief_time)[:5]
            if user_time == now_time:
                await send_daily_debrief(user, db)


async def run_weekly_summaries():
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.user import User
    from app.services.notifier import send_daily_debrief

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.onboarding_complete == True)
        )
        users = result.scalars().all()
        for user in users:
            await send_daily_debrief(user, db)


async def send_mono_reminders():
    from app.redis import redis
    from app.services.twilio_client import send_cta_button
    from app.services.mono import generate_connect_url
    from app.redis import get_session

    keys = await redis.keys("mono_pending:*")
    if not keys:
        return
    for key in keys:
        whatsapp_no = key.replace("mono_pending:", "")
        session = await get_session(whatsapp_no)
        user_id = session.get("pending_data", {}).get("user_id")
        if user_id:
            connect_url = await generate_connect_url(user_id)
            await send_cta_button(
                whatsapp_no,
                "⏰ Your bank account isn't connected yet.\n"
                "Tap below to finish — it takes 2 minutes:",
                "Connect My Bank",
                connect_url,
            )
