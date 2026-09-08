"""Vercel Serverless Function entry point for the FastAPI backend."""

import os
import sys

# Ensure backend directory is in python search path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["VERCEL"] = "1"

from app.main import app  # noqa: E402, F401
