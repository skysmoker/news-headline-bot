import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

import storage
from giga_client import close_client
from handlers.start import router as start_router
from handlers.history import router as history_router
from handlers.summary import router as summary_router
from handlers.summary_length import router as summary_length_router
from handlers.summary_by_id import router as summary_by_id_router
from handlers.headlines import router as headlines_router

load_dotenv()
logging.basicConfig(level=logging.INFO)

ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "1675347"))

# --- Прокси для Telegram (Франкфурт) ---
proxy_url = os.getenv("TELEGRAM_PROXY")
session = AiohttpSession(proxy=proxy_url) if proxy_url else None
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), session=session)
dp = Dispatcher()


@dp.update.outer_middleware()
async def access_middleware(handler, event, data):
    user = data.get("event_from_user")
    if user and user.id != ALLOWED_USER_ID:
        return
    return await handler(event, data)


# Подключаем роутеры (порядок важен: команды и кнопки — до общего handle_text)
dp.include_router(start_router)
dp.include_router(history_router)
dp.include_router(summary_router)
dp.include_router(summary_length_router)
dp.include_router(summary_by_id_router)
dp.include_router(headlines_router)


async def main():
    await storage.init_db()
    logging.info("Бот запущен")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await close_client()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
