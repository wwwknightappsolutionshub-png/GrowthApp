from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Engine: use NullPool in tests to avoid connection leaks
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    pool_size=10 if not settings.is_sqlite else 1,
    max_overflow=20 if not settings.is_sqlite else 0,
    poolclass=None if settings.ENVIRONMENT != "testing" else NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager version for use outside FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session


async def set_rls_context(session: AsyncSession, tenant_id: UUID | str | None) -> None:
    """
    Set the PostgreSQL session variable for Row-Level Security.
    Must be called at the start of every authenticated request.
    Skipped for SQLite (no RLS support).
    """
    if settings.is_sqlite:
        return
    if tenant_id is not None:
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tid, TRUE)"),
            {"tid": str(tenant_id)},
        )
    else:
        # For unauthenticated/superadmin contexts: clear RLS
        await session.execute(
            text("SELECT set_config('app.current_tenant', '', TRUE)")
        )
