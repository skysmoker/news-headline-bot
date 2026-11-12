import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import storage
from giga_client import generate_summary

router = Router()


def summary_length_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Короче", callback_data="summary_len:short"),
            InlineKeyboardButton(text="Длиннее", callback_data="summary_len:long"),
        ]
    ])


@router.callback_query(F.data.startswith("summary_len:"))
async def handle_summary_length(callback: CallbackQuery):
    # Достаём длину из callback_data ("summary_len:short" -> "short")
    try:
        length = callback.data.split(":", 1)[1]
    except IndexError:
        await callback.answer("Некорректный запрос", show_alert=True)
        return

    if length not in ("short", "standard", "long"):
        await callback.answer("Неизвестная длина", show_alert=True)
        return

    article_text = storage.get_article(callback.from_user.id)
    if not article_text:
        await callback.answer("Статья не найдена", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer("⏳ Перегенерирую анонс...")

    try:
        summary = generate_summary(article_text, length=length)
    except Exception as e:
        logging.exception("GigaChat summary error")
        await callback.message.answer(f"⚠️ Ошибка GigaChat: {e}")
        return

    await callback.message.answer(
        f"📝 <b>Анонс:</b>\n{summary}",
        parse_mode="HTML",
        reply_markup=summary_length_keyboard(),
    )
