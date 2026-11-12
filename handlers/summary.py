import html
import logging

from aiogram import Router, F
from aiogram.types import Message

import storage
from extractor import extract_article_text
from giga_client import generate_summary
from keyboards import summary_length_keyboard

router = Router()


@router.message(F.text.startswith("/summary"))
async def handle_summary_command(message: Message):
    payload = message.text[len("/summary"):].strip()

    if not payload:
        await message.answer(
            "Использование:\n"
            "/summary <ссылка или текст> — сгенерировать анонс по статье\n"
            "Анонс по последней статье также можно создать кнопкой «📝 Анонс» внизу."
        )
        return

    if payload.startswith("http"):
        await message.answer("⏳ Читаю статью...")
        article_text = await extract_article_text(payload)
        if not article_text:
            await message.answer("❌ Не удалось извлечь текст. Пришли текст статьи целиком.")
            return
        source_url = payload
    else:
        article_text = payload
        source_url = None

    title = article_text.split("\n")[0].strip()[:100] or None
    article_id = await storage.save_article(
        message.from_user.id,
        article_text,
        source_url=source_url,
        source_title=title,
    )

    await message.answer("⏳ Пишу анонс...")

    try:
        summary = await generate_summary(article_text, length="standard")
    except Exception as e:
        logging.exception("GigaChat summary error")
        await message.answer(f"⚠️ Ошибка GigaChat: {html.escape(str(e))}")
        return

    await message.answer(
        f"📝 <b>Анонс:</b>\n{html.escape(summary)}",
        parse_mode="HTML",
        reply_markup=summary_length_keyboard(article_id=article_id),
    )


@router.message(F.text == "📝 Анонс")
async def handle_summary_button(message: Message):
    article = await storage.get_article(message.from_user.id)
    if not article:
        await message.answer("❌ Не нашёл текст статьи. Пришли ссылку или текст заново.")
        return

    article_id, article_text = article
    await message.answer("⏳ Пишу анонс...")

    try:
        summary = await generate_summary(article_text, length="standard")
    except Exception as e:
        logging.exception("GigaChat summary error")
        await message.answer(f"⚠️ Ошибка GigaChat: {html.escape(str(e))}")
        return

    await message.answer(
        f"📝 <b>Анонс:</b>\n{html.escape(summary)}",
        parse_mode="HTML",
        reply_markup=summary_length_keyboard(article_id=article_id),
    )
