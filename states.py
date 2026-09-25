from aiogram.fsm.state import State, StatesGroup

class Reg(StatesGroup):
    age = State()
    height = State()
    weight = State()
    meals = State()
    water = State()
    goal = State()
    subscribe = State()

class TrackerState(StatesGroup):
    water = State()
    food = State()

class WorkoutState(StatesGroup):
    place = State()
    inventory = State()
    running = State()
    fatigue = State()

class NofapState(StatesGroup):
    count = State()

class StrengthState(StatesGroup):
    exercise = State()
    weight = State()

class WeightState(StatesGroup):
    value = State()

class GoalState(StatesGroup):
    text = State()

class AdminState(StatesGroup):
    broadcast_text = State()
    broadcast_photo = State()
    schedule_date = State()
