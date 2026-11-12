import html
from aiogram import Router, F
from aiogram.types import Message

import storage
from keyboards import history_articles_keyboard

router = Router()


@router.message(F.text.in_({"/history", "📚 История"}))
async def handle_history(message: Message):
    articles = await storage.get_articles(message.from_user.id, limit=10)

    if not articles:
        await message.answer("📭 История пуста. Пришли ссылку или текст статьи — я сохраню.")
        return

    response = "📚 <b>Последние статьи:</b>\n\n"
    for a in articles:
        time_str = html.escape(str(a["updated_at"])[:16])
        raw_title = a["source_title"] or "(без названия)"
        if len(raw_title) > 80:
            raw_title = raw_title[:77] + "..."
        title = html.escape(raw_title)

        response += f"<b>#{a['id']}</b> — {title}\n"
        response += f"   <i>{a['length']} символов, {time_str}</i>\n"
        if a["source_url"]:
            safe_url = html.escape(a["source_url"], quote=True)
            response += f"   <a href='{safe_url}'>Ссылка на статью</a>\n"
        response += "\n"

    response += "Нажми на номер статьи ниже, чтобы сгенерировать по ней анонс:"
    await message.answer(
        response,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=history_articles_keyboard(articles),
    )
