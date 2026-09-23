from typing import Any

WEIGHTS = {
    "context": 10,
    "need": 10,
    "data_materials": 20,
    "expected_result": 15,
    "success_criteria": 15,
    "constraints": 10,
    "users": 10,
    "contact": 5,
    "interaction_format": 5,
}

LABELS = {
    "context": "Контекст",
    "need": "Потребность",
    "data_materials": "Данные и материалы",
    "expected_result": "Ожидаемый результат",
    "success_criteria": "Критерии успеха",
    "constraints": "Ограничения",
    "users": "Пользователи",
    "contact": "Контакт",
    "interaction_format": "Формат взаимодействия",
}


def _filled(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) >= 2


def readiness_level(score: int) -> str:
    if score <= 39:
        return "Черновик"
    if score <= 69:
        return "Рабочая"
    if score <= 89:
        return "Готовая"
    return "Приоритетная"


def calculate_score(card: dict, confirmed: bool) -> dict:
    breakdown = []
    missing = []
    total = 0

    for field, weight in WEIGHTS.items():
        is_filled = _filled(card.get(field))
        points = weight if confirmed and is_filled else 0
        total += points
        if not is_filled:
            missing.append(field)
        breakdown.append(
            {
                "field": field,
                "label": LABELS[field],
                "weight": weight,
                "points": points,
                "filled": is_filled,
            }
        )

    return {
        "score": total,
        "readiness_level": readiness_level(total),
        "breakdown": breakdown,
        "missing_fields": missing,
        "confirmed": confirmed,
    }


def preview_score(card: dict) -> dict:
    """Preview only. Official score is calculated after human confirmation."""
    total = 0
    breakdown = []
    missing = []
    for field, weight in WEIGHTS.items():
        is_filled = _filled(card.get(field))
        points = weight if is_filled else 0
        total += points
        if not is_filled:
            missing.append(field)
        breakdown.append(
            {
                "field": field,
                "label": LABELS[field],
                "weight": weight,
                "points": points,
                "filled": is_filled,
            }
        )
    return {
        "score": total,
        "readiness_level": readiness_level(total),
        "breakdown": breakdown,
        "missing_fields": missing,
        "confirmed": False,
        "is_preview": True,
    }
