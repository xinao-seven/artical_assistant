"""
认证相关 Pydantic 模型 (请求/响应)
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ========== 请求模型 ==========

class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(
        ..., min_length=6, max_length=128, description="密码 (6-128位)"
    )
    username: str | None = Field(None, max_length=100, description="用户名 (可选)")


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str = Field(..., description="刷新令牌")


# ========== 响应模型 ==========

class UserResponse(BaseModel):
    """用户信息响应"""
    id: uuid.UUID
    email: str
    username: str | None = None
    avatar: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """登录/注册成功响应 (含 token + 用户信息)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
