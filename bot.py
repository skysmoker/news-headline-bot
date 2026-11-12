import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

from handlers.start import router as start_router
from handlers.history import router as history_router
from handlers.summary import router as summary_router
from handlers.summary_length import router as summary_length_router
#from handlers.summary_by_id import router as summary_by_id_router
from handlers.headlines import router as headlines_router

load_dotenv()
logging.basicConfig(level=logging.INFO)

# --- Прокси для Telegram (Франкфурт) ---
proxy_url = os.getenv("TELEGRAM_PROXY")
session = AiohttpSession(proxy=proxy_url) if proxy_url else None
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), session=session)
dp = Dispatcher()

# Подключаем роутеры (порядок важен: команды и кнопки — до общего handle_text)
dp.include_router(start_router)
dp.include_router(history_router)
dp.include_router(summary_router)
dp.include_router(summary_length_router)
#dp.include_router(summary_by_id_router)
dp.include_router(headlines_router)


async def main():
    logging.info("Бот запущен")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
