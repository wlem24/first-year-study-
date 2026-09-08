"""Vercel serverless entry point for the FastAPI backend."""

import sys
import os

# Add the backend directory to Python's module search path
# so that `from app.main import app` resolves correctly.
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Vercel sets VERCEL=1 automatically; ensure it's available
os.environ.setdefault("VERCEL", "1")

from app.main import app  # noqa: E402, F401 — Vercel auto-detects this ASGI app
