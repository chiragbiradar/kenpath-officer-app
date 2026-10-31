import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_db
from app.main import app
from app.auth import hash_password
from app.models import Officer

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # seed one officer
    from sqlalchemy import select
    existing = await db_session.execute(select(Officer).where(Officer.email == "test@psk.gov.in"))
    if not existing.scalar_one_or_none():
        officer = Officer(
            name="Test Officer", name_kn="ಟೆಸ್ಟ್ ಅಧಿಕಾರಿ",
            email="test@psk.gov.in",
            password_hash=hash_password("Test@123"),
            psk_district="Bangalore Urban",
        )
        db_session.add(officer)
        await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
