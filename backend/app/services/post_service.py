"""Service implementing School Board Post business logic and media management."""

import logging
import math
import os
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Admin, Post, PostFile, PostImage
from app.padlet_client import get_padlet_client
from app.repositories.audit_repository import AuditRepository
from app.repositories.post_repository import PostRepository
from app.schemas import PaginatedResponse, PostListOut, PostOut
from app.utils.file_validator import (
    ALLOWED_AUDIO_EXTENSIONS,
    sanitize_filename,
    save_upload_file,
    validate_file_size,
    validate_file_type,
)

logger = logging.getLogger("post_service")
IS_VERCEL = settings.IS_VERCEL


def _try_delete_file(url: str):
    """Safely delete uploaded file from local filesystem."""
    if IS_VERCEL:
        return
    try:
        path = url.lstrip("/")
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        logger.warning("Failed to delete file %s: %s", url, e)


class PostService:
    """Business logic for post publishing, file attachments, and Padlet integration."""

    @staticmethod
    async def list_posts(
        db: AsyncSession,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 12,
    ) -> PaginatedResponse[PostListOut]:
        """Fetch paginated posts with formatted thumbnails."""
        posts, total = await PostRepository.list_paginated(
            db, category=category, search=search, page=page, page_size=page_size
        )

        items = []
        for p in posts:
            thumbnail = p.images[0].url if p.images else None
            items.append(
                PostListOut(
                    id=p.id,
                    title=p.title,
                    description=p.description,
                    category=p.category,
                    subject=p.subject,
                    star_rating=p.star_rating or 5,
                    teacher_note=p.teacher_note,
                    audio_url=p.audio_url,
                    thumbnail_url=thumbnail,
                    likes=p.likes or 0,
                    created_at=p.created_at,
                )
            )

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    @staticmethod
    async def get_post_or_404(db: AsyncSession, post_id: int) -> Post:
        """Fetch post by id or raise HTTP 404."""
        post = await PostRepository.get_by_id(db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity post not found",
            )
        return post

    @staticmethod
    async def like_post(db: AsyncSession, post_id: int) -> int:
        """Increment like count on post."""
        post = await PostRepository.get_by_id(db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
        return await PostRepository.increment_likes(db, post)

    @staticmethod
    async def create_post(
        db: AsyncSession,
        admin: Admin,
        title: str,
        description: str = "",
        category: str = "art",
        subject: Optional[str] = None,
        star_rating: int = 5,
        teacher_note: Optional[str] = None,
        audio: Optional[UploadFile] = None,
        images: List[UploadFile] = [],
        files: List[UploadFile] = [],
    ) -> Post:
        """Create new activity post with drawings, voice recordings, and files."""
        audio_url = None
        if audio and audio.filename:
            await validate_file_type(audio)
            await validate_file_size(audio)
            audio_url, _, _ = await save_upload_file(audio, subdir="audio")

        clean_category = category.lower()
        post = Post(
            title=title,
            description=description,
            category=clean_category,
            subject=subject or category.capitalize(),
            star_rating=max(1, min(5, star_rating)),
            teacher_note=teacher_note,
            audio_url=audio_url,
        )
        post = await PostRepository.create(db, post)

        # Process Drawings / Photos
        for idx, img_file in enumerate(images):
            if img_file.filename:
                await validate_file_type(img_file)
                await validate_file_size(img_file)
                url, filename, _ = await save_upload_file(img_file, subdir="images")
                await PostRepository.add_image(
                    db,
                    PostImage(
                        post_id=post.id,
                        url=url,
                        filename=filename,
                        order=idx,
                    ),
                )

        # Process Worksheets / PDFs / Audio files
        for doc_file in files:
            if doc_file.filename:
                ext = await validate_file_type(doc_file)
                size = await validate_file_size(doc_file)
                subdir = "audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "files"
                url, filename, size = await save_upload_file(doc_file, subdir=subdir)
                safe_name = sanitize_filename(doc_file.filename)
                await PostRepository.add_file(
                    db,
                    PostFile(
                        post_id=post.id,
                        url=url,
                        filename=filename,
                        original_name=safe_name,
                        size_bytes=size,
                        file_type="audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "worksheet",
                    ),
                )

        await AuditRepository.log(
            db,
            "POST_CREATED",
            f"title={title} (category={category})",
            admin_email=admin.email,
        )
        await db.commit()
        return await PostRepository.get_by_id(db, post.id)

    @staticmethod
    async def update_post(
        db: AsyncSession,
        admin: Admin,
        post_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        subject: Optional[str] = None,
        star_rating: Optional[int] = None,
        teacher_note: Optional[str] = None,
        audio: Optional[UploadFile] = None,
        images: List[UploadFile] = [],
        files: List[UploadFile] = [],
        remove_image_ids: Optional[str] = None,
        remove_file_ids: Optional[str] = None,
        remove_audio: Optional[bool] = False,
    ) -> Post:
        """Update school post content, audio notes, and attachments."""
        post = await PostRepository.get_by_id(db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity post not found",
            )

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
                    await PostRepository.delete_image(db, img)

        # Remove specific files
        if remove_file_ids:
            ids_to_remove = [int(x) for x in remove_file_ids.split(",") if x.strip()]
            for f in list(post.files):
                if f.id in ids_to_remove:
                    _try_delete_file(f.url)
                    await PostRepository.delete_file(db, f)

        # Add new images
        existing_img_count = len(post.images)
        for idx, img_file in enumerate(images):
            if img_file.filename:
                await validate_file_type(img_file)
                await validate_file_size(img_file)
                url, filename, _ = await save_upload_file(img_file, subdir="images")
                await PostRepository.add_image(
                    db,
                    PostImage(
                        post_id=post.id,
                        url=url,
                        filename=filename,
                        order=existing_img_count + idx,
                    ),
                )

        # Add new files
        for doc_file in files:
            if doc_file.filename:
                ext = await validate_file_type(doc_file)
                size = await validate_file_size(doc_file)
                subdir = "audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "files"
                url, filename, size = await save_upload_file(doc_file, subdir=subdir)
                safe_name = sanitize_filename(doc_file.filename)
                await PostRepository.add_file(
                    db,
                    PostFile(
                        post_id=post.id,
                        url=url,
                        filename=filename,
                        original_name=safe_name,
                        size_bytes=size,
                        file_type="audio" if ext in ALLOWED_AUDIO_EXTENSIONS else "worksheet",
                    ),
                )

        await AuditRepository.log(
            db, "POST_UPDATED", f"id={post_id}", admin_email=admin.email
        )
        await db.commit()
        return await PostRepository.get_by_id(db, post.id)

    @staticmethod
    async def delete_post(db: AsyncSession, admin: Admin, post_id: int) -> str:
        """Delete activity post and physical storage assets."""
        post = await PostRepository.get_by_id(db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity post not found",
            )

        title = post.title
        if post.audio_url:
            _try_delete_file(post.audio_url)
        for img in post.images:
            _try_delete_file(img.url)
        for f in post.files:
            _try_delete_file(f.url)

        await AuditRepository.log(
            db, "POST_DELETED", f"title={title}", admin_email=admin.email
        )
        await PostRepository.delete_post(db, post)
        return title

    @staticmethod
    async def sync_padlet(db: AsyncSession, admin: Admin, post_id: int) -> None:
        """Mirror post content to Padlet classroom board."""
        post = await PostRepository.get_with_images_only(db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity post not found",
            )

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
        await AuditRepository.log(
            db, "PADLET_SYNC", f"post_id={post_id}", admin_email=admin.email
        )
        await db.commit()
