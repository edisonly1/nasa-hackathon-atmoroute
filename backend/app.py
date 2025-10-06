# backend/app.py
from __future__ import annotations

import os
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Routers
from routers import poe, event, export, ai, llm

app = FastAPI(title="Will it Rain on My Parade?", version="0.9.0")
logger = logging.getLogger("uvicorn")

# -------------------------------
# CORS (single, consolidated block)
# -------------------------------
# Priority:
# 1) If CORS_ORIGINS="*" -> allow all
# 2) Else use provided comma-separated origins
# 3) Also allow Codespaces/GitHub preview domains via regex
origins_env = os.getenv("CORS_ORIGINS", "").strip()

if origins_env == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    # Optional hard-coded single origin for convenience (kept from your file)
    FRONTEND_ORIGIN = "https://fantastic-tribble-g4wqj9gj6ggjhg46-8080.app.github.dev"
    if FRONTEND_ORIGIN not in origins:
        origins.append(FRONTEND_ORIGIN)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"https://.*\.(githubpreview|app\.github)\.dev",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# -------------------------------
# Request logging (tiny)
# -------------------------------
@app.middleware("http")
async def _log_paths(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    return await call_next(request)

# rpm rate limit
_BUCKET: Dict[str, tuple[int, int]] = {}  # ip -> (count, reset_epoch)
_LIMIT = int(os.getenv("RATE_LIMIT_RPM", "60"))
_WINDOW = 60

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = int(time.time())
    count, reset = _BUCKET.get(ip, (0, now + _WINDOW))
    if now >= reset:
        count, reset = 0, now + _WINDOW
    count += 1
    _BUCKET[ip] = (count, reset)
    if count > _LIMIT:
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMIT",
                    "message": "Too many requests",
                    "details": {"retry_sec": max(0, reset - now)},
                    "hint": "Reduce request rate or try again shortly.",
                }
            },
        )
    return await call_next(request)

# errorshape
def err(code: str, msg: str, status: int = 400, details: Any = None, hint: str | None = None):
    return JSONResponse(
        {"error": {"code": code, "message": msg, "details": details or {}, "hint": hint}},
        status_code=status,
    )

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return err("VALIDATION_ERROR", "Invalid request payload.", status=422, details=exc.errors())

@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return err("NOT_FOUND", "Route not found.", status=404)
    return err("HTTP_ERROR", str(exc.detail), status=exc.status_code)

# meta/health
@app.get("/")
def root():
    return {"ok": True, "name": app.title, "version": app.version}

@app.get("/api/health")
def health():
    return {"status": "healthy", "time_utc": datetime.now(timezone.utc).isoformat()}

# routers
# If you have a meta router, include it (optional)
try:
    from routers import meta
    app.include_router(meta.router)
except Exception:
    pass

# Main feature routers
# NOTE: poe/event/export keep prefix="/api" (their routers likely use prefix="/poe" etc.)
app.include_router(poe.router, prefix="/api")
app.include_router(event.router, prefix="/api")
app.include_router(export.router, prefix="/api")

# IMPORTANT: AI/LLM routers ALREADY have "/api/ai" and "/api/llm" in their own prefixes.
# So we include them WITHOUT an extra prefix to avoid "/api/api/..."
app.include_router(ai.router)   # no prefix here
app.include_router(llm.router)  # no prefix here
