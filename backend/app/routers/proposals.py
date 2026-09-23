from fastapi import APIRouter, HTTPException, Depends
from ..database import db_session
from .auth import current_user, business_user, performer_user, owned_challenge
from ..schemas import ProposalCreate, ProposalDecision, MilestoneConfirm

router = APIRouter(prefix="/api", tags=["proposals"])


def _proposal_dict(row):
    if not row:
        return None
    item = dict(row)
    with db_session() as conn:
        item['milestones'] = [dict(m) for m in conn.execute('SELECT * FROM milestones WHERE proposal_id=? ORDER BY id', (item['id'],))]
        history = conn.execute("""
            WITH completed AS (
                SELECT p.id, p.challenge_id, SUM(m.points) AS score
                FROM proposals p JOIN milestones m ON m.proposal_id=p.id
                WHERE p.owner_id=? AND p.team_id IS ? AND p.challenge_id<>?
                  AND p.status='accepted'
                GROUP BY p.id, p.challenge_id
                HAVING COUNT(DISTINCT m.stage)=3
            ), latest AS (
                SELECT challenge_id, MAX(id) AS id FROM completed GROUP BY challenge_id
            )
            SELECT COUNT(*) AS completed_count, ROUND(AVG(c.score),1) AS average_score
            FROM completed c JOIN latest l ON c.id=l.id
        """, (item.get('owner_id'),item.get('team_id'),item['challenge_id'])).fetchone()
    item['performer_rating'] = {'average_score':history['average_score'],'completed_count':history['completed_count'],'max_score':100}
    item['progress_points'] = sum(m['points'] for m in item['milestones'])
    return item


@router.get("/teams")
def list_teams(user=Depends(current_user)):
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
def create_proposal(payload: ProposalCreate, user=Depends(performer_user)):
    with db_session() as conn:
        challenge = conn.execute("SELECT id, status FROM challenges WHERE id=?", (payload.challenge_id,)).fetchone()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        if challenge["status"] != "published":
            raise HTTPException(status_code=400, detail="Only published challenges accept proposals")
        payload.team_id = None
        payload.team_name = user['display_name']
        cursor = conn.execute(
            """
            INSERT INTO proposals (
                challenge_id, team_id, team_name, solution_idea, plan, deadline, prototype_url, status, owner_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                payload.challenge_id, payload.team_id, payload.team_name, payload.solution_idea,
                payload.plan, payload.deadline, payload.prototype_url, user["id"],
            ),
        )
        row = conn.execute("SELECT * FROM proposals WHERE id=?", (cursor.lastrowid,)).fetchone()
    return {"proposal": _proposal_dict(row)}


@router.get("/challenges/{challenge_id}/proposals")
def list_proposals(challenge_id: int, user=Depends(business_user)):
    with db_session() as conn:
        challenge = owned_challenge(conn,challenge_id,user)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        rows = conn.execute(
            "SELECT * FROM proposals WHERE challenge_id=? ORDER BY created_at DESC", (challenge_id,)
        ).fetchall()
    return {"items": [_proposal_dict(row) for row in rows]}


@router.post("/proposals/{proposal_id}/decision")
def decide_proposal(proposal_id: int, payload: ProposalDecision, user=Depends(business_user)):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Proposal not found")
        owned_challenge(conn,row["challenge_id"],user)
        conn.execute("UPDATE proposals SET status=? WHERE id=?", (payload.decision, proposal_id))
        updated = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    return {"proposal": _proposal_dict(updated)}


@router.post('/proposals/{proposal_id}/milestones')
def confirm_milestone(proposal_id: int, payload: MilestoneConfirm, user=Depends(business_user)):
    weights = {'discovery': 20, 'prototype': 30, 'validation': 50}
    with db_session() as conn:
        row = conn.execute('SELECT * FROM proposals WHERE id=?', (proposal_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='Предложение не найдено')
        owned_challenge(conn,row['challenge_id'],user)
        if row['status'] != 'accepted':
            raise HTTPException(status_code=409, detail='Сначала выберите команду вручную')
        if conn.execute('SELECT id FROM milestones WHERE proposal_id=? AND stage=?', (proposal_id, payload.stage)).fetchone():
            raise HTTPException(status_code=409, detail='Баллы за этот этап уже начислены')
        inserted = conn.execute('INSERT INTO milestones (proposal_id, stage, evidence, points) VALUES (?, ?, ?, ?) ON CONFLICT(proposal_id, stage) DO NOTHING',
                     (proposal_id, payload.stage, payload.evidence, payload.points))
        if inserted.rowcount == 0:
            raise HTTPException(status_code=409, detail='Баллы за этот этап уже начислены')
    return {'proposal': _proposal_dict(row)}


@router.get('/my-proposals')
def own_proposals(user=Depends(performer_user)):
    with db_session() as conn:
        rows=conn.execute('SELECT p.*,c.title AS challenge_title FROM proposals p JOIN challenges c ON c.id=p.challenge_id WHERE p.owner_id=? ORDER BY p.id DESC',(user['id'],)).fetchall()
    return {'items':[_proposal_dict(row) for row in rows]}
