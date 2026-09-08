"""Application configuration loaded from environment variables."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the 1st-Grade School Board & Portfolio platform."""

    DATABASE_URL: str = "sqlite+aiosqlite:///./school_board.db"

    # Parent / Teacher Admin Credentials
    ADMIN_EMAIL: str = "mayan9@gmail.com"
    ADMIN_PASSWORD_HASH: str = "$2b$12$lkMq2pwFsYY5eyLWbgTN0OG8IwVR7KyHjATkjX5MVMX4INwW0PBOi"

    # JWT Security
    SECRET_KEY: str = "your-secret-key-change-this-to-something-random-and-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # File Uploads (25MB limit for school drawings, audio recordings, and worksheets)
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 25

    # Padlet Classroom Integration
    PADLET_API_KEY: str = ""
    PADLET_BOARD_ID: str = ""

    # ── Computed Properties ────────────────────────────────────────

    @property
    def IS_VERCEL(self) -> bool:
        """Detect if running on Vercel."""
        return bool(os.environ.get("VERCEL"))

    @property
    def EFFECTIVE_UPLOAD_DIR(self) -> str:
        """Return writable upload directory on Vercel or local filesystem."""
        return "/tmp/uploads" if self.IS_VERCEL else self.UPLOAD_DIR

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Return an async-compatible database URL."""
        if self.IS_VERCEL and ("school_board.db" in self.DATABASE_URL or "portfolio.db" in self.DATABASE_URL):
            return "sqlite+aiosqlite:////tmp/school_board.db"
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
