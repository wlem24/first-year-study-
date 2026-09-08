"""Service implementing authentication and account management business logic."""

import logging
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.models import Admin
from app.repositories.admin_repository import AdminRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas import AdminUpdate

logger = logging.getLogger("auth_service")


class AuthService:
    """Business logic for authentication and admin profile management."""

    @staticmethod
    async def authenticate_admin(
        db: AsyncSession,
        email: str,
        password: str,
        client_ip: str = "unknown",
    ) -> Tuple[Admin, str, str]:
        """Validate credentials, generate tokens, and log audit event."""
        clean_email = email.strip().lower()
        admin = await AdminRepository.get_by_email(db, clean_email)

        if admin is None or not verify_password(password, admin.hashed_password):
            logger.warning("Failed login attempt for email='%s' from IP=%s", clean_email, client_ip)
            await AuditRepository.log(db, "LOGIN_FAILED", f"email={clean_email}", ip_address=client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        access_token = create_access_token(data={"sub": admin.email})
        refresh_token = create_refresh_token(data={"sub": admin.email})

        logger.info("Successful login for email='%s'", admin.email)
        await AuditRepository.log(
            db, "LOGIN_SUCCESS", f"email={admin.email}", ip_address=client_ip, admin_email=admin.email
        )
        return admin, access_token, refresh_token

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        token: str,
    ) -> Tuple[Admin, str, str]:
        """Validate refresh token and issue new token pair."""
        payload = verify_token(token, expected_type="refresh")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        admin = await AdminRepository.get_by_email(db, email)
        if admin is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        new_access = create_access_token(data={"sub": admin.email})
        new_refresh = create_refresh_token(data={"sub": admin.email})
        return admin, new_access, new_refresh

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        admin: Admin,
        body: AdminUpdate,
    ) -> Admin:
        """Update admin email and/or password with current-password verification."""
        new_hashed_password: Optional[str] = None
        new_email: Optional[str] = None

        if body.new_password:
            if not body.current_password or not verify_password(body.current_password, admin.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="كلمة المرور الحالية غير صحيحة",
                )
            new_hashed_password = get_password_hash(body.new_password)

        if body.email:
            clean_email = body.email.strip().lower()
            if clean_email != admin.email:
                existing = await AdminRepository.get_by_email(db, clean_email)
                if existing and existing.id != admin.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="البريد الإلكتروني مستخدم بالفعل",
                    )
                new_email = clean_email

        updated_admin = await AdminRepository.update_credentials(
            db, admin, email=new_email, hashed_password=new_hashed_password
        )
        await AuditRepository.log(
            db, "PROFILE_UPDATED", f"admin_id={admin.id}", admin_email=updated_admin.email
        )
        return updated_admin
