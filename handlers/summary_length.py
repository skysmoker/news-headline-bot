import html
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

import storage
from giga_client import generate_summary
from keyboards import summary_length_keyboard

router = Router()


@router.callback_query(F.data.startswith("summary_len:"))
async def handle_summary_length(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 2:
        await callback.answer("Некорректный запрос", show_alert=True)
        return

    length = parts[1]
    if length not in ("short", "standard", "long"):
        await callback.answer("Неизвестная длина", show_alert=True)
        return

    article_id: int | None = None
    if len(parts) >= 3 and parts[2].isdigit():
        article_id = int(parts[2])
        article_text = await storage.get_article_by_id(article_id, callback.from_user.id)
    else:
        article = await storage.get_article(callback.from_user.id)
        if article:
            article_id, article_text = article
        else:
            article_text = None

    if not article_text:
        await callback.answer("Статья не найдена", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer("⏳ Перегенерирую анонс...")

    try:
        summary = await generate_summary(article_text, length=length)
    except Exception as e:
        logging.exception("GigaChat summary error")
        await callback.message.answer(f"⚠️ Ошибка GigaChat: {html.escape(str(e))}")
        return

    header = f"📝 <b>Анонс по статье #{article_id}:</b>" if article_id else "📝 <b>Анонс:</b>"
    await callback.message.answer(
        f"{header}\n{html.escape(summary)}",
        parse_mode="HTML",
        reply_markup=summary_length_keyboard(article_id=article_id),
    )
