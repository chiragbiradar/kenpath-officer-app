from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_officer
from app.db import get_db
from app.models import Application, AuditEvent, Decision, Officer
from app.schemas import DecisionRequest

router = APIRouter(prefix="/api", tags=["decisions"])


@router.post("/applications/{app_id}/decision", status_code=201)
async def make_decision(
    app_id: str,
    body: DecisionRequest,
    officer: Officer = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status != "pending":
        raise HTTPException(status_code=409, detail="Application is not pending")
    if body.action in ("return", "reject") and not body.remark:
        raise HTTPException(status_code=422, detail="Remark required for return/reject")

    app.status = body.action if body.action != "return" else "returned"

    # fetch latest AI suggestion if available
    from sqlalchemy import desc
    from app.models import AiAnalysis
    ai_result = await db.execute(
        select(AiAnalysis)
        .where(AiAnalysis.application_id == app_id)
        .order_by(desc(AiAnalysis.created_at))
        .limit(1)
    )
    latest_ai = ai_result.scalar_one_or_none()
    ai_suggestion = None
    agreed_with_ai = None
    if latest_ai:
        ai_suggestion = latest_ai.result.get("suggested_decision")
        agreed_with_ai = ai_suggestion == body.action

    decision = Decision(
        application_id=app_id,
        officer_id=officer.id,
        action=body.action,
        remark=body.remark,
        ai_suggestion=ai_suggestion,
        agreed_with_ai=agreed_with_ai,
    )
    db.add(decision)

    audit = AuditEvent(
        application_id=app_id,
        officer_id=officer.id,
        event="decided",
        detail={"action": body.action, "remark": body.remark, "agreed_with_ai": agreed_with_ai},
    )
    db.add(audit)

    await db.commit()
    return {"status": "ok", "action": body.action}
