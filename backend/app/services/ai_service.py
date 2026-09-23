import json
from typing import Any
from pydantic import ValidationError
from ..config import OPENAI_API_KEY, OPENAI_MODEL, USE_AI
from ..schemas import AIAnalysis, ChallengeCardDraft

SYSTEM_RULES = """You are an assistant for the AI SANA Challenge Hub hackathon MVP.
STRICT RULES:
1. Use ONLY facts explicitly provided by the user in raw_description or answers.
2. NEVER invent company facts, data availability, metrics, deadlines, users, contacts, constraints, or technologies.
3. If a field is unknown, return null.
4. Generate clarification questions only for missing or ambiguous required fields.
5. Return valid JSON only, no markdown and no commentary.
6. Do not choose a student team and do not rank teams.
7. Do not use personal or sensitive participant attributes.
"""

REQUIRED_FIELDS = [
    "title",
    "context",
    "need",
    "users",
    "data_materials",
    "constraints",
    "expected_result",
    "success_criteria",
    "contact",
    "interaction_format",
]


def _safe_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def _openai_json(prompt: str) -> dict[str, Any]:
    if not (USE_AI and OPENAI_API_KEY):
        raise RuntimeError("OpenAI API is disabled or key is missing")

    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError(f"OpenAI SDK unavailable: {exc}") from exc

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_RULES},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return _safe_json(content)


def _fallback_analysis(raw_description: str) -> AIAnalysis:
    lower = raw_description.lower()
    extracted = {field: None for field in REQUIRED_FIELDS}

    extracted["need"] = raw_description.strip()
    if any(word in lower for word in ["насос", "оборуд", "полом", "отказ"]):
        extracted["title"] = "Задача по повышению надёжности оборудования"

    questions = [
        "Опишите текущий контекст: что происходит сейчас и что именно необходимо изменить?",
        "Какие данные, материалы, примеры или источники уже доступны команде?",
        "Какой конкретный результат должна подготовить студенческая команда?",
        "По каким измеримым критериям бизнес поймёт, что результат успешен?",
        "Кто будет основным пользователем будущего решения?",
        "Какие есть ограничения по срокам, технологиям, доступам или инфраструктуре?",
        "Кто будет контактным лицом и в каком формате бизнес готов консультировать команду?",
    ]
    missing = [f for f in REQUIRED_FIELDS if not extracted.get(f)]
    return AIAnalysis(extracted_fields=extracted, missing_fields=missing, questions=questions)


def analyze_description(raw_description: str) -> tuple[AIAnalysis, str]:
    prompt = f"""Analyze this business task description for completeness.
Required card fields: {', '.join(REQUIRED_FIELDS)}.
Return JSON with exactly these keys:
{{
  "extracted_fields": {{
    "title": string|null,
    "context": string|null,
    "need": string|null,
    "users": string|null,
    "data_materials": string|null,
    "constraints": string|null,
    "expected_result": string|null,
    "success_criteria": string|null,
    "contact": string|null,
    "interaction_format": string|null
  }},
  "missing_fields": [string],
  "questions": [at least 3 concise relevant questions]
}}
RAW_DESCRIPTION:
{raw_description}
"""
    try:
        data = _openai_json(prompt)
        parsed = AIAnalysis.model_validate(data)
        return parsed, "openai"
    except (Exception, ValidationError):
        return _fallback_analysis(raw_description), "fallback"


def _fallback_card(raw_description: str, answers: list[dict[str, str]]) -> ChallengeCardDraft:
    joined = "\n".join(f"Q: {a['question']}\nA: {a['answer']}" for a in answers)
    # The fallback intentionally avoids guessing semantics. It keeps user text visible
    # and leaves uncertain structured fields empty for manual editing/confirmation.
    return ChallengeCardDraft(
        title="Черновик бизнес-задачи",
        context=raw_description.strip(),
        need=raw_description.strip(),
        users=None,
        data_materials=joined if joined else None,
        constraints=None,
        expected_result=None,
        success_criteria=None,
        contact=None,
        interaction_format=None,
    )


def build_card(raw_description: str, answers: list[dict[str, str]]) -> tuple[ChallengeCardDraft, str]:
    answers_text = "\n".join(
        f"QUESTION: {item['question']}\nUSER_ANSWER: {item['answer']}" for item in answers
    )
    prompt = f"""Create a structured DRAFT challenge card using only the user's raw description and answers.
Return JSON with exactly these keys and null for unknown values:
{{
  "title": string|null,
  "context": string|null,
  "need": string|null,
  "users": string|null,
  "data_materials": string|null,
  "constraints": string|null,
  "expected_result": string|null,
  "success_criteria": string|null,
  "contact": string|null,
  "interaction_format": string|null
}}
Do not invent facts. Do not add a metric, deadline, contact, dataset or technology unless the user explicitly supplied it.

RAW_DESCRIPTION:
{raw_description}

ANSWERS:
{answers_text}
"""
    try:
        data = _openai_json(prompt)
        parsed = ChallengeCardDraft.model_validate(data)
        return parsed, "openai"
    except (Exception, ValidationError):
        return _fallback_card(raw_description, answers), "fallback"
