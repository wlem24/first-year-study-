"""FastAPI application entry point for the 1st-Grade Digital School Board."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.database import init_db
from app.routers.auth import limiter
from app.routers import auth as auth_router
from app.routers import posts as posts_router

# ── Environment Detection ──────────────────────────────────────────

IS_VERCEL = settings.IS_VERCEL

# ── Logging ────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")


# ── Lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB and create upload directories. Shutdown: log info."""
    if not IS_VERCEL:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.join(settings.UPLOAD_DIR, "images"), exist_ok=True)
        os.makedirs(os.path.join(settings.UPLOAD_DIR, "audio"), exist_ok=True)
        os.makedirs(os.path.join(settings.UPLOAD_DIR, "files"), exist_ok=True)
    await init_db()
    logger.info("School Board application started (vercel=%s)", IS_VERCEL)
    yield
    logger.info("Application shutting down.")


# ── App ────────────────────────────────────────────────────────────

app = FastAPI(
    title="First-Grade Digital School Board & Portfolio API",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS — strictly allow only the frontend origin
allowed_origins = [settings.FRONTEND_URL]
vercel_url = os.environ.get("VERCEL_URL")
if vercel_url:
    allowed_origins.append(f"https://{vercel_url}")
vercel_project_url = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
if vercel_project_url:
    allowed_origins.append(f"https://{vercel_project_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ── Child Privacy & Security Headers Middleware ────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject strict security headers into every response."""
    response: Response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if IS_VERCEL:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: blob:; "
        "media-src 'self' data: blob:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'"
    )
    return response


# ── Static Files (Uploads: drawings, audio, worksheets) ─────────────

if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "images"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "audio"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "files"), exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# ── Routers (versioned: /api/v1) ──────────────────────────────────

app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(posts_router.router, prefix="/api/v1")


# ── Root ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "ok",
        "app": "First-Grade Digital School Board & Portfolio API",
        "version": "1.0.0",
    }
