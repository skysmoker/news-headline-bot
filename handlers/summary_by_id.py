import html
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

import storage
from giga_client import generate_editorial_pack
from handlers.headlines import format_editorial_pack

router = Router()


@router.callback_query(F.data.startswith("summary_by_id:"))
async def handle_summary_by_id(callback: CallbackQuery):
    try:
        article_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректный id статьи", show_alert=True)
        return

    article_text = await storage.get_article_by_id(article_id, callback.from_user.id)
    if not article_text:
        await callback.answer("Статья не найдена", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer(f"⏳ Генерирую заголовки и анонсы по статье #{article_id}...")

    try:
        headlines, summaries = await generate_editorial_pack(article_text)
    except Exception as e:
        logging.exception("GigaChat pack error")
        await callback.message.answer(f"⚠️ Ошибка GigaChat: {html.escape(str(e))}")
        return

    await callback.message.answer(
        format_editorial_pack(headlines, summaries),
        parse_mode="HTML",
    )
