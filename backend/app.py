# backend/app.py
from __future__ import annotations

import os, time
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

app = FastAPI(title="Will it Rain on My Parade?", version="0.9.0")
logger = logging.getLogger("uvicorn")

FRONTEND_ORIGIN = "https://fantastic-tribble-g4wqj9gj6ggjhg46-8080.app.github.dev"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],           # exact, no trailing slash
    allow_origin_regex=r"https://.*\.(githubpreview|app\.github)\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Request logging (tiny)
@app.middleware("http")
async def _log_paths(request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    return await call_next(request)

#CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Unified error shape
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def err(code: str, msg: str, status: int = 400, details: Any = None, hint: str | None = None):
    return JSONResponse(
        {"error": {"code": code, "message": msg, "details": details or {}, "hint": hint}},
        status_code=status
    )

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return err("VALIDATION_ERROR", "Invalid request payload.", status=422, details=exc.errors())

@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return err("NOT_FOUND", "Route not found.", status=404)
    return err("HTTP_ERROR", str(exc.detail), status=exc.status_code)

#Simple RPM rate limit
_BUCKET: Dict[str, tuple[int,int]] = {}  # ip -> (count, reset_epoch)
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
            content={"error": {"code": "RATE_LIMIT",
                               "message": "Too many requests",
                               "details": {"retry_sec": max(0, reset - now)},
                               "hint": "Reduce request rate or try again shortly."}}
        )
    return await call_next(request)

#Meta / health
@app.get("/")
def root():
    return {"ok": True, "name": app.title, "version": app.version}

@app.get("/api/health")
def health():
    return {"status": "healthy", "time_utc": datetime.now(timezone.utc).isoformat()}

#Routers
try:
    from routers import meta
    app.include_router(meta.router)
except Exception:
    pass

# Main feature routers
from routers import poe, event, export  # noqa: E402
app.include_router(poe.router, prefix="/api")
app.include_router(event.router, prefix="/api")    # ≤7d Event Corridor
app.include_router(export.router, prefix="/api")


