"""Comprehensive backend integration test."""
import sys
import os
import asyncio
import io

sys.path.insert(0, os.path.abspath("backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db
from sqlalchemy import select
from app.models import AuditLog

async def run_tests():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n--- 1. Testing Root & Security Headers ---")
        res = await client.get("/")
        assert res.status_code == 200, f"Root failed: {res.status_code}"
        assert res.headers.get("x-frame-options") == "DENY"
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert "Content-Security-Policy" in res.headers or "content-security-policy" in res.headers
        print("  [PASS] Root & Security Headers")

        print("\n--- 2. Testing Public Auth Failure & Rate Limit ---")
        bad_login = await client.post("/api/v1/auth/login", json={"email": "wrong@example.com", "password": "wrong"})
        assert bad_login.status_code == 401
        print("  [PASS] Bad login returned 401 Unauthorized")

        print("\n--- 3. Testing Admin Login (Email & Password) ---")
        login_res = await client.post("/api/v1/auth/login", json={"email": "admin@portfolio.local", "password": "changeme123"})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        assert "access_token" in client.cookies
        print("  [PASS] Admin Login succeeded, cookie set")

        print("\n--- 4. Testing /api/v1/auth/me ---")
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "admin@portfolio.local"
        print(f"  [PASS] /auth/me returned: {me_res.json()}")

        print("\n--- 5. Testing Project Creation (Multipart with Tags & Files) ---")
        png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        pdf_data = b"%PDF-1.4 Mock PDF content for testing"

        files = [
            ("images", ("test_image.png", io.BytesIO(png_data), "image/png")),
            ("files", ("test_doc.pdf", io.BytesIO(pdf_data), "application/pdf")),
        ]
        data = {
            "title": "Stitch & Kuromi Art Showcase",
            "description": "A delightful kid-friendly portfolio project featuring animated SVG vectors.",
            "tags": "art, illustration, vector, stitch, kuromi",
        }

        create_res = await client.post("/api/v1/projects/", data=data, files=files)
        assert create_res.status_code == 201, f"Project creation failed: {create_res.text}"
        proj_data = create_res.json()
        project_id = proj_data["id"]
        assert proj_data["title"] == "Stitch & Kuromi Art Showcase"
        assert len(proj_data["tags"]) == 5
        assert len(proj_data["images"]) == 1
        assert len(proj_data["files"]) == 1
        print(f"  [PASS] Project created successfully (ID: {project_id}) with tags: {proj_data['tags']}")

        print("\n--- 6. Testing Paginated Project List ---")
        list_res = await client.get("/api/v1/projects/?page=1&page_size=10")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] >= 1
        assert list_data["page"] == 1
        assert len(list_data["items"]) >= 1
        print(f"  [PASS] Paginated list returned total={list_data['total']} items, page={list_data['page']}")

        print("\n--- 7. Testing Project Detail ---")
        detail_res = await client.get(f"/api/v1/projects/{project_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == project_id
        assert detail["files"][0]["original_name"] == "test_doc.pdf"
        print(f"  [PASS] Project detail retrieved: {detail['title']}")

        print("\n--- 8. Testing Project Update ---")
        update_data = {
            "title": "Stitch & Kuromi Art Showcase (Updated)",
            "tags": "art, updated, digital",
        }
        update_res = await client.put(f"/api/v1/projects/{project_id}", data=update_data)
        assert update_res.status_code == 200
        assert update_res.json()["title"] == "Stitch & Kuromi Art Showcase (Updated)"
        assert len(update_res.json()["tags"]) == 3
        print(f"  [PASS] Project updated successfully")

        print("\n--- 9. Testing Audit Logs in Database ---")
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            logs = (await session.execute(select(AuditLog))).scalars().all()
            assert len(logs) >= 3
            print(f"  [PASS] Found {len(logs)} audit log entries:")
            for log in logs:
                print(f"     - [{log.event_type}] by {log.admin_email or 'anon'} ({log.detail})")

        print("\n--- 10. Testing Project Delete ---")
        del_res = await client.delete(f"/api/v1/projects/{project_id}")
        assert del_res.status_code == 200
        print(f"  [PASS] Project deleted: {del_res.json()}")

        print("\n--- 11. Testing Logout ---")
        logout_res = await client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200
        print(f"  [PASS] Logout successful")

        print("\nALL TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
