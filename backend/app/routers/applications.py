from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import get_or_create_analysis
from app.auth import get_current_officer
from app.db import get_db
from app.models import Application, AuditEvent, Officer
from app.priority import deadline_status, priority_score
from app.rules import run_all_rules
from app.schemas import (
    ApplicationDetail,
    ApplicationFlags,
    ApplicationListResponse,
    ApplicationRow,
    AuditEventOut,
    Document,
    Pagination,
    RuleCheck,
    StatsResponse,
)

router = APIRouter(prefix="/api", tags=["applications"])


async def _accepted_aadhaar_set(db: AsyncSession) -> set[str]:
    result = await db.execute(
        select(Application.aadhaar_masked).where(Application.status == "accepted")
    )
    return {row[0] for row in result.fetchall()}


async def _rule_checks_for(app: Application, psk_district: str, accepted: set[str]) -> list[RuleCheck]:
    results = run_all_rules(
        documents=app.documents,
        application_type=app.application_type,
        aadhaar_masked=app.aadhaar_masked,
        psk_district=psk_district,
        existing_accepted_aadhaar=accepted,
    )
    return [RuleCheck(code=r.code, status=r.status, message_kn=r.message_kn,
                      message_en=r.message_en, evidence=r.evidence) for r in results]


@router.get("/stats", response_model=StatsResponse)
async def stats(
    officer: Officer = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    all_pending = await db.execute(select(Application).where(Application.status == "pending"))
    pending_apps = all_pending.scalars().all()

    due_soon = sum(1 for a in pending_apps if deadline_status(a.deadline_at) == "due_soon")
    overdue = sum(1 for a in pending_apps if deadline_status(a.deadline_at) == "overdue")

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    decided_result = await db.execute(
        select(func.count(Application.id)).where(
            Application.status.in_(["accepted", "returned", "rejected"]),
            Application.created_at >= today_start,
        )
    )
    decided_today = decided_result.scalar() or 0

    return StatsResponse(
        pending=len(pending_apps),
        due_soon=due_soon,
        overdue=overdue,
        decided_today=decided_today,
    )


@router.get("/applications", response_model=ApplicationListResponse)
async def list_applications(
    status: str = Query("pending"),
    flag: str = Query(""),
    q: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    officer: Officer = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db),
):
    query = select(Application)
    if status:
        query = query.where(Application.status == status)
    if q:
        query = query.where(
            Application.applicant_name.ilike(f"%{q}%") | Application.app_no.ilike(f"%{q}%")
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    apps = result.scalars().all()

    accepted = await _accepted_aadhaar_set(db)
    rows = []
    for app in apps:
        rule_results = run_all_rules(
            app.documents, app.application_type, app.aadhaar_masked,
            officer.psk_district, accepted,
        )
        score = priority_score(app.deadline_at, rule_results)
        ds = deadline_status(app.deadline_at)
        recv = app.received_at.replace(tzinfo=timezone.utc) if app.received_at.tzinfo is None else app.received_at
        days_pending = (datetime.now(timezone.utc) - recv).days
        missing_docs = sum(1 for r in rule_results if r.code == "R3" and r.status == "fail")
        fails = sum(1 for r in rule_results if r.status == "fail")
        reviews = sum(1 for r in rule_results if r.status == "review")

        rows.append(ApplicationRow(
            id=app.id, app_no=app.app_no,
            applicant_name=app.applicant_name, applicant_name_kn=app.applicant_name_kn,
            application_type=app.application_type,
            days_pending=days_pending, deadline_status=ds, priority=score,
            flags=ApplicationFlags(missing_docs=missing_docs, fails=fails, reviews=reviews),
            status=app.status,
        ))

    rows.sort(key=lambda r: r.priority, reverse=True)
    return ApplicationListResponse(data=rows, pagination=Pagination(page=page, limit=limit, total=total))


@router.get("/applications/{app_id}", response_model=ApplicationDetail)
async def get_application(
    app_id: str,
    officer: Officer = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    accepted = await _accepted_aadhaar_set(db)
    rule_checks = await _rule_checks_for(app, officer.psk_district, accepted)

    audit_result = await db.execute(
        select(AuditEvent).where(AuditEvent.application_id == app_id).order_by(AuditEvent.created_at)
    )
    audit_events = [
        AuditEventOut(
            event=e.event, detail=e.detail,
            created_at=e.created_at.isoformat(), officer_id=e.officer_id
        )
        for e in audit_result.scalars().all()
    ]

    recv = app.received_at.replace(tzinfo=timezone.utc) if app.received_at.tzinfo is None else app.received_at
    days_pending = (datetime.now(timezone.utc) - recv).days
    ds = deadline_status(app.deadline_at)
    docs = [Document(**d) for d in app.documents]

    return ApplicationDetail(
        id=app.id, app_no=app.app_no,
        applicant_name=app.applicant_name, applicant_name_kn=app.applicant_name_kn,
        gender=app.gender, dob=app.dob,
        phone_masked=app.phone_masked, aadhaar_masked=app.aadhaar_masked,
        application_type=app.application_type,
        documents=docs, status=app.status,
        received_at=app.received_at.isoformat(),
        appointment_date=app.appointment_date,
        deadline_at=app.deadline_at.isoformat(),
        days_pending=days_pending, deadline_status=ds,
        rule_checks=rule_checks,
        ai_analysis=None,
        audit=audit_events,
    )


@router.post("/applications/{app_id}/analyse")
async def analyse_application(
    app_id: str,
    force: bool = Query(False),
    officer: Officer = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    accepted = await _accepted_aadhaar_set(db)
    rule_results = run_all_rules(
        app.documents, app.application_type, app.aadhaar_masked,
        officer.psk_district, accepted,
    )

    analysis = await get_or_create_analysis(db, app, rule_results, force=force)

    await db.execute(
        AuditEvent.__table__.insert().values(
            application_id=app_id, officer_id=officer.id,
            event="ai_analysed", detail={"cached": analysis.cached, "model": analysis.model},
        )
    )
    await db.commit()
    return analysis
