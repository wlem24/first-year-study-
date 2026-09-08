"""Posts router for 1st-Grade School Board delegating to PostService."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models import Admin
from app.schemas import MessageResponse, PaginatedResponse, PostListOut, PostOut
from app.services.post_service import PostService

logger = logging.getLogger("posts_router")

router = APIRouter(prefix="/posts", tags=["posts"])


# ── Public Endpoints (Kid & Family Friendly) ──────────────────────

@router.get("/", response_model=PaginatedResponse[PostListOut])
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all school board posts with pagination and category filtering."""
    return await PostService.list_posts(
        db=db,
        category=category,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Get full details of a school activity post (drawings, audio, worksheets)."""
    return await PostService.get_post_or_404(db=db, post_id=post_id)


@router.post("/{post_id}/like", response_model=MessageResponse)
async def like_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Public endpoint for family/friends to send a heart/like to a post."""
    likes = await PostService.like_post(db=db, post_id=post_id)
    return MessageResponse(message=f"❤️ {likes}")


# ── Teacher / Parent Admin Endpoints ──────────────────────────────

@router.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("art"),
    subject: Optional[str] = Form(default=None),
    star_rating: int = Form(5),
    teacher_note: Optional[str] = Form(default=None),
    audio: Optional[UploadFile] = File(default=None),
    images: List[UploadFile] = File(default=[]),
    files: List[UploadFile] = File(default=[]),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pin a new school activity with drawings, audio voice note, and worksheets."""
    return await PostService.create_post(
        db=db,
        admin=admin,
        title=title,
        description=description,
        category=category,
        subject=subject,
        star_rating=star_rating,
        teacher_note=teacher_note,
        audio=audio,
        images=images,
        files=files,
    )


@router.put("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    title: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    category: Optional[str] = Form(default=None),
    subject: Optional[str] = Form(default=None),
    star_rating: Optional[int] = Form(default=None),
    teacher_note: Optional[str] = Form(default=None),
    audio: Optional[UploadFile] = File(default=None),
    images: List[UploadFile] = File(default=[]),
    files: List[UploadFile] = File(default=[]),
    remove_image_ids: Optional[str] = Form(default=None),
    remove_file_ids: Optional[str] = Form(default=None),
    remove_audio: Optional[bool] = Form(default=False),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a school post, add drawings or remove attachments."""
    return await PostService.update_post(
        db=db,
        admin=admin,
        post_id=post_id,
        title=title,
        description=description,
        category=category,
        subject=subject,
        star_rating=star_rating,
        teacher_note=teacher_note,
        audio=audio,
        images=images,
        files=files,
        remove_image_ids=remove_image_ids,
        remove_file_ids=remove_file_ids,
        remove_audio=remove_audio,
    )


@router.delete("/{post_id}", response_model=MessageResponse)
async def delete_post(
    post_id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a school post and all attached files (teacher admin only)."""
    title = await PostService.delete_post(db=db, admin=admin, post_id=post_id)
    return MessageResponse(message=f"Post '{title}' deleted successfully")


# ── Padlet Classroom Mirroring ────────────────────────────────────

@router.post("/{post_id}/sync-padlet", response_model=MessageResponse)
async def sync_padlet(
    post_id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Sync a student's artwork, reading note, or badge to the Padlet board."""
    await PostService.sync_padlet(db=db, admin=admin, post_id=post_id)
    return MessageResponse(message="Post mirrored to Padlet classroom board!")
