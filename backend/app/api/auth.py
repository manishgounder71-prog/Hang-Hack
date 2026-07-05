"""Authentication API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.auth import create_session, validate_session

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    user_id: str
    email: str = ""


class LoginRequest(BaseModel):
    user_id: str


@router.post("/register")
async def register(req: RegisterRequest):
    if not req.user_id or len(req.user_id) < 2:
        raise HTTPException(status_code=422, detail="user_id must be at least 2 characters")
    session = create_session(req.user_id)
    return {
        "status": "registered",
        "user_id": req.user_id,
        **session,
    }


@router.post("/login")
async def login(req: LoginRequest):
    if not req.user_id:
        raise HTTPException(status_code=422, detail="user_id is required")
    session = create_session(req.user_id)
    return {
        "status": "logged_in",
        "user_id": req.user_id,
        **session,
    }


@router.get("/session")
async def check_session(token: str):
    session = validate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return {"valid": True, **session}
