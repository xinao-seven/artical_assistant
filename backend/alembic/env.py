"""
Alembic 环境配置
用于自动生成和执行数据库迁移脚本
"""
import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# 将项目根目录加入 Python 路径，确保能导入 app 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings

# Alembic Config 对象
config = context.config

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 数据库 URL (使用异步驱动)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 导入所有模型，确保 Alembic 能检测到
# TODO: 后续步骤逐步导入
# from app.models.user import User
# from app.models.paper import Paper
# 等等...

# 目标元数据 (当前为空，后续步骤逐步添加)
target_metadata = None  # 改为 Base.metadata 导入后


def run_migrations_offline():
    """离线模式: 生成 SQL 脚本而不连接数据库"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """在线模式: 连接数据库并执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """在线模式 (异步)"""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# 判断运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    # 在异步环境中运行
    # 注意: alembic 的 run_migrations_online 是同步函数，
    # 这里我们包装成异步
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        loop.run_until_complete(run_migrations_online())
    except RuntimeError:
        asyncio.run(run_migrations_online())
