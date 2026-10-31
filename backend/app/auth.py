from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import Officer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(officer_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": officer_id, "exp": expire}, settings.jwt_secret, algorithm="HS256")


async def get_current_officer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Officer:
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        officer_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(Officer).where(Officer.id == officer_id))
    officer = result.scalar_one_or_none()
    if not officer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Officer not found")
    return officer
