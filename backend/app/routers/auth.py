"""Auth router — login, refresh, logout, me using AuthService."""

import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.database import get_db
from app.auth import get_current_admin
from app.models import Admin
from app.schemas import LoginRequest, TokenResponse, AdminOut, MessageResponse, AdminUpdate
from app.services.auth_service import AuthService

logger = logging.getLogger("auth_router")

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

def _is_https(request: Request) -> bool:
    """Detect if request is HTTPS, accounting for reverse proxies (Render/Vercel)."""
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    is_https: bool = True,
) -> None:
    """Set both access and refresh tokens as httpOnly secure cookies."""
    secure_flag = is_https
    samesite_val = "none" if is_https else "lax"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_flag,
        samesite=samesite_val,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_flag,
        samesite=samesite_val,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def _clear_auth_cookies(response: Response, is_https: bool = True) -> None:
    """Clear both access and refresh token cookies."""
    secure_flag = is_https
    samesite_val = "none" if is_https else "lax"
    response.delete_cookie("access_token", path="/", secure=secure_flag, samesite=samesite_val)
    response.delete_cookie("refresh_token", path="/", secure=secure_flag, samesite=samesite_val)


# ── POST /auth/login ──────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/15minutes")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate admin, set JWT cookies, and return tokens in response body."""
    client_ip = request.client.host if request.client else "unknown"

    admin, access_token, refresh_token = await AuthService.authenticate_admin(
        db=db,
        email=body.email,
        password=body.password,
        client_ip=client_ip,
    )

    _set_auth_cookies(response, access_token, refresh_token, is_https=_is_https(request))

    return TokenResponse(
        message="Login successful",
        token_type="bearer",
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ── POST /auth/refresh ────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Issue new tokens using refresh token from cookie or header."""
    token = request.cookies.get("refresh_token")
    if not token:
        # Fallback to header if third-party cookies partitioned
        auth_header = request.headers.get("X-Refresh-Token") or request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif auth_header:
            token = auth_header.strip()

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    admin, new_access, new_refresh = await AuthService.refresh_tokens(db=db, token=token)
    _set_auth_cookies(response, new_access, new_refresh, is_https=_is_https(request))

    return TokenResponse(
        message="Tokens refreshed",
        token_type="bearer",
        access_token=new_access,
        refresh_token=new_refresh,
    )


# ── POST /auth/logout ─────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response):
    """Clear all auth cookies."""
    _clear_auth_cookies(response, is_https=_is_https(request))
    return MessageResponse(message="Logged out successfully")


# ── GET /auth/me ───────────────────────────────────────────────────

@router.get("/me", response_model=AdminOut)
async def get_me(admin: Admin = Depends(get_current_admin)):
    """Return the current authenticated admin's profile."""
    return admin


# ── PUT /auth/me ───────────────────────────────────────────────────

@router.put("/me", response_model=AdminOut)
async def update_me(
    body: AdminUpdate,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update admin email or password with current-password verification."""
    return await AuthService.update_profile(db=db, admin=admin, body=body)
