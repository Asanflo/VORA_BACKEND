from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import re

# Adapter l'URL pour asyncpg si Supabase fournit postgres:// ou postgresql://
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Options d'engine selon le type de base
engine_kwargs = {"echo": False, "future": True}
if "sqlite" in database_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Pour Supabase PostgreSQL (Pooler ou Direct)
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(database_url, **engine_kwargs)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Fournit une session asynchrone pour les dépendances FastAPI"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """Initialise les tables dans la base de données (Supabase ou SQLite)"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
