from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_token, get_current_officer, verify_password
from app.db import get_db
from app.models import Officer
from app.schemas import LoginRequest, LoginResponse, OfficerOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Officer).where(Officer.email == body.email))
    officer = result.scalar_one_or_none()
    if not officer or not verify_password(body.password, officer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(officer.id)
    return LoginResponse(token=token, officer=OfficerOut(**officer.__dict__))


@router.get("/me", response_model=OfficerOut)
async def me(officer: Officer = Depends(get_current_officer)):
    return OfficerOut(**officer.__dict__)
