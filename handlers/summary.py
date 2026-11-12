import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import storage
from extractor import extract_article_text
from giga_client import generate_summary

router = Router()


def summary_length_keyboard(article_id: int | None = None) -> InlineKeyboardMarkup:
    """Кнопки выбора длины анонса. article_id передаётся, если анонс по статье из истории."""
    suffix = f":{article_id}" if article_id is not None else ""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Короче", callback_data=f"summary_len:short{suffix}"),
            InlineKeyboardButton(text="Длиннее", callback_data=f"summary_len:long{suffix}"),
        ]
    ])


@router.message(F.from_user.id == 1675347, F.text.startswith("/summary"))
async def handle_summary_command(message: Message):
    payload = message.text[len("/summary"):].strip()

    if not payload:
        await message.answer(
            "Использование:\n"
            "/summary <ссылка> — сгенерировать анонс по статье\n"
            "Анонс также может быть сгенерирован кнопкой «📝 Анонс» внизу."
        )
        return

    if payload.startswith("http"):
        await message.answer("⏳ Читаю статью...")
        article_text = extract_article_text(payload)
        if not article_text:
            await message.answer("❌ Не удалось извлечь текст. Пришли текст статьи целиком.")
            return
    else:
        article_text = payload

    await message.answer("⏳ Пишу анонс...")

    try:
        summary = generate_summary(article_text, length="standard")
    except Exception as e:
        logging.exception("GigaChat summary error")
        await message.answer(f"⚠️ Ошибка GigaChat: {e}")
        return

    await message.answer(
        f"📝 <b>Анонс:</b>\n{summary}",
        parse_mode="HTML",
        reply_markup=summary_length_keyboard(),
    )


@router.message(F.from_user.id == 1675347, F.text == "📝 Анонс")
async def handle_summary_button(message: Message):
    article_text = storage.get_article(message.from_user.id)
    if not article_text:
        await message.answer("❌ Не нашёл текст статьи. Пришли ссылку заново.")
        return

    await message.answer("⏳ Пишу анонс...")

    try:
        summary = generate_summary(article_text, length="standard")
    except Exception as e:
        logging.exception("GigaChat summary error")
        await message.answer(f"⚠️ Ошибка GigaChat: {e}")
        return

    await message.answer(
        f"📝 <b>Анонс:</b>\n{summary}",
        parse_mode="HTML",
        reply_markup=summary_length_keyboard(),
    )
