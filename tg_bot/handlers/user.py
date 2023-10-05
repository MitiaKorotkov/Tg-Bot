from .menu_handlers import main_menu_proceccing

from aiogram.filters import CommandStart
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram import Router

from ..tmp import DESCRIPTION

user_router = Router()

# Обработчик команды /start
@user_router.message(CommandStart(), StateFilter(default_state))
async def start_command(messege: Message, bot):
    # Отправляем краткое описание бота и загружаем главное меню в ответ на сообщение /start
    await messege.answer(text=DESCRIPTION)
    await main_menu_proceccing(messege, bot)


# Съедаем весь спам, не являющийся поддерживаемыми командами
@user_router.message()
async def delete_spam(message: Message):
    await message.delete()
