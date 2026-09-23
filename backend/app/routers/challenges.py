import json
from fastapi import APIRouter, HTTPException, Query, Depends
from ..database import db_session
from ..schemas import ChallengeCreate, BuildCardRequest, ChallengeConfirm, ChallengeCardDraft
from ..services.ai_service import analyze_description, build_card
from ..services.rating_service import calculate_score, preview_score, assess_card, card_hash
from .auth import current_user, business_user, owned_challenge

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.post('/preview')
def preview_card(payload: ChallengeCardDraft, user=Depends(business_user)):
    return preview_score(payload.model_dump())


def _applicant_counts(conn, ids):
    if not ids:
        return {}
    slots=','.join('?' for _ in ids)
    rows=conn.execute(f"""SELECT challenge_id, COUNT(DISTINCT
        CASE WHEN team_id IS NOT NULL THEN 'team:' || team_id
             WHEN owner_id IS NOT NULL THEN 'user:' || owner_id
             ELSE 'proposal:' || id END) AS count
        FROM proposals WHERE challenge_id IN ({slots}) GROUP BY challenge_id""",ids).fetchall()
    return {row['challenge_id']:row['count'] for row in rows}


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
    # Old drafts had plain strings instead of field-bound questions. Rebuild their
    # question set locally; this does not call the external API or alter stored facts.
    if data['ai_questions'] and isinstance(data['ai_questions'][0], str):
        from ..services.ai_service import _questions
        data['ai_questions'] = [q.model_dump() for q in _questions(data, data['raw_description'])]
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
    data["rating"] = json.loads(data.pop("rating_json") or "{}") or calculate_score(card, confirmed=data["is_confirmed"])
    return data


@router.post("/analyze")
def create_and_analyze(payload: ChallengeCreate, user=Depends(business_user)):
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
                json.dumps([q.model_dump() for q in analysis.questions], ensure_ascii=False),
            ),
        )
        challenge_id = cursor.lastrowid
        conn.execute('UPDATE challenges SET ai_mode=?,owner_id=? WHERE id=?', (ai_mode, user['id'], challenge_id))
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
def build_challenge_card(challenge_id: int, payload: BuildCardRequest, user=Depends(business_user)):
    with db_session() as conn:
        row = owned_challenge(conn, challenge_id, user)
    if row is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if row['is_confirmed']:
        raise HTTPException(status_code=409, detail='Подтверждённую карточку изменяйте через редактор и повторное подтверждение.')

    answers = [item.model_dump() for item in payload.answers]
    stored_questions = _row_to_dict(row)['ai_questions']
    allowed = {q['field']: q['question'] for q in stored_questions if isinstance(q, dict)}
    seen = set()
    for answer in answers:
        field = answer.get('field')
        if field not in allowed or field in seen or answer['question'] != allowed[field]:
            raise HTTPException(status_code=422, detail='Вопросы изменились. Перезагрузите страницу и повторите ответы.')
        seen.add(field)
    current = _row_to_dict(row)
    card, ai_mode = build_card(row["raw_description"], answers, current)
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
def confirm_challenge(challenge_id: int, payload: ChallengeConfirm, user=Depends(business_user)):
    values = payload.model_dump()
    with db_session() as conn:
        owned_challenge(conn,challenge_id,user)
        assessment=conn.execute('SELECT * FROM assessments WHERE id=? AND challenge_id=? AND card_hash=?',(payload.assessment_id,challenge_id,card_hash(values))).fetchone()
    if not assessment:
        raise HTTPException(409,'Карточка изменилась или ещё не оценена. Выполните оценку перед подтверждением.')
    rating=json.loads(assessment['rating_json'])
    rating.update(confirmed=True,is_preview=False)

    with db_session() as conn:
        exists = conn.execute("SELECT id FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Challenge not found")
        conn.execute(
            """
            UPDATE challenges SET
                title=?, context=?, need=?, users=?, data_materials=?, constraints_text=?,
                expected_result=?, success_criteria=?, contact=?, interaction_format=?,
                score=?, readiness_level=?, rating_json=?, is_confirmed=1, status=CASE WHEN status='published' THEN 'published' ELSE 'confirmed' END, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                values.get("title"), values.get("context"), values.get("need"), values.get("users"),
                values.get("data_materials"), values.get("constraints"), values.get("expected_result"),
                values.get("success_criteria"), values.get("contact"), values.get("interaction_format"),
                rating["score"], rating["readiness_level"], json.dumps(rating,ensure_ascii=False), challenge_id,
            ),
        )
        updated = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    return {"challenge": _row_to_dict(updated), "rating": rating}


@router.post("/{challenge_id}/publish")
def publish_challenge(challenge_id: int, user=Depends(business_user)):
    with db_session() as conn:
        row = owned_challenge(conn,challenge_id,user)
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
    user=Depends(current_user),
):
    clauses = ["owner_id = ?"] if user["role"] == "business" else ["status = 'published'"]
    params = [user["id"]] if user["role"] == "business" else []
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
        counts = _applicant_counts(conn, [row['id'] for row in rows])
    items = [_row_to_dict(row) for row in rows]
    for item in items:
        item["applicant_count"] = counts.get(item["id"],0)
    if user["role"] == "performer":
        for item in items:
            for key in ("answers", "ai_questions", "raw_description"):
                item.pop(key, None)
    return {"items": items}


@router.get("/{challenge_id}")
def get_challenge(challenge_id: int, user=Depends(current_user)):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    if row is None or (user["role"] == "business" and row["owner_id"] != user["id"]) or (user["role"] == "performer" and row["status"] != "published"):
        raise HTTPException(status_code=404, detail="Задача недоступна этому аккаунту")
    item=_row_to_dict(row)
    with db_session() as conn:
        item["applicant_count"] = _applicant_counts(conn,[challenge_id]).get(challenge_id,0)
    if user["role"] == "performer":
        item.pop("answers",None)
        item.pop("ai_questions",None)
        item.pop("raw_description",None)
    return {"challenge": item}


@router.post('/{challenge_id}/assess')
def assess_challenge(challenge_id:int,payload:ChallengeCardDraft,user=Depends(business_user)):
    values=payload.model_dump()
    fingerprint=card_hash(values)
    with db_session() as conn:
        owned_challenge(conn,challenge_id,user)
        previous=conn.execute('SELECT * FROM assessments WHERE challenge_id=? AND card_hash=?',(challenge_id,fingerprint)).fetchone()
    if previous and json.loads(previous['rating_json']).get('mode') == 'openai':
        return {'assessment_id':previous['id'],'rating':json.loads(previous['rating_json']),'cached':True}
    rating=assess_card(values)
    with db_session() as conn:
        conn.execute('INSERT INTO assessments(challenge_id,card_hash,rating_json) VALUES(?,?,?) ON CONFLICT(challenge_id,card_hash) DO UPDATE SET rating_json=excluded.rating_json,created_at=CURRENT_TIMESTAMP',(challenge_id,fingerprint,json.dumps(rating,ensure_ascii=False)))
        record=conn.execute('SELECT id FROM assessments WHERE challenge_id=? AND card_hash=?',(challenge_id,fingerprint)).fetchone()
    return {'assessment_id':record['id'],'rating':rating,'cached':False}
