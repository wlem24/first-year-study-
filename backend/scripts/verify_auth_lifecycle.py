"""Automated Verification Suite for Complete Authentication Lifecycle & SPA Routing."""

import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import ASGITransport, AsyncClient
from app.main import app
from app.database import init_db


async def run_auth_verification():
    print("==================================================")
    print("STARTING AUTHENTICATION LIFECYCLE VERIFICATION")
    print("==================================================")

    # 1. Initialize DB and seed
    await init_db()
    print("[1/5] Database initialized and admin user seeded/verified.")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        # Step 1: Login Test
        print("\n[2/5] Testing POST /api/v1/auth/login with mayan9@gmail.com...")
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "mayan9@gmail.com", "password": "maYan@ram6"},
        )
        assert login_res.status_code == 200, f"Login failed ({login_res.status_code}): {login_res.text}"
        data = login_res.json()
        assert "access_token" in data, "access_token missing from response body"
        assert "access_token" in client.cookies, "access_token missing from cookies"
        print(f"  --> PASS: Login successful. Token: {data['access_token'][:20]}...")

        # Step 2: Validate current session
        print("\n[3/5] Testing GET /api/v1/auth/me (Protected Route)...")
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200, f"/me failed ({me_res.status_code}): {me_res.text}"
        assert me_res.json()["email"] == "mayan9@gmail.com", "Email mismatch in /me"
        print(f"  --> PASS: Authenticated as {me_res.json()['email']}")

        # Step 3: Profile & Password Update Test
        print("\n[4/5] Testing PUT /api/v1/auth/me (Profile & Password Update)...")
        # Update password to temporary password
        temp_pass = "maYan@temp123"
        update_res = await client.put(
            "/api/v1/auth/me",
            json={
                "email": "mayan9@gmail.com",
                "current_password": "maYan@ram6",
                "new_password": temp_pass,
            },
        )
        assert update_res.status_code == 200, f"Update failed: {update_res.text}"
        print("  --> PASS: Password updated successfully.")

        # Verify login with new password
        verify_new_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "mayan9@gmail.com", "password": temp_pass},
        )
        assert verify_new_login.status_code == 200, "Login with updated password failed"
        print("  --> PASS: Login with new password succeeded.")

        # Restore original password for production stability
        restore_res = await client.put(
            "/api/v1/auth/me",
            json={
                "email": "mayan9@gmail.com",
                "current_password": temp_pass,
                "new_password": "maYan@ram6",
            },
        )
        assert restore_res.status_code == 200, "Password restoration failed"
        print("  --> PASS: Original password restored (maYan@ram6).")

        # Step 4: Logout Test
        print("\n[5/5] Testing POST /api/v1/auth/logout...")
        logout_res = await client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200, f"Logout failed: {logout_res.text}"
        print("  --> PASS: Logout endpoint returned 200 OK.")

        # Verify access token is no longer authorized
        post_logout_me = await client.get("/api/v1/auth/me")
        assert post_logout_me.status_code == 401, f"Protected route accessible after logout: {post_logout_me.status_code}"
        print("  --> PASS: Protected route rejected after logout (401 Unauthorized).")

    print("\n==================================================")
    print("ALL 5 AUTHENTICATION LIFECYCLE CHECKS PASSED (100%)")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_auth_verification())
