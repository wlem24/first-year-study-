"""Pydantic schemas for the 1st-Grade Digital School Board."""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field


# ── Auth Schemas ───────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    message: str = "Login successful"
    token_type: str = "bearer"


class AdminOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUpdate(BaseModel):
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


# ── Post Schemas ───────────────────────────────────────────────────

class PostImageOut(BaseModel):
    id: int
    url: str
    filename: str
    order: int

    model_config = ConfigDict(from_attributes=True)


class PostFileOut(BaseModel):
    id: int
    url: str
    filename: str
    original_name: str
    size_bytes: int
    file_type: str

    model_config = ConfigDict(from_attributes=True)


class PostOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    subject: Optional[str] = None
    star_rating: int = 5
    teacher_note: Optional[str] = None
    audio_url: Optional[str] = None
    likes: int = 0
    images: List[PostImageOut] = []
    files: List[PostFileOut] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PostListOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    subject: Optional[str] = None
    star_rating: int = 5
    teacher_note: Optional[str] = None
    audio_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    likes: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Pagination ─────────────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = []
    total: int
    page: int
    page_size: int
    pages: int
