from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    steam_url = State()
    rating = State()
    about_me = State()
