import random
from datetime import datetime, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import get_all_users, get_user, update_user, get_pending_broadcasts, mark_broadcast_sent
from texts import (
    REMINDERS_MORNING, REMINDERS_DAY, REMINDERS_EVENING, REMINDERS_NIGHT,
    STREAK_LOST
)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def send_reminder(bot: Bot, period: str):
    users = await get_all_users()
    if period == "morning":
        pool = REMINDERS_MORNING
    elif period == "day":
        pool = REMINDERS_DAY
    elif period == "evening":
        pool = REMINDERS_EVENING
    else:
        pool = REMINDERS_NIGHT

    for u in users:
        try:
            text = random.choice(pool)
            await bot.send_message(u["user_id"], f"🦍 {text}")
        except Exception:
            pass


async def check_streaks(bot: Bot):
    users = await get_all_users()
    now = datetime.now()
    for u in users:
        user = await get_user(u["user_id"])
        if not user or not user.get("last_seen"):
            continue
        last = datetime.fromisoformat(user["last_seen"])
        delta = (now - last).total_seconds()
        if delta > 24 * 3600 and (user.get("streak") or 0) > 0:
            await update_user(u["user_id"], streak=0)
            try:
                await bot.send_message(
                    u["user_id"],
                    f"🦍 {random.choice(STREAK_LOST)}"
                )
            except Exception:
                pass


async def check_broadcasts(bot: Bot):
    pending = await get_pending_broadcasts()
    users = await get_all_users()
    for b in pending:
        for u in users:
            try:
                if b.get("photo_file_id"):
                    await bot.send_photo(
                        u["user_id"],
                        b["photo_file_id"],
                        caption=b["text"]
                    )
                else:
                    await bot.send_message(u["user_id"], b["text"])
            except Exception:
                pass
        await mark_broadcast_sent(b["id"])


def start_scheduler(bot: Bot):
    scheduler.add_job(send_reminder, "cron", hour=9, minute=0, args=[bot, "morning"])
    scheduler.add_job(send_reminder, "cron", hour=14, minute=0, args=[bot, "day"])
    scheduler.add_job(send_reminder, "cron", hour=19, minute=0, args=[bot, "evening"])
    scheduler.add_job(send_reminder, "cron", hour=22, minute=30, args=[bot, "night"])
    scheduler.add_job(check_streaks, "cron", minute=0)
    scheduler.add_job(check_broadcasts, "interval", minutes=1, args=[bot])
    scheduler.start()
