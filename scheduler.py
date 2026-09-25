import random
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import (
    get_all_users, get_user, update_user,
    get_pending_broadcasts, mark_broadcast_sent
)
from texts import (
    REMINDERS_MORNING, REMINDERS_DAY, REMINDERS_EVENING, REMINDERS_NIGHT,
    STREAK_LOST
)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# Глобальная ссылка на бота — установим из main.py
_bot: Bot = None


def set_bot(bot: Bot):
    global _bot
    _bot = bot


async def send_reminder(period: str):
    if not _bot:
        return
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
            await _bot.send_message(u["user_id"], f"🦍 {text}")
        except Exception:
            pass


async def check_streaks():
    if not _bot:
        return
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
                await _bot.send_message(
                    u["user_id"],
                    f"🦍 {random.choice(STREAK_LOST)}"
                )
            except Exception:
                pass


async def check_broadcasts():
    if not _bot:
        return
    pending = await get_pending_broadcasts()
    users = await get_all_users()
    for b in pending:
        for u in users:
            try:
                if b.get("photo_file_id"):
                    await _bot.send_photo(
                        u["user_id"],
                        b["photo_file_id"],
                        caption=b["text"]
                    )
                else:
                    await _bot.send_message(u["user_id"], b["text"])
            except Exception:
                pass
        await mark_broadcast_sent(b["id"])


def start_scheduler(bot: Bot):
    set_bot(bot)
    scheduler.add_job(send_reminder, "cron", hour=9, minute=0, kwargs={"period": "morning"})
    scheduler.add_job(send_reminder, "cron", hour=14, minute=0, kwargs={"period": "day"})
    scheduler.add_job(send_reminder, "cron", hour=19, minute=0, kwargs={"period": "evening"})
    scheduler.add_job(send_reminder, "cron", hour=22, minute=30, kwargs={"period": "night"})
    scheduler.add_job(check_streaks, "cron", minute=0)
    scheduler.add_job(check_broadcasts, "interval", minutes=1)
    scheduler.start()
