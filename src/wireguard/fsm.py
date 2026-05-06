from aiogram.fsm.state import State, StatesGroup


class UserConfigStates(StatesGroup):
    """Состояния FSM для добавления или удаления конфигурации пользователя."""

    waiting_add_user_config = State()
    waiting_delete_user_config = State()