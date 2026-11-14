from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def main_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная клавиатура внизу чата."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 История")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def history_articles_keyboard(articles: list[dict]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки для повторной генерации пакета по любой статье из истории (рядами по 5 штук)."""
    buttons = [
        InlineKeyboardButton(
            text=f"📰 #{a['id']}",
            callback_data=f"summary_by_id:{a['id']}",
        )
        for a in articles
    ]
    rows = [buttons[i : i + 5] for i in range(0, len(buttons), 5)]
    return InlineKeyboardMarkup(inline_keyboard=rows)
