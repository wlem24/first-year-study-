"""Auth router — login, refresh, logout, me."""

import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.database import get_db
from app.auth import get_current_admin
from app.models import Admin, AuditLog
from app.schemas import LoginRequest, TokenResponse, AdminOut, MessageResponse, AdminUpdate

logger = logging.getLogger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)

IS_VERCEL = bool(os.environ.get("VERCEL"))

# Cookie settings — Strict SameSite, Secure in production
COOKIE_SAMESITE = "strict"
COOKIE_SECURE = IS_VERCEL  # True on HTTPS (Vercel), False locally


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    """Set both access and refresh tokens as httpOnly secure cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",  # Only sent to auth endpoints
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear both access and refresh token cookies."""
    response.delete_cookie("access_token", path="/", secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)
    response.delete_cookie("refresh_token", path="/api/v1/auth", secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)


async def _log_audit(
    db: AsyncSession, event_type: str, detail: str,
    ip_address: str | None = None, admin_email: str | None = None,
) -> None:
    """Write an audit log entry."""
    entry = AuditLog(
        event_type=event_type,
        detail=detail,
        ip_address=ip_address,
        admin_email=admin_email,
    )
    db.add(entry)
    await db.commit()


# ── POST /auth/login ──────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate admin and set JWT cookies. Rate-limited to 5 attempts / 15 min."""
    client_ip = request.client.host if request.client else "unknown"
    
    clean_email = body.email.strip().lower()

    result = await db.execute(select(Admin).where(Admin.email == clean_email))
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(body.password, admin.hashed_password):
        logger.warning("Failed login attempt for email='%s' from IP=%s", clean_email, client_ip)
        await _log_audit(db, "LOGIN_FAILED", f"email={clean_email}", ip_address=client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": admin.email})
    refresh_token = create_refresh_token(data={"sub": admin.email})

    _set_auth_cookies(response, access_token, refresh_token)

    logger.info("Successful login for email='%s'", admin.email)
    await _log_audit(db, "LOGIN_SUCCESS", f"email={admin.email}", ip_address=client_ip, admin_email=admin.email)

    return TokenResponse(message="Login successful")


# ── POST /auth/refresh ────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Issue new tokens using the refresh token cookie."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = verify_token(token, expected_type="refresh")
    email = payload.get("sub")

    result = await db.execute(select(Admin).where(Admin.email == email))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_access_token(data={"sub": admin.email})
    new_refresh = create_refresh_token(data={"sub": admin.email})

    _set_auth_cookies(response, new_access, new_refresh)

    return TokenResponse(message="Tokens refreshed")


# ── POST /auth/logout ─────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """Clear all auth cookies."""
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")


# ── GET /auth/me ───────────────────────────────────────────────────

@router.get("/me", response_model=AdminOut)
async def get_me(admin: Admin = Depends(get_current_admin)):
    """Return the current authenticated admin's profile."""
    return admin

@router.put("/me", response_model=AdminOut)
async def update_me(
    body: AdminUpdate,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update admin email or password."""
    if body.new_password:
        if not body.current_password or not verify_password(body.current_password, admin.hashed_password):
            raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
        admin.hashed_password = get_password_hash(body.new_password)
        
    if body.email:
        clean_email = body.email.strip().lower()
        if clean_email != admin.email:
            result = await db.execute(select(Admin).where(Admin.email == clean_email))
            if result.scalar_one_or_none():
                 raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
            admin.email = clean_email

    await db.commit()
    await db.refresh(admin)
    return admin
