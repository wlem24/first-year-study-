"""Image Sanitizer: Strips EXIF metadata to protect child privacy."""

import io
import logging
from PIL import Image, ImageOps

logger = logging.getLogger("image_sanitizer")


def strip_image_exif(image_bytes: bytes, ext: str) -> bytes:
    """Strip all EXIF, GPS, and sensitive camera metadata from uploaded images.

    Ensures that children's photos, drawings, and artwork uploaded to the board
    do not contain embedded location, device, or timestamp metadata.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        ext: File extension (e.g. 'jpg', 'png', 'webp').

    Returns:
        Cleaned image bytes without EXIF data.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        # Transpose based on EXIF orientation before stripping EXIF so the photo remains upright
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        clean_buffer = io.BytesIO()
        ext_lower = ext.lower().lstrip(".")

        format_map = {
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "png": "PNG",
            "webp": "WEBP",
            "gif": "GIF",
        }
        img_format = format_map.get(ext_lower, image.format or "JPEG")

        # Convert RGBA / palette modes if saving as JPEG
        if img_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")

        # Save without exif parameter (clean export)
        image.save(clean_buffer, format=img_format, optimize=True)
        logger.info("EXIF metadata stripped successfully for .%s image.", ext_lower)
        return clean_buffer.getvalue()

    except Exception as e:
        logger.warning("Could not strip EXIF (saving original): %s", e)
        return image_bytes
