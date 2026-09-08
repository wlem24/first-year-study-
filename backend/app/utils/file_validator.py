"""File validator for the 1st-Grade School Board.

Supports photos, drawings, audio recordings, and school worksheets with
magic-byte verification, filename sanitization, and 25MB limits.
"""

import os
import re
import uuid
import logging
from typing import Set, Dict

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.utils.image_sanitizer import strip_image_exif

logger = logging.getLogger("file_validator")

# ── Allowed Extensions ─────────────────────────────────────────────

ALLOWED_IMAGE_EXTENSIONS: Set[str] = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_AUDIO_EXTENSIONS: Set[str] = {"mp3", "wav", "m4a", "ogg"}
ALLOWED_DOC_EXTENSIONS: Set[str] = {"pdf", "zip", "doc", "docx", "pptx"}

ALLOWED_EXTENSIONS: Set[str] = (
    ALLOWED_IMAGE_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS | ALLOWED_DOC_EXTENSIONS
)

# ── Magic Byte Signatures ─────────────────────────────────────────

MAGIC_BYTES: Dict[str, list] = {
    # Images
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "gif": [b"GIF87a", b"GIF89a"],
    "webp": [b"RIFF"],
    # Audio
    "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "wav": [b"RIFF"],
    "ogg": [b"OggS"],
    "m4a": [b"\x00\x00\x00\x18ftypM4A", b"\x00\x00\x00\x20ftypM4A", b"\x00\x00\x00"],
    # Documents & Worksheets
    "pdf": [b"%PDF"],
    "zip": [b"PK\x03\x04", b"PK\x05\x06"],
    "doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    "docx": [b"PK\x03\x04"],
    "pptx": [b"PK\x03\x04"],
}


def get_extension(filename: str) -> str:
    """Return the lowercase file extension without the dot."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and special char issues."""
    name = os.path.basename(filename)
    name = re.sub(r"[^\w.\-]", "_", name)
    name = re.sub(r"[_.]{2,}", "_", name)
    return name[:200] if name else "school_work"


async def validate_file_type(file: UploadFile) -> str:
    """Validate file extension and magic byte signature."""
    ext = get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File format '.{ext}' is not supported. "
                   f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read first 16 bytes for signature check
    header = await file.read(16)
    await file.seek(0)

    signatures = MAGIC_BYTES.get(ext, [])
    if signatures:
        matched = any(header.startswith(sig) for sig in signatures)
        if not matched and ext not in {"m4a", "docx", "pptx"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match '.{ext}' format signature.",
            )

    return ext


async def validate_file_size(file: UploadFile) -> int:
    """Validate that the file size is under MAX_FILE_SIZE_MB (25MB)."""
    file.file.seek(0, 2)
    file_size = file.file.tell()
    await file.seek(0)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large ({file_size / 1024 / 1024:.1f} MB). "
                   f"Maximum allowed is {settings.MAX_FILE_SIZE_MB} MB.",
        )
    return file_size


async def save_upload_file(file: UploadFile, subdir: str = "") -> tuple[str, str, int]:
    """Save an uploaded file with privacy protection (stripping EXIF for images).

    Returns:
        tuple of (relative_url, unique_filename, size_bytes)
    """
    ext = get_extension(file.filename or "file.bin")
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(settings.UPLOAD_DIR, subdir)
    os.makedirs(upload_path, exist_ok=True)

    full_path = os.path.join(upload_path, unique_name)
    raw_content = await file.read()

    # If it's an image, sanitize EXIF data
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        content = strip_image_exif(raw_content, ext)
    else:
        content = raw_content

    with open(full_path, "wb") as f:
        f.write(content)

    relative_url = f"/uploads/{subdir}/{unique_name}" if subdir else f"/uploads/{unique_name}"
    return relative_url, unique_name, len(content)
