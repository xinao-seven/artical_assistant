"""
数据库会话管理
- 创建异步 SQLAlchemy 引擎和会话工厂
- 提供 Base 元数据，供所有模型继承
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # 开发环境打印 SQL
    pool_size=10,                 # 连接池大小
    max_overflow=20,              # 最大溢出连接
    pool_pre_ping=True,           # 每次使用前检查连接有效性
)

# 异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,       # 提交后不过期对象 (防止懒加载报错)
)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


async def get_db() -> AsyncSession:
    """
    获取数据库会话 (FastAPI 依赖注入用)
    每次请求创建一个新会话，请求结束后自动关闭
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
