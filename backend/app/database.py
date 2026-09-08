"""Database engine, session, and initialization."""

import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash

logger = logging.getLogger("database")

IS_VERCEL = bool(os.environ.get("VERCEL"))

# ── Engine Configuration ──────────────────────────────────────────

connect_args = {}
engine_kwargs = {"echo": False}

if settings.ASYNC_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    })

engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables and seed the admin user from env vars."""
    from app.models import Base, Admin  # imported here to avoid circular imports

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Admin).where(Admin.email == settings.ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()
        if admin is None:
            new_admin = Admin(
                email=settings.ADMIN_EMAIL,
                hashed_password=settings.ADMIN_PASSWORD_HASH,
            )
            session.add(new_admin)
            await session.commit()
            logger.info("Admin user '%s' created.", settings.ADMIN_EMAIL)
        else:
            logger.info("Admin user '%s' already exists.", settings.ADMIN_EMAIL)
