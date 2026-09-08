"""SQLAlchemy ORM models for the 1st-Grade Digital School Board."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Admin(Base):
    """Single parent/teacher admin account."""
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Post(Base):
    """School board pin entry (drawing, worksheet, story, badge, voice recording)."""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="art", index=True, nullable=False)  # reading, art, math, science, badges, activities
    subject = Column(String(100), nullable=True)  # Custom label or tag
    star_rating = Column(Integer, default=5)  # 1 to 5 stars
    teacher_note = Column(Text, nullable=True)  # Encouraging feedback from teacher/mom
    audio_url = Column(String(500), nullable=True)  # Audio recording / reading voice clip
    likes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    images = relationship(
        "PostImage", back_populates="post",
        cascade="all, delete-orphan", order_by="PostImage.order"
    )
    files = relationship(
        "PostFile", back_populates="post",
        cascade="all, delete-orphan"
    )


class PostImage(Base):
    """Photos and drawings pinned to a post."""
    __tablename__ = "post_images"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="images")


class PostFile(Base):
    """Printable worksheets, PDFs, and audio recordings attached to a post."""
    __tablename__ = "post_files"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(50), default="document")  # audio, document, sheet
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="files")


class AuditLog(Base):
    """Audit log for tracking authentication attempts and teacher admin actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    admin_email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
