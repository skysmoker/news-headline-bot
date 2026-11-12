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
            [KeyboardButton(text="📚 История"), KeyboardButton(text="📝 Анонс")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def summary_length_keyboard(article_id: int | None = None) -> InlineKeyboardMarkup:
    """Кнопки выбора длины анонса с привязкой к конкретной статье."""
    suffix = f":{article_id}" if article_id is not None else ""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Короче", callback_data=f"summary_len:short{suffix}"),
                InlineKeyboardButton(text="Стандарт", callback_data=f"summary_len:standard{suffix}"),
                InlineKeyboardButton(text="Длиннее", callback_data=f"summary_len:long{suffix}"),
            ]
        ]
    )


def history_articles_keyboard(articles: list[dict]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки для генерации анонса по любой статье из истории (рядами по 5 штук)."""
    buttons = [
        InlineKeyboardButton(
            text=f"📝 #{a['id']}",
            callback_data=f"summary_by_id:{a['id']}",
        )
        for a in articles
    ]
    rows = [buttons[i : i + 5] for i in range(0, len(buttons), 5)]
    return InlineKeyboardMarkup(inline_keyboard=rows)
