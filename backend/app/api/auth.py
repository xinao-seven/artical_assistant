"""
认证 API 路由
- POST /auth/register - 注册
- POST /auth/login    - 登录
- POST /auth/refresh  - 刷新 Token
- GET  /auth/me       - 获取当前用户信息
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    用户注册
    - 邮箱唯一性校验
    - 密码 bcrypt 哈希存储
    """
    user = await auth_service.register_user(
        db, email=request.email, password=request.password, username=request.username
    )
    return user


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录
    - 验证邮箱密码
    - 返回 access_token + refresh_token + 用户信息
    """
    user, access_token, refresh_token = await auth_service.login_user(
        db, email=request.email, password=request.password
    )
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    刷新 Token
    - 用 refresh_token 换取新的 Token 对
    - 旧 refresh_token 失效 (令牌轮换)
    """
    user, access_token, refresh_token = await auth_service.refresh_access_token(
        db, request.refresh_token
    )
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    - 需要携带有效的 access_token
    """
    return current_user
