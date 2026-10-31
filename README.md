# PSK Officer Tool — ಪಾಸ್‌ಪೋರ್ಟ್ ಅಧಿಕಾರಿ ಸಾಧನ

A Kannada-first tool for Passport Seva Kendra (PSK) officers in Bangalore to review, analyse, and decide on passport applications — with AI assistance that is always advisory, never in control.

## The problem

When I applied for a passport, my Aadhaar said "Chirag Birader" and my 10th marksheet said "Chirag S. Birader". Three trips to the PSK office, weeks of delay. If the officer had a tool that flagged this name mismatch on first submission and pre-filled a return notice, one interaction would have done the job.

This app is that tool.

## Live demo

🔗 **https://kenpath-officer-app.onrender.com**

Test credentials:
| Email | Password |
|---|---|
| `officer1@psk-bangalore.gov.in` | `Officer@123` |
| `officer2@psk-bangalore.gov.in` | `Officer@456` |

> Note: Render free tier sleeps after 15 min inactivity. First request may take ~30s.

## What it does

- **Queue view**: 20 seeded applications sorted by priority (overdue first, then rule failures)
- **Rule checks**: 5 deterministic checks run before the AI — name match, DOB match, docs complete, address valid, duplicate
- **AI assistance**: Gemini Flash analyses each application, returns Kannada summary + suggested decision + draft remark
- **Decision**: officer clicks Accept / Return / Reject; remark required for Return/Reject; AI never changes status
- **Audit trail**: every event logged per application

## Key design decision: rules in code, not in the LLM

Deterministic rule checks run first. If any rule fails, the AI cannot suggest "accept" — code overrides the model. This is intentional: an LLM can hallucinate a reason to approve an ineligible application, and that is a legal liability. Deterministic rules are the last line of defense.

## Local setup

### Requirements
- Docker (for Postgres)
- Python 3.12+
- Node 20+
- Gemini API key (get free at [aistudio.google.com](https://aistudio.google.com))

### Run locally

```bash
# 1. Start Postgres
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Copy and fill .env
cp ../.env.example .env
# Set DATABASE_URL=postgresql+asyncpg://psk:psk@localhost:5432/psk_officer
# Set GEMINI_API_KEY=your-key

# Seed data
python seed.py

# Start server
uvicorn app.main:app --reload
```

```bash
# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Run tests

```bash
cd backend
pip install aiosqlite  # for in-memory test DB
pytest
```

## Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 |
| DB | PostgreSQL (local: Docker; prod: Neon free tier) |
| AI | Pydantic AI + Gemini Flash |
| Frontend | React 18 + Vite + TypeScript, react-i18next |
| Font | Noto Sans Kannada |
| Auth | bcrypt + JWT |
| Deploy | Render (backend + frontend) + Neon (Postgres) |

## What I'd add next

- **AI eval golden set**: 20 labelled applications with expected decisions; pytest-marked `llm`, run nightly
- **OCR / document upload**: real Aadhaar and marksheet PDF parsing via Tesseract or Google Vision
- **Alembic migrations**: currently uses `create_all` on startup
- **Police verification integration**: next step after PSK acceptance
- **Seva Sindhu / Aadhaar API**: real identity verification
- **NestJS backend**: happy to rewrite in NestJS/TypeScript if preferred

## Note on rule constants

All thresholds are in `backend/app/rules.py`. Constants marked `SAMPLE_RULE` are estimates;
update the single constant value when the official figure is confirmed. See `ASSUMPTIONS.md`.
