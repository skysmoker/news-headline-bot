import asyncio
import json
import os
import re
from pydantic import BaseModel, Field
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CA_CERT = os.path.join(BASE_DIR, "russian_trusted_root_ca.crt")

_shared_client: GigaChat | None = None


class HeadlinesResponse(BaseModel):
    headlines: list[str] = Field(description="Ровно 5 вариантов заголовков")


class SummariesPack(BaseModel):
    short: str = Field(description="Короткий анонс (12-18 слов)")
    standard: str = Field(description="Стандартный анонс (22-32 слова)")
    long: str = Field(description="Развёрнутый анонс (35-48 слов)")


class EditorialPackResponse(BaseModel):
    headlines: list[str]
    summaries: SummariesPack


EDITORIAL_SYSTEM_PROMPT = """Ты — шеф-редактор делового и аналитического медиа (уровня РБК, Коммерсантъ, Forbes).
Твоя задача — по тексту статьи подготовить редакционный пакет: ровно 5 сильных заголовков и 3 варианта анонса разной длины.

ЧАСТЬ 1. ПЯТЬ ЗАГОЛОВКОВ (строго под эти углы подачи):
1. Фактологический (суть) — кто, что сделал и с каким итогом, предельно прямо и ясно.
2. С опорой на цифру или масштаб — выносит вперёд главную сумму, процент, срок или охват из текста.
3. Практическое последствие — отвечает на вопрос «что теперь изменится на практике».
4. Конфликт или парадокс — столкновение позиций, интересов либо ожиданий и реальности.
5. Смысловой вывод (тезис) — ёмкая формулировка главного итога статьи, удобная для репоста.

Правила для заголовков:
- Длина каждого заголовка: строго до 75 символов (оптимально 7–10 слов).
- Живой русский язык, глаголы действия. Без канцелярита («осуществление», «проведение», «в рамках», «на фоне», «реализация», «данный»).
- Запрещены вопросительные знаки, восклицания, многоточия и точка в конце заголовка.
- Запрещены жёлтые шаблоны: «Стало известно...», «Раскрыта правда...», «Вот что произошло...», «Названа причина...», «Эксперты объяснили...».
- Никаких пояснений — только сами заголовки.

ЧАСТЬ 2. ТРИ ВАРИАНТА АНОНСА:
- short (Короткий): 12–18 слов (80–120 символов), ровно 1 предложение. Сразу главный факт: кто, что сделал и главный результат. Без вводных слов («в статье рассказывается...»), вопросов и восклицаний.
- standard (Стандартный): 22–32 слова (150–210 символов), 1–2 предложения по принципу перевёрнутой пирамиды (главная новость + ключевой контекст, цифры, имена). Без канцелярита и вопросов.
- long (Развёрнутый): 35–48 слов (230–300 символов), 2–3 предложения для Telegram-канала (главная новость, ключевые аргументы/детали из текста и практический вывод). Плотный фактологический стиль без воды и пересказа структуры статьи.

Верни ответ строго в формате валидного JSON без markdown-обёрток и комментариев:
{
  "headlines": [
    "Заголовок 1",
    "Заголовок 2",
    "Заголовок 3",
    "Заголовок 4",
    "Заголовок 5"
  ],
  "summaries": {
    "short": "Текст короткого анонса",
    "standard": "Текст стандартного анонса",
    "long": "Текст развёрнутого анонса"
  }
}"""


def _get_shared_client() -> GigaChat:
    """Возвращает единый экземпляр клиента GigaChat (переиспользует OAuth-токен 30 минут)."""
    global _shared_client
    if _shared_client is None:
        ca_file = os.getenv("GIGACHAT_CA_CERT", DEFAULT_CA_CERT)
        kwargs = {"credentials": os.getenv("GIGACHAT_CREDENTIALS")}
        if os.path.exists(ca_file):
            kwargs["ca_bundle_file"] = ca_file
        _shared_client = GigaChat(**kwargs)
    return _shared_client


async def close_client() -> None:
    """Корректно закрывает HTTP-сессию клиента GigaChat при остановке бота."""
    global _shared_client
    if _shared_client is not None:
        await _shared_client.aclose()
        _shared_client = None


def _prepare_text(article_text: str, max_chars: int = 12000) -> str:
    """Если статья длинная, сохраняет начало (9000 симв.) и финал с выводами (3000 симв.)."""
    text = article_text.strip()
    if len(text) <= max_chars:
        return text
    head = text[:9000].rstrip()
    tail = text[-3000:].lstrip()
    return f"{head}\n\n[...середина статьи сокращена...]\n\n{tail}"


def _clean_headline(raw: str) -> str:
    """Убирает нумерацию, внешние кавычки и висячую точку в конце заголовка."""
    cleaned = re.sub(r"^\d+[\.\)]\s*", "", raw.strip())
    if (cleaned.startswith("«") and cleaned.endswith("»")) or (
        cleaned.startswith('"') and cleaned.endswith('"')
    ):
        cleaned = cleaned[1:-1].strip()
    return cleaned.rstrip(".")


async def generate_editorial_pack(article_text: str) -> tuple[HeadlinesResponse, dict[str, str]]:
    """Генерирует 5 заголовков и 3 варианта анонса за один запрос к GigaChat-2-Max."""
    prepared = _prepare_text(article_text)
    last_error = None
    client = _get_shared_client()

    for attempt in range(3):
        try:
            chat = Chat(
                model="GigaChat-2-Max",
                temperature=0.6,
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=EDITORIAL_SYSTEM_PROMPT),
                    Messages(role=MessagesRole.USER, content=prepared),
                ],
            )
            response = await client.achat(chat)
            content = response.choices[0].message.content.strip()

            if not content:
                raise ValueError("Пустой ответ от GigaChat")

            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise ValueError("JSON не найден в ответе модели")

            data = json.loads(match.group(0))
            raw_headlines = data.get("headlines", [])
            cleaned_headlines = [
                _clean_headline(item["title"] if isinstance(item, dict) else str(item))
                for item in raw_headlines
                if (item.get("title") if isinstance(item, dict) else str(item)).strip()
            ]
            data["headlines"] = cleaned_headlines[:5]

            pack = EditorialPackResponse(**data)
            summaries = {
                "short": pack.summaries.short.strip(),
                "standard": pack.summaries.standard.strip(),
                "long": pack.summaries.long.strip(),
            }
            return HeadlinesResponse(headlines=pack.headlines), summaries
        except Exception as e:
            last_error = str(e)
            if attempt < 2:
                await asyncio.sleep(3 * (attempt + 1))

    raise RuntimeError(f"Не удалось сгенерировать материал после 3 попыток. Последняя ошибка: {last_error}")
