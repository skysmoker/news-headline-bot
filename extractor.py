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


async def extract_article_text(url: str) -> str | None:
    """
    Асинхронно скачивает страницу по ссылке и вытаскивает основной текст статьи.
    Возвращает текст или None, если извлечь не удалось.
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
        return None

    if not html:
        return None

    text = await asyncio.to_thread(trafilatura.extract, html, favor_precision=True)
    if not text or len(text.strip()) < 150:
        return None

    return text.strip()
