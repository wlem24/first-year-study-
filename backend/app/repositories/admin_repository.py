"""Repository for Admin user database operations."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Admin


class AdminRepository:
    """Encapsulates database access for Admin entities."""

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Admin]:
        """Fetch admin record by normalized email."""
        clean_email = email.strip().lower()
        result = await db.execute(select(Admin).where(Admin.email == clean_email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, email: str, hashed_password: str) -> Admin:
        """Create and persist a new admin user."""
        admin = Admin(email=email.strip().lower(), hashed_password=hashed_password)
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        return admin

    @staticmethod
    async def update_credentials(
        db: AsyncSession,
        admin: Admin,
        email: Optional[str] = None,
        hashed_password: Optional[str] = None,
    ) -> Admin:
        """Update email and/or password hash for an admin."""
        if email:
            admin.email = email.strip().lower()
        if hashed_password:
            admin.hashed_password = hashed_password
        await db.commit()
        await db.refresh(admin)
        return admin
