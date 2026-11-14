import html
import logging

from aiogram import Router, F
from aiogram.types import Message

import storage
from extractor import extract_article_text
from giga_client import generate_editorial_pack, HeadlinesResponse
from keyboards import main_keyboard

router = Router()

HEADLINE_ANGLES = [
    "Факт",
    "Цифра и масштаб",
    "Последствие",
    "Контраст",
    "Тезис",
]


def format_editorial_pack(headlines: HeadlinesResponse, summaries: dict[str, str]) -> str:
    lines = ["📰 <b>5 вариантов заголовка:</b>\n"]
    for i, title in enumerate(headlines.headlines, 1):
        angle = HEADLINE_ANGLES[i - 1] if i <= len(HEADLINE_ANGLES) else f"Вариант {i}"
        lines.append(f"<b>{i}. {angle}:</b>\n<code>{html.escape(title)}</code>\n")

    lines.append("───────────────\n")
    lines.append("📝 <b>3 варианта анонса:</b>\n")
    lines.append(f"<b>Короткий:</b>\n<code>{html.escape(summaries['short'])}</code>\n")
    lines.append(f"<b>Стандартный:</b>\n<code>{html.escape(summaries['standard'])}</code>\n")
    lines.append(f"<b>Развёрнутый:</b>\n<code>{html.escape(summaries['long'])}</code>")

    return "\n".join(lines)[:4096]


@router.message(F.text.startswith("http"))
async def handle_url(message: Message):
    url = message.text.strip()
    await message.answer("⏳ Ссылка получена, анализирую статью...")

    article_text, extracted_title = await extract_article_text(url)
    if not article_text:
        await message.answer(
            "❌ Не удалось извлечь текст. Возможно, сайт защищен от копирования и парсинга.\n"
            "Скопируйте текст статьи и пришлите его сюда, обработка будет продолжена."
        )
        return

    await storage.save_article(
        message.from_user.id,
        article_text,
        source_url=url,
        source_title=extracted_title,
    )

    await message.answer(
        f"📄 Извлечено символов: {len(article_text)}. Генерирую 5 заголовков и 3 варианта анонса..."
    )

    try:
        headlines, summaries = await generate_editorial_pack(article_text)
    except Exception as e:
        logging.exception("GigaChat error")
        await message.answer(f"⚠️ Ошибка GigaChat: {html.escape(str(e))}")
        return

    await message.answer(
        format_editorial_pack(headlines, summaries),
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


@router.message(F.text)
async def handle_text(message: Message):
    if len(message.text) < 100:
        await message.answer("Пришли ссылку (начинается с http: или https:) или текст статьи целиком.")
        return

    title = message.text.split("\n")[0].strip()[:120] or None
    await storage.save_article(
        message.from_user.id,
        message.text,
        source_url=None,
        source_title=title,
    )

    await message.answer("⏳ Генерирую 5 заголовков и 3 варианта анонса...")
    try:
        headlines, summaries = await generate_editorial_pack(message.text)
    except Exception as e:
        logging.exception("GigaChat error")
        await message.answer(f"⚠️ Ошибка GigaChat: {html.escape(str(e))}")
        return

    await message.answer(
        format_editorial_pack(headlines, summaries),
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )
