"""Authentication and authorization module."""
import hashlib
import hmac
import time
import logging
from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

SESSIONS: dict[str, dict] = {}
SESSION_TTL = 86400  # 24 hours


def _generate_token(user_id: str) -> str:
    payload = f"{user_id}:{int(time.time())}:{settings.SECRET_KEY}"
    return hashlib.sha256(payload.encode()).hexdigest()


def create_session(user_id: str) -> dict:
    token = _generate_token(user_id)
    SESSIONS[token] = {
        "user_id": user_id,
        "created_at": time.time(),
        "expires_at": time.time() + SESSION_TTL,
    }
    return {"token": token, "user_id": user_id, "expires_at": SESSIONS[token]["expires_at"]}


def validate_session(token: str) -> Optional[dict]:
    session = SESSIONS.get(token)
    if not session:
        return None
    if time.time() > session["expires_at"]:
        del SESSIONS[token]
        return None
    return session


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None,
) -> str:
    if not settings.AUTH_ENABLED:
        return "default"

    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    session = validate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return session["user_id"]
