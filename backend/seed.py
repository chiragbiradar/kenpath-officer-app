"""
Idempotent seeder: 2 officers + 20 passport applications.
Run: python seed.py  (from backend/ directory with .env present)
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select, text
from app.auth import hash_password
from app.db import AsyncSessionLocal, engine, Base
from app.models import Application, AuditEvent, Officer

PSK_DISTRICT = "Bangalore Urban"

OFFICERS = [
    {
        "email": "officer1@psk-bangalore.gov.in",
        "name": "Ramesh Kumar",
        "name_kn": "ರಮೇಶ್ ಕುಮಾರ್",
        "password": "Officer@123",
        "psk_district": PSK_DISTRICT,
    },
    {
        "email": "officer2@psk-bangalore.gov.in",
        "name": "Sunita Devi",
        "name_kn": "ಸುನಿತಾ ದೇವಿ",
        "password": "Officer@456",
        "psk_district": PSK_DISTRICT,
    },
]

now = datetime.now(timezone.utc)


def make_app(
    seq: int,
    name: str,
    name_kn: str,
    gender: str,
    dob: str,
    aadhaar_last4: str,
    application_type: str,
    documents: list[dict],
    days_ago: int = 1,
    overdue: bool = False,
    due_soon: bool = False,
) -> dict:
    received = now - timedelta(days=days_ago)
    if overdue:
        deadline = now - timedelta(days=1)
    elif due_soon:
        deadline = now + timedelta(days=1)
    else:
        deadline = received + timedelta(days=3)

    return {
        "app_no": f"PSP-2026-{seq:04d}",
        "applicant_name": name,
        "applicant_name_kn": name_kn,
        "gender": gender,
        "dob": dob,
        "phone_masked": f"XXXXXX{7000 + seq}",
        "aadhaar_masked": f"XXXX-XXXX-{aadhaar_last4}",
        "application_type": application_type,
        "documents": documents,
        "status": "pending",
        "received_at": received,
        "appointment_date": received.date().isoformat(),
        "deadline_at": deadline,
    }


def aadhaar_doc(name: str, dob: str, district: str = PSK_DISTRICT) -> dict:
    return {"type": "aadhaar", "present": True, "fields": {"name": name, "dob": dob, "address_district": district, "address_state": "Karnataka"}}


def dob_doc(name: str, dob: str) -> dict:
    return {"type": "dob_proof", "present": True, "fields": {"name": name, "dob": dob}}


def appt_doc(seq: int) -> dict:
    return {"type": "appointment_letter", "present": True, "fields": {"appointment_id": f"APPT{seq:04d}", "appointment_date": now.date().isoformat()}}


def old_passport_doc(name: str, dob: str) -> dict:
    return {"type": "old_passport", "present": True, "fields": {"name": name, "dob": dob, "expiry_date": "2020-01-01"}}


def missing_doc(doc_type: str) -> dict:
    return {"type": doc_type, "present": False, "fields": {}}


APPLICATIONS = [
    # ── 6 clean (all pass → accept) ──────────────────────────────────────────
    make_app(1, "Anitha Rao", "ಅನಿತಾ ರಾವ್", "F", "1990-05-15", "1001", "fresh",
             [aadhaar_doc("Anitha Rao", "1990-05-15"), dob_doc("Anitha Rao", "1990-05-15"), appt_doc(1)]),

    make_app(2, "Vijay Kumar", "ವಿಜಯ್ ಕುಮಾರ್", "M", "1985-11-20", "1002", "fresh",
             [aadhaar_doc("Vijay Kumar", "1985-11-20"), dob_doc("Vijay Kumar", "1985-11-20"), appt_doc(2)]),

    make_app(3, "Meena Patil", "ಮೀನಾ ಪಾಟೀಲ್", "F", "1995-03-08", "1003", "fresh",
             [aadhaar_doc("Meena Patil", "1995-03-08"), dob_doc("Meena Patil", "1995-03-08"), appt_doc(3)]),

    make_app(4, "Suresh Gowda", "ಸುರೇಶ್ ಗೌಡ", "M", "1978-07-22", "1004", "renewal",
             [aadhaar_doc("Suresh Gowda", "1978-07-22"), dob_doc("Suresh Gowda", "1978-07-22"),
              appt_doc(4), old_passport_doc("Suresh Gowda", "1978-07-22")]),

    make_app(5, "Kavitha Nair", "ಕಾವ್ಯ ನಾಯರ್", "F", "2000-01-30", "1005", "fresh",
             [aadhaar_doc("Kavitha Nair", "2000-01-30"), dob_doc("Kavitha Nair", "2000-01-30"), appt_doc(5)]),

    make_app(6, "Ravi Shankar", "ರವಿ ಶಂಕರ್", "M", "1992-09-14", "1006", "fresh",
             [aadhaar_doc("Ravi Shankar", "1992-09-14"), dob_doc("Ravi Shankar", "1992-09-14"), appt_doc(6)]),

    # ── 4 missing documents (→ return) ───────────────────────────────────────
    make_app(7, "Priya Reddy", "ಪ್ರಿಯಾ ರೆಡ್ಡಿ", "F", "1998-06-18", "2001", "fresh",
             [aadhaar_doc("Priya Reddy", "1998-06-18"), missing_doc("dob_proof"), appt_doc(7)]),

    make_app(8, "Gopal Krishna", "ಗೋಪಾಲ್ ಕೃಷ್ಣ", "M", "1975-12-03", "2002", "fresh",
             [aadhaar_doc("Gopal Krishna", "1975-12-03"), dob_doc("Gopal Krishna", "1975-12-03"), missing_doc("appointment_letter")]),

    make_app(9, "Lakshmi Devi", "ಲಕ್ಷ್ಮಿ ದೇವಿ", "F", "1988-04-25", "2003", "renewal",
             [aadhaar_doc("Lakshmi Devi", "1988-04-25"), dob_doc("Lakshmi Devi", "1988-04-25"),
              appt_doc(9), missing_doc("old_passport")]),

    make_app(10, "Mohan Das", "ಮೋಹನ್ ದಾಸ್", "M", "1970-08-11", "2004", "fresh",
             [missing_doc("aadhaar"), dob_doc("Mohan Das", "1970-08-11"), appt_doc(10)]),

    # ── 3 name mismatches (→ return) — #11 mirrors personal story ─────────────
    # App 11: Aadhaar = "Chirag Birader", 10th = "Chirag S Birader" (personal story)
    make_app(11, "Chirag Birader", "ಚಿರಾಗ್ ಬಿರಾದರ್", "M", "1998-03-15", "3001", "fresh",
             [aadhaar_doc("Chirag Birader", "1998-03-15"), dob_doc("Chirag S Birader", "1998-03-15"), appt_doc(11)]),

    make_app(12, "Shalini Verma", "ಶಾಲಿನಿ ವರ್ಮಾ", "F", "1993-10-07", "3002", "fresh",
             [aadhaar_doc("Shalini Verma", "1993-10-07"), dob_doc("Shalini K Verma", "1993-10-07"), appt_doc(12)]),

    make_app(13, "Abdul Rahman", "ಅಬ್ದುಲ್ ರಹಮಾನ್", "M", "1982-02-19", "3003", "fresh",
             [aadhaar_doc("Abdul Rahman", "1982-02-19"), dob_doc("Abdulrahman", "1982-02-19"), appt_doc(13)]),

    # ── 2 DOB mismatches (→ reject) ───────────────────────────────────────────
    make_app(14, "Rekha Singh", "ರೇಖಾ ಸಿಂಗ್", "F", "1986-07-30", "4001", "fresh",
             [aadhaar_doc("Rekha Singh", "1986-07-30"), dob_doc("Rekha Singh", "1987-07-30"), appt_doc(14)]),

    make_app(15, "Prakash Hegde", "ಪ್ರಕಾಶ್ ಹೆಗ್ಡೆ", "M", "1979-11-05", "4002", "fresh",
             [aadhaar_doc("Prakash Hegde", "1979-11-05"), dob_doc("Prakash Hegde", "1980-11-05"), appt_doc(15)]),

    # ── 2 duplicates (→ reject) — these will be seeded as pending but we mark one aadhaar ─
    # App 16 will be accepted first by code; app 17 uses same aadhaar → duplicate
    make_app(16, "Nirmala Shetty", "ನಿರ್ಮಲಾ ಶೆಟ್ಟಿ", "F", "1991-08-22", "5001", "fresh",
             [aadhaar_doc("Nirmala Shetty", "1991-08-22"), dob_doc("Nirmala Shetty", "1991-08-22"), appt_doc(16)]),

    make_app(17, "Nirmala Shetty", "ನಿರ್ಮಲಾ ಶೆಟ್ಟಿ", "F", "1991-08-22", "5001", "fresh",
             [aadhaar_doc("Nirmala Shetty", "1991-08-22"), dob_doc("Nirmala Shetty", "1991-08-22"), appt_doc(17)]),

    # ── 2 overdue ─────────────────────────────────────────────────────────────
    make_app(18, "Dinesh Kumar", "ದಿನೇಶ್ ಕುಮಾರ್", "M", "1987-05-10", "6001", "fresh",
             [aadhaar_doc("Dinesh Kumar", "1987-05-10"), dob_doc("Dinesh Kumar", "1987-05-10"), appt_doc(18)],
             days_ago=5, overdue=True),

    make_app(19, "Savitha Bhat", "ಸವಿತಾ ಭಟ್", "F", "1994-12-01", "6002", "fresh",
             [aadhaar_doc("Savitha Bhat", "1994-12-01"), dob_doc("Savitha Bhat", "1994-12-01"), appt_doc(19)],
             days_ago=4, overdue=True),

    # ── 1 due soon + address mismatch ─────────────────────────────────────────
    make_app(20, "Harish Naik", "ಹರೀಶ್ ನಾಯಕ್", "M", "1996-06-28", "7001", "fresh",
             [aadhaar_doc("Harish Naik", "1996-06-28", district="Mysuru"),
              dob_doc("Harish Naik", "1996-06-28"), appt_doc(20)],
             due_soon=True),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Officers
        for o in OFFICERS:
            existing = await db.execute(select(Officer).where(Officer.email == o["email"]))
            if not existing.scalar_one_or_none():
                officer = Officer(
                    name=o["name"], name_kn=o["name_kn"],
                    email=o["email"], password_hash=hash_password(o["password"]),
                    psk_district=o["psk_district"],
                )
                db.add(officer)
        await db.commit()

        # Applications
        for a in APPLICATIONS:
            existing = await db.execute(select(Application).where(Application.app_no == a["app_no"]))
            if not existing.scalar_one_or_none():
                app = Application(**a)
                db.add(app)
                await db.flush()
                audit = AuditEvent(
                    application_id=app.id, officer_id=None,
                    event="received", detail={"app_no": app.app_no},
                )
                db.add(audit)

        # App 16 (Nirmala Shetty first copy) → accepted so app 17 is a duplicate
        await db.commit()
        result = await db.execute(select(Application).where(Application.app_no == "PSP-2026-0016"))
        app16 = result.scalar_one_or_none()
        if app16 and app16.status == "pending":
            app16.status = "accepted"
            await db.commit()

        await db.commit()
        print("Seeded: 2 officers, 20 applications")


if __name__ == "__main__":
    asyncio.run(seed())
