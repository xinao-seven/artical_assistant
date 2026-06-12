"""
认证业务逻辑
- 注册: 验证邮箱唯一性 + bcrypt 哈希密码
- 登录: 验证密码 + 生成 JWT
- Token 刷新: 验证 refresh_token + 颁发新 token
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, RefreshToken


# ========== 密码工具 ==========

def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希"""
    # bcrypt 要求密码不超过 72 字节 (UTF-8)
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ========== JWT 工具 ==========

def create_access_token(user_id: uuid.UUID) -> str:
    """生成访问令牌 (短期, 默认30分钟)"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": str(uuid.uuid4()),  # 唯一标识，防止令牌完全相同
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """生成刷新令牌 (长期, 默认7天)"""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid.uuid4()),  # 唯一标识，防止令牌完全相同
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 JWT Token"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )


# ========== 认证业务逻辑 ==========


async def register_user(
    db: AsyncSession, email: str, password: str, username: str | None = None
) -> User:
    """
    注册新用户
    - 检查邮箱是否已注册
    - 对密码进行 bcrypt 哈希
    - 创建用户记录

    Raises:
        HTTPException 409: 邮箱已注册
    """
    # 检查邮箱唯一性
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )

    # 创建用户
    user = User(
        email=email,
        password_hash=hash_password(password),
        username=username,
    )
    db.add(user)
    await db.flush()  # 获取 UUID
    await db.refresh(user)
    return user


async def login_user(
    db: AsyncSession, email: str, password: str
) -> tuple[User, str, str]:
    """
    用户登录
    - 验证邮箱和密码
    - 生成 access_token 和 refresh_token
    - 将 refresh_token 存储到数据库

    Returns:
        (user, access_token, refresh_token)

    Raises:
        HTTPException 401: 邮箱或密码错误
        HTTPException 403: 账号已禁用
    """
    # 查找用户
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 检查账号是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员",
        )

    # 生成 Token
    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(user.id)

    # 存储 refresh_token 到数据库
    refresh_token_expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=refresh_token_expire,
    )
    db.add(refresh_token_record)
    await db.flush()

    return user, access_token, refresh_token_str


async def refresh_access_token(
    db: AsyncSession, refresh_token_str: str
) -> tuple[User, str, str]:
    """
    刷新 Token
    - 验证 refresh_token 有效性 (JWT 签名 + 数据库记录)
    - 删除旧的 refresh_token
    - 颁发新的 access_token 和 refresh_token

    Returns:
        (user, new_access_token, new_refresh_token)

    Raises:
        HTTPException 401: Token 无效或过期
    """
    # 1. 解码 JWT 验证签名和过期
    payload = decode_token(refresh_token_str)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 类型错误",
        )

    user_id = uuid.UUID(payload["sub"])

    # 2. 在数据库中查找该 token
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == refresh_token_str)
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已被使用或无效",
        )

    # 3. 查找用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    # 4. 删除旧的 refresh_token (令牌轮换，防止重放攻击)
    await db.delete(stored_token)

    # 5. 生成新的 Token 对
    new_access_token = create_access_token(user.id)
    new_refresh_token_str = create_refresh_token(user.id)

    # 6. 存储新的 refresh_token
    new_expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    new_refresh_record = RefreshToken(
        user_id=user.id,
        token=new_refresh_token_str,
        expires_at=new_expire,
    )
    db.add(new_refresh_record)
    await db.flush()

    return user, new_access_token, new_refresh_token_str


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """根据 ID 获取用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
