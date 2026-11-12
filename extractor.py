import asyncio
import logging
import httpx
import trafilatura

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _parse_html(html: str) -> tuple[str | None, str | None]:
    """Синхронно извлекает текст и заголовок статьи из HTML через trafilatura."""
    extracted = trafilatura.bare_extraction(html, favor_precision=True)
    if not extracted:
        return None, None

    # Поддержка как dict, так и Document-объекта в разных версиях trafilatura
    if isinstance(extracted, dict):
        text = extracted.get("text")
        title = extracted.get("title")
    else:
        text = getattr(extracted, "text", None)
        title = getattr(extracted, "title", None)

    if not text or len(text.strip()) < 150:
        return None, None

    clean_text = text.strip()
    clean_title = (title.strip()[:120] if title and title.strip() else None) or (
        clean_text.split("\n")[0].strip()[:120] or None
    )
    return clean_text, clean_title


async def extract_article_text(url: str) -> tuple[str | None, str | None]:
    """
    Асинхронно скачивает страницу по ссылке и возвращает (текст_статьи, заголовок).
    Если извлечь не удалось, возвращает (None, None).
    """
    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except Exception as e:
        logging.warning(f"Ошибка при скачивании {url}: {e}")
        return None, None

    if not html:
        return None, None

    return await asyncio.to_thread(_parse_html, html)
