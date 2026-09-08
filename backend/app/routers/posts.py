"""Posts router for 1st-Grade School Board (public browsing, parent/teacher CRUD)."""

import os
import logging
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.core.config import settings
from app.utils.file_validator import (
    validate_file_type, validate_file_size, save_upload_file, sanitize_filename, get_extension,
    ALLOWED_AUDIO_EXTENSIONS,
)
from app.padlet_client import get_padlet_client
from app.database import get_db
from app.models import Admin, AuditLog, Post, PostFile, PostImage
from app.schemas import MessageResponse, PaginatedResponse, PostListOut, PostOut

logger = logging.getLogger("posts")

IS_VERCEL = bool(os.environ.get("VERCEL"))

router = APIRouter(prefix="/posts", tags=["posts"])


# ── Audit Logger Helper ───────────────────────────────────────────

async def _audit(db: AsyncSession, event: str, detail: str, admin_email: str | None = None):
    db.add(AuditLog(event_type=event, detail=detail, admin_email=admin_email))


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
    query = select(Post).options(selectinload(Post.images))
    count_query = select(func.count(Post.id))

    if category and category.lower() != "all":
        query = query.where(Post.category == category.lower())
        count_query = count_query.where(Post.category == category.lower())

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            (Post.title.ilike(search_pattern)) | (Post.description.ilike(search_pattern)) | (Post.subject.ilike(search_pattern))
        )
        count_query = count_query.where(
            (Post.title.ilike(search_pattern)) | (Post.description.ilike(search_pattern)) | (Post.subject.ilike(search_pattern))
        )

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Post.created_at.desc()).offset(offset).limit(page_size)
    )
    posts = result.scalars().all()

    items = []
    for p in posts:
        thumbnail = p.images[0].url if p.images else None
        items.append(PostListOut(
            id=p.id,
            title=p.title,
            description=p.description,
            category=p.category,
            subject=p.subject,
            star_rating=p.star_rating or 5,
            teacher_note=p.teacher_note,
            audio_url=p.audio_url,
            thumbnail_url=thumbnail,
            created_at=p.created_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Get full details of a school activity post (drawings, audio, worksheets)."""
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images), selectinload(Post.files))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Activity post not found")
    return post


@router.post("/{post_id}/like", response_model=MessageResponse)
async def like_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Public endpoint for family/friends to send a heart/like to a post."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes = (post.likes or 0) + 1
    await db.commit()
    return MessageResponse(message=f"❤️ {post.likes}")


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
    audio_url = None
    if audio and audio.filename:
        await validate_file_type(audio)
        await validate_file_size(audio)
        audio_url, _, _ = await save_upload_file(audio, subdir="audio")

    post = Post(
        title=title,
        description=description,
        category=category.lower(),
        subject=subject or category.capitalize(),
        star_rating=max(1, min(5, star_rating)),
        teacher_note=teacher_note,
        audio_url=audio_url,
    )
    db.add(post)
    await db.flush()

    # Process Drawings / Photos
    for idx, img_file in enumerate(images):
        if img_file.filename:
            await validate_file_type(img_file)
            await validate_file_size(img_file)
            url, filename, _ = await save_upload_file(img_file, subdir="images")
            db.add(PostImage(
                post_id=post.id,
                url=url,
                filename=filename,
                order=idx,
            ))

    # Process Worksheets / PDFs / Audio files
    for doc_file in files:
        if doc_file.filename:
            ext = await validate_file_type(doc_file)
            size = await validate_file_size(doc_file)
            subdir = "audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "files"
            url, filename, size = await save_upload_file(doc_file, subdir=subdir)
            safe_name = sanitize_filename(doc_file.filename)
            db.add(PostFile(
                post_id=post.id,
                url=url,
                filename=filename,
                original_name=safe_name,
                size_bytes=size,
                file_type="audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "worksheet",
            ))

    await _audit(db, "POST_CREATED", f"title={title} (category={category})", admin_email=admin.email)
    await db.commit()
    await db.refresh(post)

    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images), selectinload(Post.files))
        .where(Post.id == post.id)
    )
    return result.scalar_one()


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
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images), selectinload(Post.files))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Activity post not found")

    if title is not None:
        post.title = title
    if description is not None:
        post.description = description
    if category is not None:
        post.category = category.lower()
    if subject is not None:
        post.subject = subject
    if star_rating is not None:
        post.star_rating = max(1, min(5, star_rating))
    if teacher_note is not None:
        post.teacher_note = teacher_note

    # Audio update
    if remove_audio and post.audio_url:
        _try_delete_file(post.audio_url)
        post.audio_url = None

    if audio and audio.filename:
        await validate_file_type(audio)
        await validate_file_size(audio)
        if post.audio_url:
            _try_delete_file(post.audio_url)
        url, _, _ = await save_upload_file(audio, subdir="audio")
        post.audio_url = url

    # Remove specific photos
    if remove_image_ids:
        ids_to_remove = [int(x) for x in remove_image_ids.split(",") if x.strip()]
        for img in list(post.images):
            if img.id in ids_to_remove:
                _try_delete_file(img.url)
                await db.delete(img)

    # Remove specific files
    if remove_file_ids:
        ids_to_remove = [int(x) for x in remove_file_ids.split(",") if x.strip()]
        for f in list(post.files):
            if f.id in ids_to_remove:
                _try_delete_file(f.url)
                await db.delete(f)

    # Add new images
    existing_img_count = len(post.images)
    for idx, img_file in enumerate(images):
        if img_file.filename:
            await validate_file_type(img_file)
            await validate_file_size(img_file)
            url, filename, _ = await save_upload_file(img_file, subdir="images")
            db.add(PostImage(
                post_id=post.id,
                url=url,
                filename=filename,
                order=existing_img_count + idx,
            ))

    # Add new files
    for doc_file in files:
        if doc_file.filename:
            ext = await validate_file_type(doc_file)
            size = await validate_file_size(doc_file)
            subdir = "audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "files"
            url, filename, size = await save_upload_file(doc_file, subdir=subdir)
            safe_name = sanitize_filename(doc_file.filename)
            db.add(PostFile(
                post_id=post.id,
                url=url,
                filename=filename,
                original_name=safe_name,
                size_bytes=size,
                file_type="audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "worksheet",
            ))

    await _audit(db, "POST_UPDATED", f"id={post_id}", admin_email=admin.email)
    await db.commit()

    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images), selectinload(Post.files))
        .where(Post.id == post.id)
    )
    return result.scalar_one()


@router.delete("/{post_id}", response_model=MessageResponse)
async def delete_post(
    post_id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a school post and all attached files (teacher admin only)."""
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images), selectinload(Post.files))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Activity post not found")

    if post.audio_url:
        _try_delete_file(post.audio_url)
    for img in post.images:
        _try_delete_file(img.url)
    for f in post.files:
        _try_delete_file(f.url)

    await _audit(db, "POST_DELETED", f"title={post.title}", admin_email=admin.email)
    await db.delete(post)
    await db.commit()
    return MessageResponse(message=f"Post '{post.title}' deleted successfully")


# ── Padlet Classroom Mirroring ────────────────────────────────────

@router.post("/{post_id}/sync-padlet", response_model=MessageResponse)
async def sync_padlet(
    post_id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Sync a student's artwork, reading note, or badge to the Padlet board."""
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Activity post not found")

    client = get_padlet_client()
    image_url = post.images[0].url if post.images else None

    body_text = post.description or ""
    if post.teacher_note:
        body_text += f"\n\n💬 Teacher Note: {post.teacher_note}"

    await client.create_post(
        title=post.title,
        body=body_text,
        image_url=image_url,
        category=post.category,
        star_rating=post.star_rating,
    )

    await _audit(db, "PADLET_SYNC", f"post_id={post_id}", admin_email=admin.email)
    await db.commit()
    return MessageResponse(message="Post mirrored to Padlet classroom board!")


# ── Helpers ────────────────────────────────────────────────────────

def _try_delete_file(url: str):
    """Safely delete uploaded file from storage (no-op on Vercel read-only FS)."""
    if IS_VERCEL:
        return
    try:
        path = url.lstrip("/")
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        logger.warning("Failed to delete file %s: %s", url, e)
