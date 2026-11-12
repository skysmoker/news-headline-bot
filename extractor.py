import trafilatura

def extract_article_text(url: str) -> str | None:
    """
    Скачивает страницу по ссылке и вытаскивает основной текст статьи.
    Возвращает текст или None, если извлечь не удалось.
    """
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    text = trafilatura.extract(downloaded, favor_precision=True)
    return text
