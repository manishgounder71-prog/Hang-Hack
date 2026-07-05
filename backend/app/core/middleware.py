"""Rate limiting and request validation middleware."""
import time
import logging
from collections import defaultdict

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60.0

        self.clients[client_ip] = [t for t in self.clients[client_ip] if now - t < window]
        if len(self.clients[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        self.clients[client_ip].append(now)
        return await call_next(request)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    MAX_CONTENT_LENGTH = 100_000  # 100KB

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Max {self.MAX_CONTENT_LENGTH} bytes."},
            )
        return await call_next(request)
