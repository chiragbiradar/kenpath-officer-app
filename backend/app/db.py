import re

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_url = re.sub(r"[?&]sslmode=\w+", "", settings.database_url).rstrip("?")
_ssl = "asyncpg" in settings.database_url and "sslmode=require" in settings.database_url
engine = create_async_engine(_url, echo=False, connect_args={"ssl": True} if _ssl else {})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
