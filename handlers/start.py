from aiogram import Router, F
from aiogram.types import Message
from keyboards import main_keyboard

router = Router()


@router.message(F.from_user.id == 1675347, F.text == "/start")
async def handle_start(message: Message):
    await message.answer(
        "Привет! Пришли ссылку или текст статьи — я сделаю заголовки и анонс.\n"
        "Или воспользуйся кнопками внизу.",
        reply_markup=main_keyboard()
    )
