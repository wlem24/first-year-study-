"""Repository for audit logging operations."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog


class AuditRepository:
    """Encapsulates database access for audit log records."""

    @staticmethod
    async def log(
        db: AsyncSession,
        event_type: str,
        detail: str,
        ip_address: Optional[str] = None,
        admin_email: Optional[str] = None,
    ) -> AuditLog:
        """Create and commit an audit log entry."""
        entry = AuditLog(
            event_type=event_type,
            detail=detail,
            ip_address=ip_address,
            admin_email=admin_email,
        )
        db.add(entry)
        await db.commit()
        return entry
