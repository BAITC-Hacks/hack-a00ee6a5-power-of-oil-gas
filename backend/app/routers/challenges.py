import json
from fastapi import APIRouter, HTTPException, Query
from ..database import db_session
from ..schemas import ChallengeCreate, BuildCardRequest, ChallengeConfirm
from ..services.ai_service import analyze_description, build_card
from ..services.rating_service import calculate_score, preview_score

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


def _row_to_dict(row):
    if row is None:
        return None
    data = dict(row)
    data["constraints"] = data.pop("constraints_text")
    for key in ("ai_questions", "answers"):
        try:
            data[key] = json.loads(data[key] or "[]")
        except json.JSONDecodeError:
            data[key] = []
    data["is_confirmed"] = bool(data["is_confirmed"])
    card = {
        "context": data.get("context"),
        "need": data.get("need"),
        "data_materials": data.get("data_materials"),
        "expected_result": data.get("expected_result"),
        "success_criteria": data.get("success_criteria"),
        "constraints": data.get("constraints"),
        "users": data.get("users"),
        "contact": data.get("contact"),
        "interaction_format": data.get("interaction_format"),
    }
    data["rating"] = calculate_score(card, confirmed=data["is_confirmed"])
    return data


@router.post("/analyze")
def create_and_analyze(payload: ChallengeCreate):
    analysis, ai_mode = analyze_description(payload.raw_description)
    fields = analysis.extracted_fields

    with db_session() as conn:
        cursor = conn.execute(
            """
            INSERT INTO challenges (
                raw_description, industry, title, context, need, users, data_materials,
                constraints_text, expected_result, success_criteria, contact,
                interaction_format, ai_questions, status, is_confirmed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0)
            """,
            (
                payload.raw_description, payload.industry, fields.get("title"), fields.get("context"),
                fields.get("need"), fields.get("users"), fields.get("data_materials"),
                fields.get("constraints"), fields.get("expected_result"), fields.get("success_criteria"),
                fields.get("contact"), fields.get("interaction_format"),
                json.dumps(analysis.questions, ensure_ascii=False),
            ),
        )
        challenge_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()

    card = {
        "context": fields.get("context"),
        "need": fields.get("need"),
        "data_materials": fields.get("data_materials"),
        "expected_result": fields.get("expected_result"),
        "success_criteria": fields.get("success_criteria"),
        "constraints": fields.get("constraints"),
        "users": fields.get("users"),
        "contact": fields.get("contact"),
        "interaction_format": fields.get("interaction_format"),
    }

    return {
        "challenge": _row_to_dict(row),
        "missing_fields": analysis.missing_fields,
        "questions": analysis.questions,
        "preview_rating": preview_score(card),
        "ai_mode": ai_mode,
    }


@router.post("/{challenge_id}/build-card")
def build_challenge_card(challenge_id: int, payload: BuildCardRequest):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    answers = [item.model_dump() for item in payload.answers]
    card, ai_mode = build_card(row["raw_description"], answers)
    values = card.model_dump()

    with db_session() as conn:
        conn.execute(
            """
            UPDATE challenges SET
                title=?, context=?, need=?, users=?, data_materials=?, constraints_text=?,
                expected_result=?, success_criteria=?, contact=?, interaction_format=?,
                answers=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                values.get("title"), values.get("context"), values.get("need"), values.get("users"),
                values.get("data_materials"), values.get("constraints"), values.get("expected_result"),
                values.get("success_criteria"), values.get("contact"), values.get("interaction_format"),
                json.dumps(answers, ensure_ascii=False), challenge_id,
            ),
        )
        updated = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()

    preview = preview_score(values)
    return {"challenge": _row_to_dict(updated), "preview_rating": preview, "ai_mode": ai_mode}


@router.put("/{challenge_id}/confirm")
def confirm_challenge(challenge_id: int, payload: ChallengeConfirm):
    values = payload.model_dump()
    rating = calculate_score(values, confirmed=True)

    with db_session() as conn:
        exists = conn.execute("SELECT id FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Challenge not found")
        conn.execute(
            """
            UPDATE challenges SET
                title=?, context=?, need=?, users=?, data_materials=?, constraints_text=?,
                expected_result=?, success_criteria=?, contact=?, interaction_format=?,
                score=?, readiness_level=?, is_confirmed=1, status='confirmed', updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                values.get("title"), values.get("context"), values.get("need"), values.get("users"),
                values.get("data_materials"), values.get("constraints"), values.get("expected_result"),
                values.get("success_criteria"), values.get("contact"), values.get("interaction_format"),
                rating["score"], rating["readiness_level"], challenge_id,
            ),
        )
        updated = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    return {"challenge": _row_to_dict(updated), "rating": rating}


@router.post("/{challenge_id}/publish")
def publish_challenge(challenge_id: int):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Challenge not found")
        if not row["is_confirmed"]:
            raise HTTPException(status_code=400, detail="Challenge must be manually confirmed before publication")
        conn.execute("UPDATE challenges SET status='published', updated_at=CURRENT_TIMESTAMP WHERE id=?", (challenge_id,))
        updated = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    return {"challenge": _row_to_dict(updated)}


@router.get("")
def list_challenges(
    industry: str | None = Query(default=None),
    readiness: str | None = Query(default=None),
    include_drafts: bool = Query(default=False),
):
    clauses = [] if include_drafts else ["status = 'published'"]
    params = []
    if industry:
        clauses.append("industry = ?")
        params.append(industry)
    if readiness:
        clauses.append("readiness_level = ?")
        params.append(readiness)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM challenges {where} ORDER BY score DESC, updated_at DESC"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
    return {"items": [_row_to_dict(row) for row in rows]}


@router.get("/{challenge_id}")
def get_challenge(challenge_id: int):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {"challenge": _row_to_dict(row)}
