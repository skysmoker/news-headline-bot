import html
import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

import storage
from giga_client import generate_summary
from keyboards import summary_length_keyboard

router = Router()

LENGTH_LABELS = {
    "short": "короткий",
    "standard": "стандартный",
    "long": "развёрнутый",
}


@router.callback_query(F.data.startswith("summary_len:"))
async def handle_summary_length(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 2:
        await callback.answer("Некорректный запрос", show_alert=True)
        return

    length = parts[1]
    if length not in LENGTH_LABELS:
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

    await callback.answer(f"Генерирую {LENGTH_LABELS[length]} анонс...")

    header = f"📝 <b>Анонс по статье #{article_id}:</b>" if article_id else "📝 <b>Анонс:</b>"
    try:
        await callback.message.edit_text(
            f"{header}\n<i>⏳ Перегенерирую ({LENGTH_LABELS[length]})...</i>",
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    try:
        summary = await generate_summary(article_text, length=length)
    except Exception as e:
        logging.exception("GigaChat summary error")
        await callback.message.edit_text(
            f"⚠️ Ошибка GigaChat: {html.escape(str(e))}",
            parse_mode="HTML",
            reply_markup=summary_length_keyboard(article_id=article_id),
        )
        return

    try:
        await callback.message.edit_text(
            f"{header}\n{html.escape(summary)}",
            parse_mode="HTML",
            reply_markup=summary_length_keyboard(article_id=article_id),
        )
    except TelegramBadRequest:
        pass
