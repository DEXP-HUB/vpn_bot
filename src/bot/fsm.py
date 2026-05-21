from aiogram.fsm.state import State, StatesGroup


class UserManageStates(StatesGroup):
    """Состояния FSM для пошагового управления пользователями."""

    waiting_add_user_id = State()
    waiting_delete_user_id = State()
    waiting_add_user_name = State()
    waiting_delete_user_name = State()
