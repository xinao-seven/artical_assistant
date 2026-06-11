"""
API 路由聚合
将所有子路由汇聚到统一的路由器
"""
from fastapi import APIRouter

from app.api.auth import router as auth_router

# 创建 v1 版本路由
api_router = APIRouter(prefix="/api/v1")

# 注册子路由
api_router.include_router(auth_router)

# 后续步骤逐步添加:
# from app.api.papers import router as papers_router
# api_router.include_router(papers_router)
# from app.api.upload import router as upload_router
# api_router.include_router(upload_router)
# from app.api.search import router as search_router
# api_router.include_router(search_router)
