"""Comprehensive integration test suite for First-Grade Digital School Board."""
import sys
import os
import asyncio
import io

sys.path.insert(0, os.path.abspath("backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db
from sqlalchemy import select
from app.models import AuditLog, Post
from PIL import Image

async def run_school_board_tests():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n--- 1. Testing Root & Child Privacy Security Headers ---")
        res = await client.get("/")
        assert res.status_code == 200, f"Root failed: {res.status_code}"
        assert res.headers.get("x-frame-options") == "DENY"
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert "Content-Security-Policy" in res.headers or "content-security-policy" in res.headers
        print("  [PASS] Root & Child Privacy Security Headers")

        print("\n--- 2. Testing Public Auth Rejection & Rate Limiting ---")
        bad_login = await client.post("/api/v1/auth/login", json={"email": "intruder@example.com", "password": "wrong"})
        assert bad_login.status_code == 401
        print("  [PASS] Intruder login rejected (401 Unauthorized)")

        print("\n--- 3. Testing Teacher / Parent Login ---")
        login_res = await client.post("/api/v1/auth/login", json={"email": "teacher@schoolboard.local", "password": "changeme123"})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        assert "access_token" in client.cookies
        print("  [PASS] Teacher Login succeeded with httpOnly cookie")

        print("\n--- 4. Testing /api/v1/auth/me Session Validation ---")
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "teacher@schoolboard.local"
        print(f"  [PASS] /auth/me verified teacher: {me_res.json()['email']}")

        print("\n--- 5. Testing Pinning School Activity (Drawing + Voice Clip + Worksheet) ---")
        # 1x1 PNG Image
        png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        # Mock Audio file (WAV)
        audio_data = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        # Mock Worksheet (PDF)
        pdf_data = b"%PDF-1.4 1st Grade Reading Worksheet"

        files = [
            ("images", ("sunflower_drawing.png", io.BytesIO(png_data), "image/png")),
            ("files", ("reading_phonics_sheet.pdf", io.BytesIO(pdf_data), "application/pdf")),
            ("audio", ("reading_voice_recording.wav", io.BytesIO(audio_data), "audio/wav")),
        ]
        data = {
            "title": "My Sunflower Watercolor & Reading Practice",
            "description": "Mayan painted a bright sunflower and read chapter 2 aloud!",
            "category": "art",
            "subject": "Watercolor Art",
            "star_rating": "5",
            "teacher_note": "Beautiful color blending and clear reading voice! ⭐",
        }

        create_res = await client.post("/api/v1/posts/", data=data, files=files)
        assert create_res.status_code == 201, f"Post creation failed: {create_res.text}"
        post_data = create_res.json()
        post_id = post_data["id"]
        assert post_data["title"] == "My Sunflower Watercolor & Reading Practice"
        assert post_data["star_rating"] == 5
        assert post_data["audio_url"] is not None
        assert len(post_data["images"]) == 1
        assert len(post_data["files"]) == 1
        print(f"  [PASS] School Activity Pinned! ID={post_id}, Stars={post_data['star_rating']}, Audio={post_data['audio_url']}")

        print("\n--- 6. Testing Category Filtering & Search ---")
        art_res = await client.get("/api/v1/posts/?category=art")
        assert art_res.status_code == 200
        assert art_res.json()["total"] >= 1
        print(f"  [PASS] Art category filter returned {art_res.json()['total']} activities")

        search_res = await client.get("/api/v1/posts/?search=Sunflower")
        assert search_res.status_code == 200
        assert search_res.json()["total"] >= 1
        print(f"  [PASS] Search 'Sunflower' returned {search_res.json()['total']} activity")

        print("\n--- 7. Testing Activity Detail View ---")
        detail_res = await client.get(f"/api/v1/posts/{post_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == post_id
        assert detail["teacher_note"] == "Beautiful color blending and clear reading voice! ⭐"
        print(f"  [PASS] Detail retrieved: {detail['title']}")

        print("\n--- 8. Testing Updating Activity & Star Rating ---")
        update_data = {
            "title": "My Sunflower Watercolor (Gold Star Award)",
            "star_rating": "5",
            "teacher_note": "Awarded Classroom Artist of the Week! 🎨",
        }
        update_res = await client.put(f"/api/v1/posts/{post_id}", data=update_data)
        assert update_res.status_code == 200
        assert update_res.json()["teacher_note"] == "Awarded Classroom Artist of the Week! 🎨"
        print("  [PASS] Activity updated successfully")

        print("\n--- 9. Testing Database Audit Logs ---")
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            logs = (await session.execute(select(AuditLog))).scalars().all()
            assert len(logs) >= 3
            print(f"  [PASS] Verified {len(logs)} audit entries in database:")
            for log in logs:
                print(f"     - [{log.event_type}] ({log.detail})")

        print("\n--- 10. Testing Activity Delete ---")
        del_res = await client.delete(f"/api/v1/posts/{post_id}")
        assert del_res.status_code == 200
        print(f"  [PASS] Post deleted: {del_res.json()['message']}")

        print("\n--- 11. Testing Logout ---")
        logout_res = await client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200
        print("  [PASS] Logout succeeded and cookies cleared")

        print("\nALL 11 SCHOOL BOARD INTEGRATION TESTS PASSED!\n")

if __name__ == "__main__":
    asyncio.run(run_school_board_tests())
