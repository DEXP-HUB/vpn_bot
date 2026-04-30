from os import getenv

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
from fast_depends import Depends, inject

from .dependency import provide_deleted_user, provide_new_user
from .fsm import UserManageStates
from .middlewares import AdminMessageMiddleware, LoggingMessageMiddleware

load_dotenv()

router = Router(name="Users")
router.message.middleware(LoggingMessageMiddleware(router.name))
router.message.middleware(AdminMessageMiddleware(int(getenv("ADMIN_ID"))))


@router.message(Command("add_user"))
async def add_user(
    message: Message,
    state: FSMContext,
) -> None:
    """Запускает сценарий добавления пользователя через FSM."""
    await state.set_state(UserManageStates.waiting_add_user_id)
    await message.answer("Введите telegram_id пользователя для добавления:")


@router.message(UserManageStates.waiting_add_user_id, F.text.isdigit())
@inject
async def process_add_user(
    message: Message, 
    state: FSMContext,
    status: str = Depends(provide_new_user),
) -> None:
    """Обрабатывает ввод telegram_id и добавляет пользователя в БД."""
    await message.answer(status)
    await state.clear()


@router.message(Command("delete_user"))
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
    status: str = Depends(provide_deleted_user),
) -> None:
    """Обрабатывает ввод telegram_id и удаляет пользователя из БД."""
    await message.answer(status)
    await state.clear()
