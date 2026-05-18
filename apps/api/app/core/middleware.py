import time
import uuid
import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)

# Rate limiter instance (shared across app)
# Use memory storage for local dev when Redis is not available
_limiter_storage = settings.REDIS_URL if not settings.is_sqlite else "memory://"
limiter = Limiter(key_func=get_remote_address, storage_uri=_limiter_storage)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Log request duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
        if duration_ms > 1000:
            logger.warning(
                "Slow request: %s %s took %.1fms",
                request.method,
                request.url.path,
                duration_ms,
            )
        return response


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app."""

    # CORS — must be first. Credentials are required because access/refresh
    # tokens are sent as httpOnly cookies. Wildcard origins are NOT compatible
    # with credentials, so the allowlist must be explicit.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_origin_regex=None,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
        max_age=600,
    )

    # Request ID
    app.add_middleware(RequestIDMiddleware)

    # Timing
    app.add_middleware(TimingMiddleware)

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
