"""Repository for School Board Post database operations."""

from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Post, PostFile, PostImage


class PostRepository:
    """Encapsulates database access for Post and child attachment entities."""

    @staticmethod
    async def get_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
        """Fetch post by ID with images and files preloaded."""
        result = await db.execute(
            select(Post)
            .options(selectinload(Post.images), selectinload(Post.files))
            .where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_with_images_only(db: AsyncSession, post_id: int) -> Optional[Post]:
        """Fetch post with images preloaded for sync operations."""
        result = await db.execute(
            select(Post)
            .options(selectinload(Post.images))
            .where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_paginated(
        db: AsyncSession,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Post], int]:
        """List posts matching category/search filters with total item count."""
        query = select(Post).options(selectinload(Post.images))
        count_query = select(func.count(Post.id))

        if category and category.lower() != "all":
            clean_category = category.lower()
            query = query.where(Post.category == clean_category)
            count_query = count_query.where(Post.category == clean_category)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_cond = (
                (Post.title.ilike(search_pattern))
                | (Post.description.ilike(search_pattern))
                | (Post.subject.ilike(search_pattern))
            )
            query = query.where(filter_cond)
            count_query = count_query.where(filter_cond)

        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await db.execute(
            query.order_by(Post.created_at.desc()).offset(offset).limit(page_size)
        )
        posts = result.scalars().all()
        return list(posts), total

    @staticmethod
    async def create(db: AsyncSession, post: Post) -> Post:
        """Persist a new post entity."""
        db.add(post)
        await db.flush()
        return post

    @staticmethod
    async def add_image(db: AsyncSession, image: PostImage) -> PostImage:
        """Add image attachment to post."""
        db.add(image)
        return image

    @staticmethod
    async def add_file(db: AsyncSession, file_item: PostFile) -> PostFile:
        """Add document or audio attachment to post."""
        db.add(file_item)
        return file_item

    @staticmethod
    async def delete_image(db: AsyncSession, image: PostImage) -> None:
        """Delete image entity from database."""
        await db.delete(image)

    @staticmethod
    async def delete_file(db: AsyncSession, file_item: PostFile) -> None:
        """Delete file entity from database."""
        await db.delete(file_item)

    @staticmethod
    async def delete_post(db: AsyncSession, post: Post) -> None:
        """Delete post entity and cascaded relationships."""
        await db.delete(post)
        await db.commit()

    @staticmethod
    async def increment_likes(db: AsyncSession, post: Post) -> int:
        """Increment like counter on post."""
        post.likes = (post.likes or 0) + 1
        await db.commit()
        return post.likes
