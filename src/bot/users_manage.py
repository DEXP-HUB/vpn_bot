from os import getenv

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
from fast_depends import Depends, inject

from .dependency import provide_deleted_user_by_id, provide_deleted_user_by_name, provide_new_user, provide_users_list
from .fsm import UserManageStates
from .middlewares import AdminMessageMiddleware, LoggingMessageMiddleware
from .repository import UserRepository
from ..database import async_session_maker

load_dotenv()

router = Router(name="Users")
router.message.middleware(LoggingMessageMiddleware(router.name))
router.message.middleware(AdminMessageMiddleware(
    user_repository=UserRepository(async_session_maker)
    )
)


@router.message(Command("add_user_by_id"))
async def add_user_by_id(
    message: Message,
    state: FSMContext,
) -> None:
    """Запускает сценарий добавления пользователя через FSM."""
    await state.set_state(UserManageStates.waiting_add_user_id)
    await message.answer("Введите telegram_id пользователя для добавления:")


@router.message(UserManageStates.waiting_add_user_id, F.text.isdigit())
@inject
async def process_add_user_by_id(
    message: Message, 
    state: FSMContext,
) -> None:
    """Обрабатывает ввод telegram_id и добавляет пользователя в БД."""
    await state.set_data({"telegram_id": message.text})
    await message.answer("Введите имя пользователя:")
    await state.set_state(UserManageStates.waiting_add_user_name)


@router.message(UserManageStates.waiting_add_user_name, F.text)
@inject
async def process_add_user_by_name(
    message: Message,
    state: FSMContext,
    status: str = Depends(provide_new_user),
) -> None:
    """Обрабатывает ввод имени пользователя и добавляет пользователя в БД."""
    await message.answer(status)
    await state.clear()


@router.message(Command("delete_user_id"))
async def deleted_user(
    message: Message,
    state: FSMContext,
) -> None:
    """Запускает сценарий удаления пользователя через FSM."""
    await state.set_state(UserManageStates.waiting_delete_user_id)
    await message.answer("Введите telegram_id пользователя для удаления:")


@router.message(UserManageStates.waiting_delete_user_id, F.text.isdigit())
@inject
async def process_deleted_user(
    message: Message,
    state: FSMContext,
    status: str = Depends(provide_deleted_user_by_id),
) -> None:
    """Обрабатывает ввод telegram_id и удаляет пользователя из БД."""
    await message.answer(status)
    await state.clear()


@router.message(Command("delete_user_name"))
async def deleted_user_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Запускает сценарий удаления пользователя через FSM."""
    await state.set_state(UserManageStates.waiting_delete_user_name)
    await message.answer("Введите имя пользователя для удаления:")


@router.message(UserManageStates.waiting_delete_user_name, F.text)
@inject
async def process_deleted_user_name(
    message: Message,
    state: FSMContext,
    status: str = Depends(provide_deleted_user_by_name),
) -> None:
    """Обрабатывает ввод имени пользователя и удаляет пользователя из БД."""
    await message.answer(status)
    await state.clear()

@router.message(Command("users"))
@inject
async def get_users(
    message: Message,
    users_list: str = Depends(provide_users_list),
) -> None:
    """Отправляет список всех пользователей из БД."""
    await message.answer(users_list)
