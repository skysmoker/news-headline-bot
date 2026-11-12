import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

import storage
from giga_client import generate_summary

router = Router()


@router.callback_query(F.data.startswith("summary_by_id:"))
async def handle_summary_by_id(callback: CallbackQuery):
    # Достаём id статьи из callback_data ("summary_by_id:13" -> 13)
    try:
        article_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректный id статьи", show_alert=True)
        return

    article_text = storage.get_article_by_id(article_id, callback.from_user.id)
    if not article_text:
        await callback.answer("Статья не найдена", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer(f"⏳ Пишу анонс по статье #{article_id}...")

    try:
        summary = generate_summary(article_text)
    except Exception as e:
        logging.exception("GigaChat summary error")
        await callback.message.answer(f"⚠️ Ошибка GigaChat: {e}")
        return

    await callback.message.answer(
        f"📝 <b>Анонс по статье #{article_id}:</b>\n{summary}",
        parse_mode="HTML",
    )
