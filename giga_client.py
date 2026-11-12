import os
import time
import json
from pydantic import BaseModel, Field
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

class Headline(BaseModel):
    title: str = Field(description="Вариант заголовка")
    rationale: str = Field(description="Почему этот заголовок сработает")

class HeadlinesResponse(BaseModel):
    headlines: list[Headline] = Field(description="Ровно 5 вариантов заголовков")

SYSTEM_PROMPT = """Ты — главный редактор аналитического отдела крупного медиа с 20-летним опытом.
Твоя специализация — создание заголовков, которые одновременно привлекают внимание и точно отражают суть материала.

Тебе дан текст статьи. Предложи ровно 5 вариантов заголовка для публикации в Telegram-канале.
Заголовки должны быть разными по стилю:
1. Фактологический (суть в одном предложении)
2. С интригой (но без кликбейта)
3. С последствием (что это значит, к чему приведёт)
4. С контрастом (было — стало, одни — другие)
5. С деталью-крючком (одна яркая цифра, имя или реплика из статьи)

Для каждого варианта напиши одно предложение, объясняющее, на какую аудиторию и почему он сработает.
Избегай откровенного кликбейта. Заголовок должен вызывать доверие у интеллектуальной аудитории.
Ни в одном заголовке не используй вопросительную интонацию и знак вопроса.
Верни ответ строго в формате JSON: {"headlines": [{"title": "...", "rationale": "..."}]}. Без markdown-обёрток, без комментариев."""


def generate_headlines(article_text: str) -> HeadlinesResponse:
    truncated = article_text[:6000]
    last_error = None

    for attempt in range(3):  # 3 попытки
        with GigaChat(
            credentials=os.getenv("GIGACHAT_CREDENTIALS"),
            ca_bundle_file="/home/skysmoker/news-headline-bot/russian_trusted_root_ca.crt"
        ) as client:
            chat = Chat(
                model="GigaChat-2",
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT),
                    Messages(role=MessagesRole.USER, content=truncated),
                ],
            )
            response = client.chat(chat)
            content = response.choices[0].message.content.strip()

            # Чистим возможные markdown-обёртки
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            if not content:
                last_error = "Пустой ответ от GigaChat"
                time.sleep(2)
                continue

            try:
                data = json.loads(content)
                return HeadlinesResponse(**data)
            except Exception as e:
                last_error = str(e)
                time.sleep(2)

    raise Exception(f"Не удалось получить заголовки после 3 попыток. Последняя ошибка: {last_error}")

SUMMARY_PROMPTS = {
    "short": """Ты — главный редактор аналитического отдела крупного медиа.
Напиши краткий анонс статьи для новостного портала.
Требования:
- Длина: 80–120 символов.
- Одно предложение, без воды и канцелярита.
- Суть: что произошло и почему это важно.
- Без кликбейта, без вопросов, без восклицаний.""",

    "standard": """Ты — главный редактор аналитического отдела крупного медиа.
Напиши краткий анонс статьи для новостного портала.
Требования:
- Длина: 150–200 символов.
- Одно-два предложения, без воды и канцелярита.
- Суть: что произошло, кто участвовал, почему это важно.
- Без кликбейта, без вопросов, без восклицаний.""",

    "long": """Ты — главный редактор аналитического отдела крупного медиа.
Напиши краткий анонс статьи для новостного портала.
Требования:
- Длина: 230–280 символов.
- Два-три предложения, без воды и канцелярита.
- Суть: что произошло, кто участвовал, почему это важно, какие детали.
- Без кликбейта, без вопросов, без восклицаний.""",
}


def generate_summary(article_text: str, length: str = "standard") -> str:
    truncated = article_text[:6000]
    prompt = SUMMARY_PROMPTS.get(length, SUMMARY_PROMPTS["standard"])

    with GigaChat(
        credentials=os.getenv("GIGACHAT_CREDENTIALS"),
        ca_bundle_file="/home/skysmoker/news-headline-bot/russian_trusted_root_ca.crt"
    ) as client:
        chat = Chat(
            model="GigaChat-2-Max",
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=prompt),
                Messages(role=MessagesRole.USER, content=truncated),
            ],
        )
        response = client.chat(chat)
        return response.choices[0].message.content.strip()
