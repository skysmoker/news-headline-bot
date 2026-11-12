import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "articles.db")

def init_db():
    """Создаёт таблицу, если её ещё нет."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source_url TEXT,
            source_title TEXT,
            article_text TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_article(user_id: int, article_text: str, source_url: str = None, source_title: str = None):
    """Сохраняет новую статью и удаляет старые, оставляя последние 10."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO articles (user_id, source_url, source_title, article_text, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, source_url, source_title, article_text))

    cursor.execute("""
        DELETE FROM articles
        WHERE user_id = ? AND id NOT IN (
            SELECT id FROM articles
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
        )
    """, (user_id, user_id))

    conn.commit()
    conn.close()

def get_article(user_id: int) -> str | None:
    """Достаёт последнюю сохранённую статью или None."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT article_text FROM articles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else None

def get_articles(user_id: int, limit: int = 10) -> list[dict]:
    """Возвращает список последних статей для пользователя."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, source_url, source_title, length(article_text), updated_at "
        "FROM articles WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
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

def get_article_by_id(article_id: int, user_id: int) -> str | None:
    """Достаёт текст статьи по id, если она принадлежит этому пользователю."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT article_text FROM articles WHERE id = ? AND user_id = ?",
        (article_id, user_id)
    ).fetchone()
    conn.close()
    return row[0] if row else None

# Создаём таблицу при импорте модуля
init_db()
