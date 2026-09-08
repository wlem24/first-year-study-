"""Vercel Serverless Function entry point for the FastAPI backend."""

import os
import sys
import traceback

# Ensure backend directory is in python search path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

os.environ["VERCEL"] = "1"

import_error = None
fastapi_app = None

try:
    from app.main import app as _app
    fastapi_app = _app
except Exception:
    import_error = traceback.format_exc()


class VercelPathResolver:
    """
    ASGI middleware ensuring that Vercel rewritten paths
    (e.g., from x-matched-path or x-invoke-path) are properly mapped to FastAPI routes.
    """
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            if import_error:
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"text/plain; charset=utf-8"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": f"Backend Import Error:\n{import_error}".encode("utf-8"),
                })
                return

            raw_path = scope.get("path", "")
            headers = dict(scope.get("headers", []))

            # Inspect headers injected by Vercel Edge proxy
            matched_path = None
            for key, val in headers.items():
                k_lower = key.lower()
                if k_lower in (b"x-matched-path", b"x-now-route-matches", b"x-invoke-path"):
                    try:
                        decoded = val.decode("utf-8").split("?")[0]
                        if decoded and not decoded.endswith(".py"):
                            matched_path = decoded
                            break
                    except Exception:
                        pass

            # Extract __vercel_path__ if passed by vercel.json rewrite
            raw_qs = scope.get("query_string", b"").decode("utf-8")
            if "__vercel_path__=" in raw_qs:
                from urllib.parse import parse_qs, urlencode
                params = parse_qs(raw_qs, keep_blank_values=True)
                if "__vercel_path__" in params:
                    scope["path"] = params.pop("__vercel_path__")[0]
                    # Reconstruct query string without __vercel_path__
                    scope["query_string"] = urlencode(params, doseq=True).encode("utf-8")
            elif matched_path and matched_path.startswith("/api"):
                scope["path"] = matched_path
            elif raw_path in ("/api/index.py", "/api/index"):
                scope["path"] = "/api"

            try:
                await self.inner_app(scope, receive, send)
            except Exception:
                err = traceback.format_exc()
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"text/plain; charset=utf-8"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": f"Runtime Execution Error:\n{err}".encode("utf-8"),
                })
                return
        else:
            if self.inner_app:
                await self.inner_app(scope, receive, send)


app = VercelPathResolver(fastapi_app)
