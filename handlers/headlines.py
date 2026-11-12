import logging

from aiogram import Router, F
from aiogram.types import Message
from keyboards import main_keyboard

import storage
from extractor import extract_article_text
from giga_client import generate_headlines

router = Router()


@router.message(F.from_user.id == 1675347, F.text.startswith("http"))
async def handle_url(message: Message):
    url = message.text.strip()
    await message.answer("⏳ Ссылка получена, анализирую статью...")

    article_text = extract_article_text(url)
    if not article_text:
        await message.answer(
            "❌ Не удалось извлечь текст. Возможно, сайт защищен от копирования и парсинга.\n"
            "Скопируйте текст статьи и пришлите его сюда, обработка будет продолжена."
        )
        return

    title = article_text.split("\n")[0].strip()[:100] or None
    storage.save_article(message.from_user.id, article_text, source_url=url, source_title=title)

    await message.answer(f"📄 Извлечено символов по ссылке: {len(article_text)}. Генерирую заголовки и аргументацию...")

    try:
        result = generate_headlines(article_text)
    except Exception as e:
        logging.exception("GigaChat error")
        await message.answer(f"⚠️ Ошибка GigaChat: {e}")
        return

    response = "📰 <b>5 вариантов заголовка:</b>\n\n"
    for i, h in enumerate(result.headlines, 1):
        response += f"<b>{i}.</b> <b>{h.title}</b>\n<i>{h.rationale}</i>\n\n"

    await message.answer(response, parse_mode="HTML", reply_markup=main_keyboard())


@router.message(F.from_user.id == 1675347, F.text)
async def handle_text(message: Message):
    if len(message.text) < 100:
        await message.answer("Пришли ссылку (начинается с http: или https:) или текст статьи целиком.")
        return

    title = message.text.split("\n")[0].strip()[:100] or None
    storage.save_article(message.from_user.id, message.text, source_url=None, source_title=title)

    await message.answer("⏳ Обрабатываю текст...")
    try:
        result = generate_headlines(message.text)
    except Exception as e:
        logging.exception("GigaChat error")
        await message.answer(f"⚠️ Ошибка GigaChat: {e}")
        return

    response = "📰 <b>5 вариантов заголовка:</b>\n\n"
    for i, h in enumerate(result.headlines, 1):
        response += f"<b>{i}.</b> <b>{h.title}</b>\n<i>{h.rationale}</i>\n\n"

    await message.answer(response, parse_mode="HTML", reply_markup=main_keyboard())
