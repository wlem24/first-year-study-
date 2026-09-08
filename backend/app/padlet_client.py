"""Padlet Classroom API client for mirroring student work and badges."""

import logging
from typing import Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("padlet_client")


class PadletClient:
    """Encapsulates Padlet REST API communication for the school board."""

    BASE_URL = "https://api.padlet.dev/v1"

    def __init__(self):
        if not settings.PADLET_API_KEY or not settings.PADLET_BOARD_ID:
            raise HTTPException(
                status_code=400,
                detail="Padlet API key and Board ID are not configured in .env",
            )
        self.api_key = settings.PADLET_API_KEY
        self.board_id = settings.PADLET_BOARD_ID

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_post(
        self,
        title: str,
        body: str = "",
        image_url: Optional[str] = None,
        category: Optional[str] = None,
        star_rating: Optional[int] = None,
    ) -> dict:
        """Create a new post on the school's Padlet board with subject and star badge.

        Args:
            title: Post title / activity name.
            body: Description and teacher encouragement note.
            image_url: Optional photo or drawing attachment URL.
            category: Subject category (Art, Reading, Math, Science, Badges).
            star_rating: Student star rating (1-5 stars).

        Returns:
            Padlet API response dictionary.
        """
        stars_display = "⭐" * (star_rating or 5)
        subject_tag = f"[{category.upper()}] " if category else ""
        formatted_subject = f"{subject_tag}{title} ({stars_display})"

        payload = {
            "subject": formatted_subject,
            "body": body,
        }
        if image_url:
            payload["image"] = image_url

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/boards/{self.board_id}/posts",
                json=payload,
                headers=self._headers(),
                timeout=15.0,
            )

        if resp.status_code not in (200, 201):
            logger.error(
                "Padlet sync failed: %s %s", resp.status_code, resp.text[:200]
            )
            raise HTTPException(
                status_code=502, detail="Failed to sync post with Padlet board"
            )

        logger.info("School post '%s' synced to Padlet successfully.", title)
        return resp.json()


def get_padlet_client() -> PadletClient:
    """Factory function returning a configured PadletClient instance."""
    return PadletClient()
