import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_session
from app.core.seed_data import seed_initial_data

# Base de données de test SQLite asynchrone isolée
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine):
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        # Peupler les repères locaux et alertes pour les tests
        await seed_initial_data(session)
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest_asyncio.fixture
async def client(test_session):
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
