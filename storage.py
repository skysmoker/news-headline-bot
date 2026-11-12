import os
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles.db")


async def init_db() -> None:
    """Создаёт таблицу, если её ещё нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source_url TEXT,
                source_title TEXT,
                article_text TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_article(
    user_id: int,
    article_text: str,
    source_url: str | None = None,
    source_title: str | None = None,
) -> int:
    """Сохраняет новую статью, удаляет старые (оставляя 10) и возвращает id новой записи."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO articles (user_id, source_url, source_title, article_text, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, source_url, source_title, article_text),
        )
        article_id = cursor.lastrowid

        await db.execute(
            """
            DELETE FROM articles
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM articles
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 10
            )
            """,
            (user_id, user_id),
        )
        await db.commit()
        return article_id


async def get_article(user_id: int) -> tuple[int, str] | None:
    """Достаёт (id, article_text) последней сохранённой статьи или None."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, article_text FROM articles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return (row[0], row[1]) if row else None


async def get_articles(user_id: int, limit: int = 10) -> list[dict]:
    """Возвращает список последних статей для пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, source_url, source_title, length(article_text), updated_at "
            "FROM articles WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "source_url": r[1],
                    "source_title": r[2],
                    "length": r[3],
                    "updated_at": r[4],
                }
                for r in rows
            ]


async def get_article_by_id(article_id: int, user_id: int) -> str | None:
    """Достаёт текст статьи по id, если она принадлежит этому пользователю."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT article_text FROM articles WHERE id = ? AND user_id = ?",
            (article_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
