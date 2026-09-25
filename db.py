import aiosqlite
import os
from datetime import datetime, timedelta
from config import DB_PATH

os.makedirs("data", exist_ok=True)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            age INTEGER,
            height INTEGER,
            weight REAL,
            meals INTEGER,
            water_l REAL,
            goal TEXT,
            body_type TEXT,
            streak INTEGER DEFAULT 0,
            last_seen TEXT,
            created_at TEXT,
            pro_until TEXT,
            lifetime INTEGER DEFAULT 0,
            trial_used INTEGER DEFAULT 0,
            workout_day INTEGER DEFAULT 0,
            total_exercises INTEGER DEFAULT 0,
            current_title TEXT,
            current_title_date TEXT,
            goal_text TEXT,
            subscribed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            water_l REAL DEFAULT 0,
            food_kcal INTEGER DEFAULT 0,
            workout_done INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS nofap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS strength (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exercise TEXT,
            weight REAL,
            date TEXT
        );

        CREATE TABLE IF NOT EXISTS weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            weight REAL,
            date TEXT
        );

        CREATE TABLE IF NOT EXISTS workouts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            exercises_done INTEGER,
            fatigue INTEGER,
            liked TEXT,
            hard TEXT
        );

        CREATE TABLE IF NOT EXISTS broadcast_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            photo_file_id TEXT,
            send_at TEXT,
            sent INTEGER DEFAULT 0
        );
        """)
        await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def create_user(user_id, username, first_name):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, created_at, last_seen) VALUES (?,?,?,?,?)",
            (user_id, username or "", first_name or "", now, now)
        )
        await db.commit()


async def update_user(user_id, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {fields} WHERE user_id=?", values)
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT user_id FROM users")
        return [dict(r) for r in await cur.fetchall()]


async def update_streak(user_id):
    user = await get_user(user_id)
    if not user:
        return 0, False
    now = datetime.now()
    last = user.get("last_seen")
    streak = user.get("streak") or 0
    lost = False
    if last:
        last_dt = datetime.fromisoformat(last)
        delta = (now - last_dt).total_seconds()
        if delta > 24 * 3600:
            streak = 0
            lost = True
        elif delta < 24 * 3600 and last_dt.date() != now.date():
            streak += 1
    else:
        streak = 1
    await update_user(user_id, streak=streak, last_seen=now.isoformat())
    return streak, lost


async def add_tracker(user_id, date, water_l=0, food_kcal=0, workout_done=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM tracker WHERE user_id=? AND date=?",
            (user_id, date)
        )
        row = await cur.fetchone()
        if row:
            if water_l:
                await db.execute("UPDATE tracker SET water_l=water_l+? WHERE id=?", (water_l, row[0]))
            if food_kcal:
                await db.execute("UPDATE tracker SET food_kcal=food_kcal+? WHERE id=?", (food_kcal, row[0]))
            if workout_done is not None:
                await db.execute("UPDATE tracker SET workout_done=? WHERE id=?", (1 if workout_done else 0, row[0]))
        else:
            await db.execute(
                "INSERT INTO tracker (user_id, date, water_l, food_kcal, workout_done) VALUES (?,?,?,?,?)",
                (user_id, date, water_l, food_kcal, 1 if workout_done else 0)
            )
        await db.commit()


async def get_week_tracker(user_id):
    days = []
    today = datetime.now().date()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            cur = await db.execute(
                "SELECT water_l, food_kcal FROM tracker WHERE user_id=? AND date=?",
                (user_id, d)
            )
            row = await cur.fetchone()
            days.append(dict(row) if row else {"water_l": 0, "food_kcal": 0})
    return days


async def set_nofap(user_id, date, count):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, count FROM nofap WHERE user_id=? AND date=?",
            (user_id, date)
        )
        row = await cur.fetchone()
        if row:
            await db.execute("UPDATE nofap SET count=count+? WHERE id=?", (count, row[0]))
        else:
            await db.execute(
                "INSERT INTO nofap (user_id, date, count) VALUES (?,?,?)",
                (user_id, date, count)
            )
        await db.commit()


async def get_nofap_week(user_id):
    days = []
    today = datetime.now().date()
    async with aiosqlite.connect(DB_PATH) as db:
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            cur = await db.execute(
                "SELECT count FROM nofap WHERE user_id=? AND date=?",
                (user_id, d)
            )
            row = await cur.fetchone()
            days.append(row[0] if row else 0)
    return days


async def get_nofap_total(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COALESCE(SUM(count),0) FROM nofap WHERE user_id=?",
            (user_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else 0


async def save_strength(user_id, exercise, weight):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO strength (user_id, exercise, weight, date) VALUES (?,?,?,?)",
            (user_id, exercise, weight, datetime.now().date().isoformat())
        )
        await db.commit()


async def save_weight(user_id, weight):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO weights (user_id, weight, date) VALUES (?,?,?)",
            (user_id, weight, datetime.now().date().isoformat())
        )
        await db.commit()


async def save_workout_log(user_id, exercises_done, fatigue, liked, hard):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO workouts_log (user_id, date, exercises_done, fatigue, liked, hard) VALUES (?,?,?,?,?,?)",
            (user_id, datetime.now().date().isoformat(), exercises_done, fatigue, liked, hard)
        )
        await db.commit()


async def save_template(text):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO broadcast_templates (text, created_at) VALUES (?,?)",
            (text, datetime.now().isoformat())
        )
        # оставляем только 3 последних
        await db.execute("""
            DELETE FROM broadcast_templates
            WHERE id NOT IN (SELECT id FROM broadcast_templates ORDER BY id DESC LIMIT 3)
        """)
        await db.commit()


async def get_templates():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM broadcast_templates ORDER BY id DESC")
        return [dict(r) for r in await cur.fetchall()]


async def schedule_broadcast(text, photo_file_id, send_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO scheduled_broadcasts (text, photo_file_id, send_at) VALUES (?,?,?)",
            (text, photo_file_id, send_at)
        )
        await db.commit()


async def get_pending_broadcasts():
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM scheduled_broadcasts WHERE sent=0 AND send_at<=?",
            (now,)
        )
        return [dict(r) for r in await cur.fetchall()]


async def mark_broadcast_sent(bid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE scheduled_broadcasts SET sent=1 WHERE id=?", (bid,))
        await db.commit()


async def get_leagues(period="day"):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT u.first_name, u.username, u.streak, u.total_exercises
            FROM users u
            ORDER BY u.streak DESC, u.total_exercises DESC
            LIMIT 10
        """)
        return [dict(r) for r in await cur.fetchall()]


async def get_shame_today():
    today = datetime.now().date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT u.first_name, u.username, t.water_l, t.food_kcal, t.workout_done
            FROM users u
            LEFT JOIN tracker t ON t.user_id=u.user_id AND t.date=?
            WHERE COALESCE(t.workout_done,0)=0
            ORDER BY COALESCE(t.water_l,0) ASC, COALESCE(t.food_kcal,0) ASC
            LIMIT 3
        """, (today,))
        return [dict(r) for r in await cur.fetchall()]
