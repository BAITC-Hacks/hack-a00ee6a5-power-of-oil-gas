from fastapi import APIRouter, HTTPException
from ..database import db_session
from ..schemas import ProposalCreate, ProposalDecision

router = APIRouter(prefix="/api", tags=["proposals"])


def _proposal_dict(row):
    return dict(row) if row else None


@router.get("/teams")
def list_teams():
    import json
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM teams ORDER BY id").fetchall()
    items = []
    for row in rows:
        item = dict(row)
        for key in ("interests", "skills", "technologies"):
            item[key] = json.loads(item[key] or "[]")
        items.append(item)
    return {"items": items}


@router.post("/proposals")
def create_proposal(payload: ProposalCreate):
    with db_session() as conn:
        challenge = conn.execute("SELECT id, status FROM challenges WHERE id=?", (payload.challenge_id,)).fetchone()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        if challenge["status"] != "published":
            raise HTTPException(status_code=400, detail="Only published challenges accept proposals")
        cursor = conn.execute(
            """
            INSERT INTO proposals (
                challenge_id, team_id, team_name, solution_idea, plan, deadline, prototype_url, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                payload.challenge_id, payload.team_id, payload.team_name, payload.solution_idea,
                payload.plan, payload.deadline, payload.prototype_url,
            ),
        )
        row = conn.execute("SELECT * FROM proposals WHERE id=?", (cursor.lastrowid,)).fetchone()
    return {"proposal": _proposal_dict(row)}


@router.get("/challenges/{challenge_id}/proposals")
def list_proposals(challenge_id: int):
    with db_session() as conn:
        challenge = conn.execute("SELECT id FROM challenges WHERE id=?", (challenge_id,)).fetchone()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        rows = conn.execute(
            "SELECT * FROM proposals WHERE challenge_id=? ORDER BY created_at DESC", (challenge_id,)
        ).fetchall()
    return {"items": [_proposal_dict(row) for row in rows]}


@router.post("/proposals/{proposal_id}/decision")
def decide_proposal(proposal_id: int, payload: ProposalDecision):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Proposal not found")
        conn.execute("UPDATE proposals SET status=? WHERE id=?", (payload.decision, proposal_id))
        updated = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    return {"proposal": _proposal_dict(updated)}
