from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_gender = State()
    waiting_preferred_gender = State()
    waiting_photo = State()
    waiting_bio = State()
    waiting_city = State()

class ProfileStates(StatesGroup):
    waiting_new_name = State()
    waiting_new_age = State()
    waiting_new_gender = State()
    waiting_new_preferred_gender = State()
    waiting_new_photo = State()
    waiting_new_bio = State()
    waiting_new_city = State()
    waiting_new_min_age = State()
    waiting_new_max_age = State()
    waiting_new_max_distance = State() 