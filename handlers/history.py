from aiogram import Router, F
from aiogram.types import Message
import storage

router = Router()


@router.message(F.from_user.id == 1675347, F.text.in_({"/history", "📚 История"}))
async def handle_history(message: Message):
    articles = storage.get_articles(message.from_user.id, limit=10)

    if not articles:
        await message.answer("📭 История пуста. Пришли ссылку или текст статьи — я сохраню.")
        return

    response = "📚 <b>Последние статьи:</b>\n\n"
    for a in articles:
        time_str = a["updated_at"][:16]
        title = a["source_title"] or "(без названия)"
        if len(title) > 80:
            title = title[:77] + "..."

        response += f"<b>#{a['id']}</b> — {title}\n"
        response += f"   <i>{a['length']} символов, {time_str}</i>\n"
        if a["source_url"]:
            response += f"   <a href='{a['source_url']}'>Ссылка на статью</a>\n"
        response += "\n"

    response += "Чтобы написать анонс по последней статье, нажми кнопку «📝 Анонс» внизу."
    await message.answer(response, parse_mode="HTML", disable_web_page_preview=True)
