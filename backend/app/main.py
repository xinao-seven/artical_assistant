"""
FastAPI 应用入口
- 创建 FastAPI 实例
- 配置 CORS 中间件
- 注册路由
- 生命周期事件 (启动时初始化，关闭时清理)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ===== 启动时 =====
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    # TODO: 初始化数据库连接池
    # TODO: 加载 Embedding 模型
    yield
    # ===== 关闭时 =====
    logger.info("应用关闭")
    # TODO: 关闭数据库连接池


# 创建 FastAPI 实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS (开发环境允许前端跨域访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 健康检查端点 ==========
@app.get("/health", tags=["System"])
async def health_check():
    """健康检查 - Docker 用"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# ========== 注册路由 ==========
from app.api.router import api_router
app.include_router(api_router)
