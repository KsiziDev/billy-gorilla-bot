from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ─────────── ГЛАВНОЕ МЕНЮ ───────────
def main_menu(is_admin=False):
    kb = [
        [KeyboardButton(text="🏋️ Тренировка"), KeyboardButton(text="🍗 Трекер")],
        [KeyboardButton(text="📊 Профиль"), KeyboardButton(text="🍎 Питание")],
        [KeyboardButton(text="🎯 Цель"), KeyboardButton(text="🏆 Лиги")],
        [KeyboardButton(text="📚 Знания"), KeyboardButton(text="🆘 Помощь")],
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🛠 Админка")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ─────────── РЕГИСТРАЦИЯ ───────────
def kb_goal():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💪 Набрать массу")],
        [KeyboardButton(text="🔥 Похудеть")],
        [KeyboardButton(text="⚡ Рельеф")],
        [KeyboardButton(text="🐗 Просто стать сильнее")],
    ], resize_keyboard=True, one_time_keyboard=True)


def kb_unknown():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Не знаю 🤷")],
    ], resize_keyboard=True, one_time_keyboard=True)


def kb_after_help():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Понял, написать число")],
    ], resize_keyboard=True, one_time_keyboard=True)


def kb_subscribe():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/billy_gorilla")],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")],
    ])


# ─────────── ТРЕКЕР ───────────
def kb_tracker():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💧 Вода"), KeyboardButton(text="🍎 Еда")],
        [KeyboardButton(text="📅 За неделю"), KeyboardButton(text="⬅️ Назад")],
    ], resize_keyboard=True)


# ─────────── ТРЕНИРОВКА ───────────
def kb_workout_place():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏠 Дома"), KeyboardButton(text="🏟 В зале")],
        [KeyboardButton(text="⬅️ Назад")],
    ], resize_keyboard=True)


def kb_workout_inventory():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏋️ Гантели"), KeyboardButton(text="🔔 Гиря")],
        [KeyboardButton(text="🎒 Рюкзак с водой"), KeyboardButton(text="📚 Рюкзак с книгами")],
        [KeyboardButton(text="🚫 Ничего нет")],
        [KeyboardButton(text="⬅️ Назад")],
    ], resize_keyboard=True)


def kb_workout_pro():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Попробовать 1 день", callback_data="trial_workout")],
        [InlineKeyboardButton(text="✅ Купить PRO 199⭐", callback_data="buy_pro")],
    ])


def kb_start_workout():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать тренировку", callback_data="start_workout")],
    ])


def kb_exercise_done():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнил", callback_data="ex_done")],
        [InlineKeyboardButton(text="❌ Не смог", callback_data="ex_fail")],
    ])


def kb_fatigue():
    kb = [[InlineKeyboardButton(text=str(i), callback_data=f"fatigue_{i}") for i in range(1, 6)],
          [InlineKeyboardButton(text=str(i), callback_data=f"fatigue_{i}") for i in range(6, 11)]]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ─────────── ПИТАНИЕ ───────────
def kb_food_lessons(idx, total, has_pro):
    prev_btn = InlineKeyboardButton(text="⬅️", callback_data=f"food_{idx-1}")
    next_btn = InlineKeyboardButton(
        text="➡️" if has_pro or idx + 1 == 0 else "🚫",
        callback_data=f"food_{idx+1}" if has_pro or idx + 1 == 0 else "food_locked"
    )
    if idx == 0:
        prev_btn = InlineKeyboardButton(text="🚫", callback_data="noop")
    if idx == total - 1:
        next_btn = InlineKeyboardButton(text="🚫", callback_data="noop")
    return InlineKeyboardMarkup(inline_keyboard=[
        [prev_btn, InlineKeyboardButton(text=f"Урок {idx+1}", callback_data="noop"), next_btn],
    ])


# ─────────── АДМИНКА ───────────
def kb_admin():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📢 Рассылка")],
        [KeyboardButton(text="🖼 С картинкой")],
        [KeyboardButton(text="⏰ Отложить")],
        [KeyboardButton(text="📝 Шаблоны")],
        [KeyboardButton(text="💰 Напомнить о PRO")],
        [KeyboardButton(text="⬅️ Назад")],
    ], resize_keyboard=True)


# ─────────── ПРОЧЕЕ ───────────
def kb_back():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⬅️ Назад")],
    ], resize_keyboard=True)
