import asyncio
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery

from config import (
    BOT_TOKEN, ADMIN_ID, CHANNEL_ID, CHANNEL_URL,
    PRICE_PRO, PRICE_LIFETIME
)
from db import (
    init_db, create_user, get_user, update_user, get_all_users,
    update_streak, add_tracker, get_week_tracker,
    set_nofap, get_nofap_week, get_nofap_total,
    save_strength, save_weight, save_workout_log,
    save_template, get_templates, schedule_broadcast,
    get_leagues, get_shame_today
)
from keyboards import (
    main_menu, kb_goal, kb_unknown, kb_after_help, kb_subscribe,
    kb_tracker, kb_workout_place, kb_workout_inventory, kb_workout_pro,
    kb_start_workout, kb_exercise_done, kb_fatigue,
    kb_food_lessons, kb_admin, kb_back
)
from states import (
    Reg, TrackerState, WorkoutState, NofapState,
    StrengthState, WeightState, GoalState, AdminState
)
from texts import (
    GREET, ASK_AGE, ASK_HEIGHT, ASK_WEIGHT, ASK_MEALS, ASK_MEALS_HELP,
    ASK_WATER, ASK_WATER_HELP, ASK_GOAL, BODY_PHRASES,
    SUBSCRIBE_ASK, SUBSCRIBE_FAIL, HELP, FOOD_LESSONS, TITLES
)
from charts import (
    draw_circle, draw_week_chart, draw_profile_progress,
    draw_nofap_stats, draw_strength_card, draw_title_card
)
from payments import send_pro_invoice, send_lifetime_invoice, send_program_invoice
from scheduler import start_scheduler
import os

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ─────────── ХЕЛПЕРЫ ───────────
def is_admin(uid):
    return uid == ADMIN_ID


def body_type(weight, height):
    bmi = weight / ((height / 100) ** 2)
    if bmi < 18.5:
        return "ectomorph"
    if bmi < 25:
        return "mesomorph"
    return "endomorph"


async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return True


def norm_water(weight):
    return round(weight * 0.03, 1)


def norm_kcal(weight, goal):
    if goal and "набрать" in goal.lower():
        return int(weight * 33)
    if goal and "похудеть" in goal.lower():
        return int(weight * 26)
    return int(weight * 30)


def safe_image(path):
    """Возвращает BufferedInputFile или None, если файла нет."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return BufferedInputFile(f.read(), filename=os.path.basename(path))
    except Exception:
        pass
    return None


async def send_photo_or_text(message, img_path, caption, reply_markup=None):
    """Шлёт фото если есть, иначе текст."""
    photo = safe_image(img_path)
    if photo:
        try:
            await message.answer_photo(photo, caption=caption, reply_markup=reply_markup)
            return
        except Exception:
            pass
    await message.answer(caption, reply_markup=reply_markup)


# ─────────── START ───────────
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    await create_user(uid, message.from_user.username, message.from_user.first_name)
    await state.clear()
    await message.answer(GREET, reply_markup=kb_goal())
    await state.set_state(Reg.age)


# ─────────── РЕГИСТРАЦИЯ ───────────
@dp.message(Reg.age)
async def reg_age(message: types.Message, state: FSMContext):
    if message.text in ("💪 Набрать массу", "🔥 Похудеть", "⚡ Рельеф", "🐗 Просто стать сильнее"):
        await state.update_data(goal=message.text)
        await message.answer(ASK_AGE, reply_markup=kb_unknown())
        return
    if message.text == "Не знаю 🤷":
        await state.update_data(age=20)
    else:
        try:
            await state.update_data(age=int(message.text.strip()))
        except Exception:
            await message.answer("Бро, цифрой. Просто число.")
            return
    await message.answer(ASK_HEIGHT, reply_markup=kb_unknown())
    await state.set_state(Reg.height)


@dp.message(Reg.height)
async def reg_height(message: types.Message, state: FSMContext):
    if message.text == "Не знаю 🤷":
        await state.update_data(height=175)
    else:
        try:
            await state.update_data(height=int(message.text.strip()))
        except Exception:
            await message.answer("Цифрой, бро.")
            return
    await message.answer(ASK_WEIGHT, reply_markup=kb_unknown())
    await state.set_state(Reg.weight)


@dp.message(Reg.weight)
async def reg_weight(message: types.Message, state: FSMContext):
    if message.text == "Не знаю 🤷":
        await state.update_data(weight=70.0)
    else:
        try:
            await state.update_data(weight=float(message.text.replace(",", ".").strip()))
        except Exception:
            await message.answer("Цифрой, бро. Например 70")
            return
    await message.answer(ASK_MEALS, reply_markup=kb_unknown())
    await state.set_state(Reg.meals)


@dp.message(Reg.meals)
async def reg_meals(message: types.Message, state: FSMContext):
    if message.text == "Не знаю 🤷":
        await message.answer(ASK_MEALS_HELP, reply_markup=kb_after_help())
        return
    if message.text == "Понял, написать число":
        await message.answer("Напиши число приёмов пищи в день.")
        return
    try:
        meals = int(message.text.strip())
        await state.update_data(meals=meals)
    except Exception:
        await message.answer("Числом, бро.")
        return
    await message.answer(ASK_WATER, reply_markup=kb_unknown())
    await state.set_state(Reg.water)


@dp.message(Reg.water)
async def reg_water(message: types.Message, state: FSMContext):
    if message.text == "Не знаю 🤷":
        await message.answer(ASK_WATER_HELP, reply_markup=kb_after_help())
        return
    if message.text == "Понял, написать число":
        await message.answer("Напиши сколько литров воды пьёшь в день. Например 2.0")
        return
    try:
        water = float(message.text.replace(",", ".").strip())
        await state.update_data(water=water)
    except Exception:
        await message.answer("Числом, бро. Например 2.0")
        return

    data = await state.get_data()
    uid = message.from_user.id
    bt = body_type(data["weight"], data["height"])
    await update_user(
        uid,
        age=data["age"], height=data["height"], weight=data["weight"],
        meals=data["meals"], water_l=data["water"],
        goal=data.get("goal", "Просто стать сильнее"), body_type=bt,
        streak=1, last_seen=datetime.now().isoformat()
    )
    await message.answer(
        f"🦍 {random.choice(BODY_PHRASES[bt])}\n\n"
        f"📊 Твои данные:\n"
        f"Возраст: {data['age']}\n"
        f"Рост: {data['height']} см\n"
        f"Вес: {data['weight']} кг\n"
        f"Приёмов пищи: {data['meals']}\n"
        f"Вода: {data['water']} л\n"
        f"Цель: {data.get('goal', '-')}"
    )
    await message.answer(SUBSCRIBE_ASK, reply_markup=kb_subscribe())
    await state.set_state(Reg.subscribe)


@dp.callback_query(F.data == "check_sub")
async def check_sub_cb(cb: CallbackQuery, state: FSMContext):
    ok = await check_sub(cb.from_user.id)
    if ok:
        await cb.message.answer(
            "🦍 <b>Красавчик, бро.</b> Теперь мы в одной команде.\n"
            "Держи меню 👇",
            reply_markup=main_menu(is_admin(cb.from_user.id))
        )
        await state.clear()
        await cb.answer()
    else:
        await cb.message.answer(SUBSCRIBE_FAIL, reply_markup=kb_subscribe())
        await cb.answer("Не подписан", show_alert=True)


# ─────────── ТРЕКЕР ───────────
@dp.message(F.text == "🍗 Трекер")
async def tracker_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🦍 <b>Трекер, бро.</b> Записывай честно.", reply_markup=kb_tracker())


@dp.message(F.text == "💧 Вода")
async def water_tracker(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    norm = norm_water(user["weight"] or 70)
    week = await get_week_tracker(message.from_user.id)
    today = week[-1]["water_l"] if week else 0
    percent = int(today / norm * 100) if norm else 0
    buf = draw_circle(percent, "Вода", f"{today:.1f} / {norm} л", color="#2196F3")
    await message.answer_photo(
        BufferedInputFile(buf.read(), filename="water.png"),
        caption=(
            f"💧 <b>Водный баланс</b>\n"
            f"Сегодня: <b>{percent}%</b>\n\n"
            f"Сколько выпил? Напиши в литрах (например 0.5)"
        )
    )
    await state.set_state(TrackerState.water)


@dp.message(TrackerState.water)
async def water_add(message: types.Message, state: FSMContext):
    try:
        val = float(message.text.replace(",", ".").strip())
    except Exception:
        await message.answer("Числом, бро.")
        return
    today = datetime.now().date().isoformat()
    await add_tracker(message.from_user.id, today, water_l=val)
    await message.answer(f"✅ +{val} л воды. Красавчик, бро 💧")
    await state.clear()


@dp.message(F.text == "🍎 Еда")
async def food_tracker(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    norm = norm_kcal(user["weight"] or 70, user.get("goal") or "")
    week = await get_week_tracker(message.from_user.id)
    today = week[-1]["food_kcal"] if week else 0
    percent = int(today / norm * 100) if norm else 0
    buf = draw_circle(percent, "Еда", f"{today} / {norm} ккал", color="#4CAF50")
    await message.answer_photo(
        BufferedInputFile(buf.read(), filename="food.png"),
        caption=(
            f"🍎 <b>Питание</b>\n"
            f"Сегодня: <b>{percent}%</b>\n\n"
            f"Сколько съел? Напиши в ккал (примерно, например 500)"
        )
    )
    await state.set_state(TrackerState.food)


@dp.message(TrackerState.food)
async def food_add(message: types.Message, state: FSMContext):
    try:
        val = int(float(message.text.replace(",", ".").strip()))
    except Exception:
        await message.answer("Числом, бро.")
        return
    today = datetime.now().date().isoformat()
    await add_tracker(message.from_user.id, today, food_kcal=val)
    await message.answer(f"✅ +{val} ккал. Так держать 🍗")
    await state.clear()


@dp.message(F.text == "📅 За неделю")
async def week_chart(message: types.Message):
    user = await get_user(message.from_user.id)
    n_water = norm_water(user["weight"] or 70)
    n_food = norm_kcal(user["weight"] or 70, user.get("goal") or "")
    week = await get_week_tracker(message.from_user.id)
    water_pct = [int(d["water_l"] / n_water * 100) if n_water else 0 for d in week]
    food_pct = [int(d["food_kcal"] / n_food * 100) if n_food else 0 for d in week]
    buf = draw_week_chart(water_pct, food_pct)
    await message.answer_photo(
        BufferedInputFile(buf.read(), filename="week.png"),
        caption="📊 <b>Твоя неделя, бро</b>"
    )


# ─────────── ПРОФИЛЬ ───────────
@dp.message(F.text == "📊 Профиль")
async def profile(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала /start, бро.")
        return
    created = datetime.fromisoformat(user["created_at"])
    days = (datetime.now() - created).days + 1
    values = [min(100, (i + 1) * 5) for i in range(min(days, 10))]
    buf = draw_profile_progress(values, days, user.get("streak") or 0)
    title = user.get("current_title") or "-"
    await message.answer_photo(
        BufferedInputFile(buf.read(), filename="profile.png"),
        caption=(
            f"🦍 <b>{user['first_name'] or 'бро'}, твой профиль:</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📅 В Билли: {days} дней\n"
            f"🔥 Серия: <b>{user.get('streak') or 0}</b>\n"
            f"🏅 Титул дня: <b>{title}</b>\n"
            f"⚖️ Вес: {user.get('weight') or '-'} кг\n"
            f"📏 Рост: {user.get('height') or '-'} см\n"
            f"🎯 Цель: {user.get('goal') or '-'}\n"
            f"🍗 Приёмов пищи: {user.get('meals') or '-'}\n"
            f"💧 Вода: {user.get('water_l') or '-'} л\n"
            f"━━━━━━━━━━━━━━━"
        )
    )


# ─────────── ЦЕЛЬ ───────────
@dp.message(F.text == "🎯 Цель")
async def goal_cmd(message: types.Message, state: FSMContext):
    await message.answer("🦍 Напиши свою цель, бро. Я буду напоминать, когда ты ленишься.")
    await state.set_state(GoalState.text)


@dp.message(GoalState.text)
async def goal_set(message: types.Message, state: FSMContext):
    await update_user(message.from_user.id, goal_text=message.text)
    await message.answer("✅ Запомнил. Буду трясти тебя. 🦍")
    await state.clear()


# ─────────── ЛИГИ ───────────
@dp.message(F.text == "🏆 Лиги")
async def leagues(message: types.Message):
    top = await get_leagues()
    text = "🏆 <b>Лиги, бро:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(top[:10]):
        m = medals[i] if i < 3 else f"{i+1}."
        name = u["first_name"] or u["username"] or "Аноним"
        text += f"{m} {name} — 🔥{u['streak'] or 0} | 💪{u['total_exercises'] or 0}\n"
    text += "\n💎 Алмаз | 🥇 Золото | 🥈 Серебро | 🥉 Бронза"
    await message.answer(text)


# ─────────── ПОМОЩЬ ───────────
@dp.message(F.text == "🆘 Помощь")
async def help_cmd(message: types.Message):
    await message.answer(HELP)


# ─────────── ПИТАНИЕ ───────────
@dp.message(F.text == "🍎 Питание")
async def food_menu(message: types.Message):
    await send_lesson(message, 0)


async def send_lesson(message, idx):
    user = await get_user(message.from_user.id)
    has_pro = False
    if user and user.get("pro_until"):
        try:
            has_pro = datetime.fromisoformat(user["pro_until"]) > datetime.now()
        except Exception:
            pass
    if idx > 0 and not has_pro:
        await message.answer(
            "🚫 <b>Это PRO-урок, бро.</b>\n\n"
            "199 ⭐ в месяц — и вся база знаний твоя.\n"
            "Это как 2 шаурмы, только работает дольше. 😏",
            reply_markup=kb_workout_pro()
        )
        return
    lesson = FOOD_LESSONS[idx]
    await send_photo_or_text(
        message,
        "images/food_lesson.png",
        lesson["text"],
        reply_markup=kb_food_lessons(idx, len(FOOD_LESSONS), has_pro)
    )


@dp.callback_query(F.data.startswith("food_"))
async def food_nav(cb: CallbackQuery):
    parts = cb.data.split("_")
    if parts[1] == "locked":
        await cb.answer("PRO нужен, бро 🚫", show_alert=True)
        return
    idx = int(parts[1])
    if idx < 0 or idx >= len(FOOD_LESSONS):
        await cb.answer("Край, бро")
        return
    try:
        await cb.message.delete()
    except Exception:
        pass
    await send_lesson(cb.message, idx)
    await cb.answer()


# ─────────── ЗНАНИЯ ───────────
@dp.message(F.text == "📚 Знания")
async def knowledge(message: types.Message):
    await message.answer(
        "📚 <b>Знания, бро:</b>\n\n"
        "💦 <b>Счётчик</b> — /nofap (записать и статистика)\n"
        "🥔 <b>Брутто-сила</b> — /strength\n"
        "⚖️ <b>Вес</b> — /weigh\n"
        "🏅 <b>Титул</b> — /title\n"
        "🚫 <b>Зал позора</b> — /shame"
    )


# ─────────── NO-FAP ───────────
@dp.message(Command("nofap"))
async def nofap_cmd(message: types.Message, state: FSMContext):
    await message.answer("💦 Сколько раз сегодня, бро? Напиши цифру (0, 1, 5...)")
    await state.set_state(NofapState.count)


@dp.message(NofapState.count)
async def nofap_set(message: types.Message, state: FSMContext):
    try:
        n = int(message.text.strip())
    except Exception:
        await message.answer("Цифрой, бро.")
        return
    today = datetime.now().date().isoformat()
    await set_nofap(message.from_user.id, today, n)
    week = await get_nofap_week(message.from_user.id)
    total = await get_nofap_total(message.from_user.id)
    buf = draw_nofap_stats(week, total=total, today=n)
    if n == 0:
        advice = "Красавчик, держи фокус. 💪"
    elif n <= 2:
        advice = "Норма, бро. Не парься. Но следи."
    else:
        advice = "Слушай, займись делом. Стресс, сон, тренировки — вот твоё."
    caption = (
        f"📊 <b>Статистика</b>\n\n{advice}\n\n"
        f"<i>Тестостерон падает ненадолго после, но восстанавливается. "
        f"Главное - не в петлю зависимости. Держи баланс.</i>"
    )
    await message.answer_photo(
        BufferedInputFile(buf.read(), filename="nofap.png"),
        caption=caption
    )
    await state.clear()


# ─────────── БРУТТО-СИЛА ───────────
@dp.message(Command("strength"))
async def strength_cmd(message: types.Message, state: FSMContext):
    await message.answer("💪 Напиши упражнение и вес через пробел. Пример: <b>жим 120</b>")
    await state.set_state(StrengthState.exercise)


@dp.message(StrengthState.exercise)
async def strength_set(message: types.Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <b>упражнение вес</b>. Пример: жим 120")
        return
    exercise = parts[0]
    try:
        weight = float(parts[1].replace(",", "."))
    except Exception:
        await message.answer("Вес числом, бро.")
        return
    await save_strength(message.from_user.id, exercise, weight)

    items = []
    if weight >= 30:
        items.append(f"🥔 {round(weight/40,1)} мешков картошки")
    if weight >= 60:
        items.append(f"❄️ {round(weight/80,1)} холодильников")
    if weight >= 100:
        items.append(f"🧱 {round(weight/50,1)} мешков цемента")
    if not items:
        items.append("🐱 котёнка примерно")

    buf = draw_strength_card(exercise.capitalize(), int(weight), items)
    await message.answer_photo(
        BufferedInputFile(buf.read(), filename="strength.png"),
        caption="💪 <b>Твоя брутто-сила</b>"
    )
    await state.clear()


# ─────────── ВЕС ───────────
@dp.message(Command("weigh"))
async def weigh_cmd(message: types.Message, state: FSMContext):
    await message.answer("⚖️ Сколько сейчас весишь? В кг.")
    await state.set_state(WeightState.value)


@dp.message(WeightState.value)
async def weigh_set(message: types.Message, state: FSMContext):
    try:
        w = float(message.text.replace(",", "."))
    except Exception:
        await message.answer("Числом, бро.")
        return
    user = await get_user(message.from_user.id)
    old = user.get("weight") or w
    await save_weight(message.from_user.id, w)
    await update_user(message.from_user.id, weight=w)

    diff = w - old
    bt = user.get("body_type")
    if diff > 0.5:
        if bt == "endomorph":
            msg = "Вес растёт. Следи, чтобы это были мышцы, а не жир. Кардио не забывай."
        else:
            msg = "Вес растёт — мышцы растут. Хорошо, бро. Продолжай."
    elif diff < -0.5:
        if bt == "ectomorph":
            msg = "Ты схуднул. Ты и так худой. Жри больше, бро!"
        else:
            msg = "Вес падает. Если цель — масса, срочно добавь еды."
    else:
        msg = "Вес стабилен. Это норма. Продолжай."
    await message.answer(f"⚖️ Записал: <b>{w} кг</b>\n\n{msg}")
    await state.clear()


# ─────────── ТИТУЛ ───────────
@dp.message(Command("title"))
async def title_cmd(message: types.Message):
    user = await get_user(message.from_user.id)
    t = user.get("current_title") or "Новичок"
    for k, v in TITLES.items():
        if v["name"] == t:
            buf = draw_title_card(v["name"], v["emoji"], v["reason"])
            await message.answer_photo(
                BufferedInputFile(buf.read(), filename="title.png"),
                caption="🏅 <b>Титул дня</b>"
            )
            return
    await message.answer(f"🏅 Титул: <b>{t}</b>")


# ─────────── ЗАЛ ПОЗОРА ───────────
@dp.message(Command("shame"))
async def shame_cmd(message: types.Message):
    top = await get_shame_today()
    text = "🚫 <b>Топ-3 слабака за день:</b>\n\n"
    for i, u in enumerate(top):
        name = u["first_name"] or u["username"] or "Аноним"
        text += f"{i+1}. {name}\n"
    text += "\n💔 Завтра — докажи обратное."
    await message.answer(text)


# ─────────── ТРЕНИРОВКА ───────────
def get_plan_for_user(user):
    goal = (user.get("goal") or "").lower()
    place = user.get("workout_place") or "home"
    inv = user.get("inventory") or "nothing"

    if place == "gym":
        if "похудеть" in goal:
            return [
                ("Приседания", "4x10", "ex_squat"),
                ("Жим лёжа", "4x8", "ex_bench"),
                ("Тяга штанги", "4x8", "ex_deadlift"),
                ("Бёрпи", "3x12", "ex_burpee"),
                ("Скакалка", "3x60сек", "ex_jumprope"),
                ("Планка", "3x60сек", "ex_plank"),
            ]
        elif "сила" in goal or "сильн" in goal:
            return [
                ("Приседания", "5x5", "ex_squat"),
                ("Жим лёжа", "5x5", "ex_bench"),
                ("Становая тяга", "1x5", "ex_deadlift"),
                ("Жим стоя", "5x5", "ex_press"),
                ("Тяга штанги", "5x5", "ex_row"),
            ]
        else:
            return [
                ("Жим лёжа", "4x8", "ex_bench"),
                ("Жим гантелей", "3x10", "ex_press"),
                ("Разводка гантелей", "3x12", "ex_fly"),
                ("Брусья", "3x10", "ex_dips"),
                ("Французский жим", "3x12", "ex_curl"),
            ]
    else:
        if "похудеть" in goal:
            return [
                ("Бег/быстрая ходьба", "15 мин", "ex_run"),
                ("Бёрпи", "3x12", "ex_burpee"),
                ("Скакалка", "3x60сек", "ex_jumprope"),
                ("Приседания", "4x20", "ex_squat"),
                ("Выпады", "3x12", "ex_lunge"),
                ("Планка", "3x60сек", "ex_plank"),
            ]
        elif inv == "dumbbells":
            return [
                ("Жим гантелей лёжа", "4x10", "ex_bench"),
                ("Тяга гантелей", "4x10", "ex_row"),
                ("Приседания с гантелями", "4x12", "ex_squat"),
                ("Выпады с гантелями", "3x12", "ex_lunge"),
                ("Махи в стороны", "3x15", "ex_press"),
                ("Французский жим", "3x12", "ex_curl"),
            ]
        elif inv == "kettlebell":
            return [
                ("Приседания с гирей", "4x12", "ex_squat"),
                ("Мах гирей", "4x15", "ex_row"),
                ("Жим гири", "3x10", "ex_press"),
                ("Выпады с гирей", "3x12", "ex_lunge"),
                ("Планка", "3x60сек", "ex_plank"),
            ]
        elif inv in ("backpack_water", "backpack_books"):
            return [
                ("Приседания с рюкзаком", "4x15", "ex_squat"),
                ("Жим рюкзака", "4x12", "ex_press"),
                ("Тяга рюкзака", "4x12", "ex_row"),
                ("Выпады с рюкзаком", "3x12", "ex_lunge"),
                ("Планка с рюкзаком", "3x60сек", "ex_plank"),
            ]
        else:
            return [
                ("Отжимания", "4x15", "ex_pushup"),
                ("Приседания", "4x20", "ex_squat"),
                ("Выпады", "3x12", "ex_lunge"),
                ("Планка", "3x60сек", "ex_plank"),
                ("Бёрпи", "3x10", "ex_burpee"),
                ("Скакалка (или бег на месте)", "3x60сек", "ex_jumprope"),
            ]


@dp.message(F.text == "🏋️ Тренировка")
async def workout_menu(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    has_pro = False
    if user and user.get("pro_until"):
        try:
            has_pro = datetime.fromisoformat(user["pro_until"]) > datetime.now()
        except Exception:
            pass
    if not has_pro and not user.get("trial_used"):
        await message.answer(
            "🦍 <b>Программа тренировок, бро.</b>\n\n"
            "😏 Слушай, тренировки — это <b>PRO</b>, 199 ⭐/мес.\n"
            "Но я не жлоб. Дам <b>1 день бесплатно</b>, попробуй.\n"
            "Дальше — 199 звёзд. Это как 2 шаурмы, только работает дольше.",
            reply_markup=kb_workout_pro()
        )
        return
    if not has_pro:
        await message.answer(
            "🚫 <b>Пробный закончился, бро.</b>\n\n"
            "199 ⭐ — и полный доступ:\n"
            "✅ Адаптив под тебя\n"
            "✅ Полная программа\n"
            "✅ Таймеры\n"
            "✅ Прогрессия весов",
            reply_markup=kb_workout_pro()
        )
        return
    await message.answer("🦍 Где тренируешься, бро?", reply_markup=kb_workout_place())


@dp.callback_query(F.data == "trial_workout")
async def trial_workout(cb: CallbackQuery):
    await update_user(cb.from_user.id, trial_used=1)
    await cb.message.answer("🎁 Пробный день активирован! Где тренируешься?", reply_markup=kb_workout_place())
    await cb.answer()


@dp.callback_query(F.data == "buy_pro")
async def buy_pro(cb: CallbackQuery):
    await send_pro_invoice(bot, cb.from_user.id)
    await cb.answer()


@dp.message(F.text == "🏠 Дома")
async def workout_home(message: types.Message, state: FSMContext):
    await message.answer("🦍 Что у тебя есть дома?", reply_markup=kb_workout_inventory())
    await state.set_state(WorkoutState.inventory)


@dp.message(F.text == "🏟 В зале")
async def workout_gym(message: types.Message, state: FSMContext):
    await update_user(message.from_user.id, workout_place="gym")
    await show_workout_plan(message)


@dp.message(WorkoutState.inventory)
async def inventory_set(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("Где тренируешься?", reply_markup=kb_workout_place())
        await state.clear()
        return
    inv_map = {
        "🏋️ Гантели": "dumbbells",
        "🔔 Гиря": "kettlebell",
        "🎒 Рюкзак с водой": "backpack_water",
        "📚 Рюкзак с книгами": "backpack_books",
        "🚫 Ничего нет": "nothing",
    }
    inv = inv_map.get(message.text, "nothing")
    await update_user(message.from_user.id, workout_place="home", inventory=inv)
    await show_workout_plan(message)


async def show_workout_plan(message):
    user = await get_user(message.from_user.id)
    plan = get_plan_for_user(user)
    text = "🦍 <b>Твоя тренировка, бро:</b>\n\n"
    for i, (name, sets, _) in enumerate(plan, 1):
        text += f"{i}. <b>{name}</b> — {sets}\n"
    text += f"\n🎧 <b>Плейлист:</b> {CHANNEL_URL}\n\nГотов?"
    await message.answer(text, reply_markup=kb_start_workout())


@dp.callback_query(F.data == "start_workout")
async def start_workout(cb: CallbackQuery, state: FSMContext):
    user = await get_user(cb.from_user.id)
    plan = get_plan_for_user(user)
    await state.update_data(plan=plan, idx=0, done=0)
    await send_next_exercise(cb.message, state)
    await cb.answer()


async def send_next_exercise(message, state):
    data = await state.get_data()
    plan = data.get("plan", [])
    idx = data.get("idx", 0)
    if idx >= len(plan):
        await finish_workout(message, state)
        return
    name, sets, img = plan[idx]
    text = (
        f"🏋️ <b>Упражнение {idx+1}/{len(plan)}: {name}</b>\n\n"
        f"Сетов: <b>{sets}</b>\n\n"
        f"Давай, бро. Ты можешь. 💪\n"
        f"Когда закончишь — жми кнопку."
    )
    await send_photo_or_text(
        message,
        f"images/exercises/{img}.png",
        text,
        reply_markup=kb_exercise_done()
    )


@dp.callback_query(F.data == "ex_done")
async def ex_done(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data.get("idx", 0) + 1
    done = data.get("done", 0) + 1
    await state.update_data(idx=idx, done=done)
    try:
        await cb.message.delete()
    except Exception:
        pass
    await send_next_exercise(cb.message, state)
    await cb.answer("Красавчик!")


@dp.callback_query(F.data == "ex_fail")
async def ex_fail(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data.get("idx", 0) + 1
    await state.update_data(idx=idx)
    try:
        await cb.message.delete()
    except Exception:
        pass
    await send_next_exercise(cb.message, state)
    await cb.answer("Ок, идём дальше")


async def finish_workout(message, state):
    data = await state.get_data()
    done = data.get("done", 0)
    await message.answer(
        f"🔥 <b>Тренировка завершена, бро!</b>\n\n"
        f"Выполнено: <b>{done}</b> упражнений\n\n"
        f"Насколько устал? 1-10",
        reply_markup=kb_fatigue()
    )
    await state.set_state(WorkoutState.fatigue)


@dp.callback_query(F.data.startswith("fatigue_"))
async def fatigue_set(cb: CallbackQuery, state: FSMContext):
    level = int(cb.data.split("_")[1])
    data = await state.get_data()
    done = data.get("done", 0)
    await save_workout_log(cb.from_user.id, done, level, "", "")
    today = datetime.now().date().isoformat()
    await add_tracker(cb.from_user.id, today, workout_done=True)
    user = await get_user(cb.from_user.id)
    await update_user(cb.from_user.id, total_exercises=(user.get("total_exercises") or 0) + done)

    if level >= 7:
        t = TITLES["monstr"]
    elif level >= 4:
        t = TITLES["silach"]
    else:
        t = TITLES["molodec"]
    await update_user(
        cb.from_user.id,
        current_title=t["name"],
        current_title_date=today
    )
    await cb.message.answer(
        f"🏅 Титул дня: <b>{t['emoji']} {t['name']}</b>\n\n{t['reason']}"
    )
    if level <= 4:
        await cb.message.answer("Слишком легко, бро. В следующий раз добавлю нагрузки. 😏")
    else:
        await cb.message.answer("Тяжело? Значит растёшь. Так держать, бро! 🦍")
    await state.clear()
    await cb.answer()


# ─────────── ОПЛАТА ───────────
@dp.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def payment_success(message: types.Message):
    payload = message.successful_payment.invoice_payload
    uid = message.from_user.id
    if payload == "pro_monthly":
        until = (datetime.now() + timedelta(days=30)).isoformat()
        await update_user(uid, pro_until=until)
        await message.answer("✅ <b>PRO активирован на 30 дней!</b>\n\nПогнали, бро 🦍")
    elif payload == "lifetime":
        await update_user(uid, lifetime=1)
        await message.answer("👑 <b>LIFETIME активирован!</b>\n\nТы легенда, бро.")
    elif payload == "program_once":
        await message.answer("📋 <b>Программа оформлена!</b>\n\nСкоро получишь, бро.")


# ─────────── АДМИНКА ───────────
@dp.message(F.text == "🛠 Админка")
async def admin_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🦍 <b>Админ-панель</b>", reply_markup=kb_admin())


@dp.message(F.text == "📢 Рассылка")
async def admin_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Напиши текст рассылки:")
    await state.set_state(AdminState.broadcast_text)


@dp.message(AdminState.broadcast_text)
async def do_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    users = await get_all_users()
    ok = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], message.text)
            ok += 1
        except Exception:
            pass
    await save_template(message.text)
    await message.answer(f"✅ Отправлено: {ok}/{len(users)}", reply_markup=kb_admin())
    await state.clear()


@dp.message(F.text == "📝 Шаблоны")
async def admin_templates(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    tpl = await get_templates()
    if not tpl:
        await message.answer("Шаблонов пока нет.")
        return
    text = "📝 <b>Последние шаблоны:</b>\n\n"
    for i, t in enumerate(tpl, 1):
        text += f"{i}. {t['text'][:100]}...\n\n"
    await message.answer(text)


@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🦍 Главное меню", reply_markup=main_menu(is_admin(message.from_user.id)))


# ─────────── ЗАПУСК ───────────
async def main():
    await init_db()
    start_scheduler(bot)
    print("🦍 Billy Gorilla started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
