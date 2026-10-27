from fastapi import APIRouter, Depends, Response

import config
from dependencies import get_current_user
from schemas.auth_schemas import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from schemas.dna import ErrorResponse
from services import user_service
from utils import security

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# NOTE: these are plain `def` (not async) on purpose - password hashing is slow
# CPU work, and FastAPI runs `def` routes in a thread pool so it doesn't block.


@router.post(
    "/register",
    status_code=201,
    response_model=RegisterResponse,
    summary="Create an account",
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        422: {"model": ErrorResponse, "description": "Invalid email or weak password"},
    },
)
def register(data: RegisterRequest):
    user = user_service.register_user(data.email, data.password)
    return {"success": True, "message": "Account created", "user": user}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive a JWT access token",
    responses={401: {"model": ErrorResponse, "description": "Invalid email or password"}},
)
def login(data: LoginRequest, response: Response):
    user = user_service.authenticate_user(data.email, data.password)
    token = security.create_access_token(user["id"], user["role"])
    response.headers["Cache-Control"] = "no-store"
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "expires_in": config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Who am I? (needs a valid token)",
    responses={401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"}},
)
def me(current_user: dict = Depends(get_current_user)):
    return {"success": True, "user": current_user}
