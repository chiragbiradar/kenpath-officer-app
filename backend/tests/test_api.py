import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.models import Application, AuditEvent


pytestmark = pytest.mark.asyncio


async def _login(client):
    r = await client.post("/api/auth/login", json={"email": "test@psk.gov.in", "password": "Test@123"})
    assert r.status_code == 200
    return r.json()["token"]


async def _seed_app(db_session, app_no="TEST-0001"):
    from sqlalchemy import select
    existing = await db_session.execute(select(Application).where(Application.app_no == app_no))
    if existing.scalar_one_or_none():
        return

    now = datetime.now(timezone.utc)
    app = Application(
        app_no=app_no,
        applicant_name="Test User",
        applicant_name_kn="ಟೆಸ್ಟ್ ಬಳಕೆದಾರ",
        gender="M",
        dob="1990-01-01",
        phone_masked="XXXXXX9999",
        aadhaar_masked="XXXX-XXXX-9999",
        application_type="fresh",
        documents=[
            {"type": "aadhaar", "present": True, "fields": {"name": "Test User", "dob": "1990-01-01", "address_district": "Bangalore Urban"}},
            {"type": "dob_proof", "present": True, "fields": {"name": "Test User", "dob": "1990-01-01"}},
            {"type": "appointment_letter", "present": True, "fields": {}},
        ],
        status="pending",
        received_at=now - timedelta(days=1),
        appointment_date=(now - timedelta(days=1)).date().isoformat(),
        deadline_at=now + timedelta(days=2),
    )
    db_session.add(app)
    await db_session.flush()  # ensures app.id is set before referencing it
    db_session.add(AuditEvent(application_id=app.id, event="received", detail={}))
    await db_session.commit()
    return app


async def test_login_success(client):
    r = await client.post("/api/auth/login", json={"email": "test@psk.gov.in", "password": "Test@123"})
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["officer"]["email"] == "test@psk.gov.in"


async def test_login_bad_password(client):
    r = await client.post("/api/auth/login", json={"email": "test@psk.gov.in", "password": "wrong"})
    assert r.status_code == 401


async def test_me_requires_auth(client):
    r = await client.get("/api/auth/me")
    assert r.status_code in (401, 403)


async def test_me_returns_officer(client):
    token = await _login(client)
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "test@psk.gov.in"


async def test_list_applications(client, db_session):
    await _seed_app(db_session)
    token = await _login(client)
    r = await client.get("/api/applications", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert "pagination" in data


async def test_get_application_detail(client, db_session):
    await _seed_app(db_session)
    token = await _login(client)
    list_r = await client.get("/api/applications", headers={"Authorization": f"Bearer {token}"})
    apps = list_r.json()["data"]
    assert len(apps) > 0
    app_id = apps[0]["id"]
    r = await client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    detail = r.json()
    assert "rule_checks" in detail
    assert len(detail["rule_checks"]) == 5


async def test_decision_accept(client, db_session):
    await _seed_app(db_session, "TEST-ACCEPT")
    token = await _login(client)
    list_r = await client.get("/api/applications?q=TEST-ACCEPT", headers={"Authorization": f"Bearer {token}"})
    app_id = list_r.json()["data"][0]["id"]
    r = await client.post(
        f"/api/applications/{app_id}/decision",
        json={"action": "accept"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201


async def test_decision_reject_requires_remark(client, db_session):
    await _seed_app(db_session, "TEST-REJECT")
    token = await _login(client)
    list_r = await client.get("/api/applications?q=TEST-REJECT", headers={"Authorization": f"Bearer {token}"})
    app_id = list_r.json()["data"][0]["id"]
    r = await client.post(
        f"/api/applications/{app_id}/decision",
        json={"action": "reject"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


async def test_decision_reject_with_remark(client, db_session):
    await _seed_app(db_session, "TEST-REJECT2")
    token = await _login(client)
    list_r = await client.get("/api/applications?q=TEST-REJECT2", headers={"Authorization": f"Bearer {token}"})
    app_id = list_r.json()["data"][0]["id"]
    r = await client.post(
        f"/api/applications/{app_id}/decision",
        json={"action": "reject", "remark": "Duplicate Aadhaar found"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201


async def test_double_decision_rejected(client, db_session):
    await _seed_app(db_session, "TEST-DOUBLE")
    token = await _login(client)
    list_r = await client.get("/api/applications?q=TEST-DOUBLE", headers={"Authorization": f"Bearer {token}"})
    app_id = list_r.json()["data"][0]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"/api/applications/{app_id}/decision", json={"action": "accept"}, headers=headers)
    r = await client.post(f"/api/applications/{app_id}/decision", json={"action": "accept"}, headers=headers)
    assert r.status_code == 409
