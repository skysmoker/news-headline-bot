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


class Headline(BaseModel):
    title: str = Field(description="Вариант заголовка")
    rationale: str = Field(description="Почему этот заголовок сработает")


class HeadlinesResponse(BaseModel):
    headlines: list[Headline] = Field(description="Ровно 5 вариантов заголовков")


SYSTEM_PROMPT = """Ты — шеф-редактор новостного и аналитического Telegram-канала.
Твоя задача — написать по тексту статьи ровно 5 сильных заголовков, которые цепляют умную аудиторию за счёт смысла, фактов и точной формулировки, а не за счёт дешёвой сенсационности.

Сделай 5 вариантов под разные углы подачи:
1. Фактологический — главная новость предельно прямо и ясно (кто, что сделал, с каким результатом).
2. С интригой без кликбейта — обозначает неочевидный поворот, скрытый механизм или причину, но не обманывает читателя.
3. С последствием — отвечает на вопрос «что теперь изменится» или «к чему это приведёт на практике».
4. С контрастом — столкновение ожиданий и реальности, «было — стало», конфликт интересов или позиций.
5. С деталью-крючком — выносит вперёд одну яркую цифру, точную цитату, редкий факт или конкретный прецедент из текста.

Жёсткие редакционные правила:
- Длина каждого заголовка: строго до 75 символов (оптимально 7–10 слов). Никаких длинных «простыней».
- Пиши живым русским языком, глаголами действия. Убирай канцелярит («осуществление», «проведение», «в рамках», «на фоне»).
- Запрещены вопросительные знаки, восклицания и многоточия.
- Запрещены жёлтые шаблоны: «Стало известно...», «Раскрыта правда...», «Вот что произошло...», «Названа причина...», «Эксперты объяснили...».
- Для каждого заголовка напиши 1 короткое предложение (rationale): на какой триггер внимания и для какой аудитории он сработает.

Верни ответ строго в формате JSON без markdown-обёрток и пояснений:
{"headlines": [{"title": "...", "rationale": "..."}]}"""


SUMMARY_PROMPTS = {
    "short": """Ты — редактор новостной ленты. Напиши предельно плотный короткий анонс статьи.
Правила:
- Объём: 12–18 слов (примерно 80–120 символов).
- Ровно 1 предложение.
- Сразу главный факт: кто, что сделал и главный результат.
- Никакой воды, вводных слов («в статье рассказывается», «автор отмечает»), вопросов и восклицаний.""",

    "standard": """Ты — редактор новостного и аналитического медиа. Напиши классический информационный анонс статьи (лид).
Правила:
- Объём: 22–32 слова (примерно 150–210 символов).
- 1–2 предложения по принципу перевёрнутой пирамиды: в первом — главная новость, во втором — ключевой контекст или масштаб.
- Пиши конкретно: имена, компании, цифры, суть решения.
- Без канцелярита, без клише «стало известно / эксперты считают», без вопросов и восклицаний.""",

    "long": """Ты — редактор аналитического Telegram-канала. Напиши развёрнутый анонс-подводку к статье.
Правила:
- Объём: 35–48 слов (примерно 230–300 символов).
- 2–3 предложения: главная новость, ключевые аргументы или детали из текста и практический вывод (почему это важно).
- Плотный фактологический стиль без воды и пересказа структуры статьи («в материале рассматриваются...»).
- Без вопросов и восклицаний.""",
}


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


def _prepare_text(article_text: str, max_chars: int = 6000) -> str:
    """Если статья длинная, сохраняет начало (4500 симв.) и финал с выводами (1500 симв.)."""
    text = article_text.strip()
    if len(text) <= max_chars:
        return text
    head = text[:4500].rstrip()
    tail = text[-1500:].lstrip()
    return f"{head}\n\n[...середина статьи сокращена...]\n\n{tail}"


async def generate_headlines(article_text: str) -> HeadlinesResponse:
    prepared = _prepare_text(article_text)
    last_error = None
    client = _get_shared_client()

    for attempt in range(3):
        try:
            chat = Chat(
                model="GigaChat-2",
                temperature=0.7,
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT),
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
            return HeadlinesResponse(**data)
        except Exception as e:
            last_error = str(e)
            if attempt < 2:
                await asyncio.sleep(2)

    raise RuntimeError(f"Не удалось получить заголовки после 3 попыток. Последняя ошибка: {last_error}")


async def generate_summary(article_text: str, length: str = "standard") -> str:
    prepared = _prepare_text(article_text)
    prompt = SUMMARY_PROMPTS.get(length, SUMMARY_PROMPTS["standard"])
    last_error = None
    client = _get_shared_client()

    for attempt in range(3):
        try:
            chat = Chat(
                model="GigaChat-2-Max",
                temperature=0.3,
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=prompt),
                    Messages(role=MessagesRole.USER, content=prepared),
                ],
            )
            response = await client.achat(chat)
            content = response.choices[0].message.content.strip()
            if not content:
                raise ValueError("Пустой ответ от GigaChat")
            return content
        except Exception as e:
            last_error = str(e)
            if attempt < 2:
                await asyncio.sleep(2)

    raise RuntimeError(f"Не удалось сгенерировать анонс после 3 попыток. Последняя ошибка: {last_error}")
