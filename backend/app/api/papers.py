"""
论文 CRUD API 路由
- GET  /papers      - 论文列表 (分页/筛选)
- GET  /papers/{id}  - 论文详情
- POST /papers       - 手动创建论文
- PATCH /papers/{id} - 更新用户关联信息
- DELETE /papers/{id} - 删除论文
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.paper import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperDetailResponse,
    PaperListParams,
    PaginatedResponse,
    PaperDeleteResponse,
)
from app.services import paper_service

router = APIRouter(prefix="/papers", tags=["论文"])


@router.get("", response_model=PaginatedResponse)
async def list_papers(
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    sort: str = Query(default="created_at", description="排序字段"),
    order: str = Query(default="desc", description="排序方向"),
    collection: str | None = Query(default=None, description="按分组筛选"),
    tag: str | None = Query(default=None, description="按标签筛选"),
    keyword: str | None = Query(default=None, description="标题关键词搜索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的论文列表

    - 支持分页、排序、按分组/标签/关键词筛选
    - 每页最多返回 100 条
    """
    params = PaperListParams(
        page=page,
        size=size,
        sort=sort,
        order=order,
        collection=collection,
        tag=tag,
        keyword=keyword,
    )
    items, total = await paper_service.get_papers(db, current_user, params)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{paper_id}", response_model=PaperDetailResponse)
async def get_paper(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取论文详情

    - 含完整文本和用户关联信息
    - 仅论文库拥有者可访问
    """
    paper = await paper_service.get_paper_detail(db, current_user, paper_id)
    return paper_service.paper_to_detail_response(paper)


@router.post("", response_model=PaperResponse, status_code=201)
async def create_paper(
    request: PaperCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    手动录入论文

    - 创建论文记录并自动关联当前用户
    - 支持设置标签、笔记和分组
    """
    return await paper_service.create_paper(db, current_user, request)


@router.patch("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: uuid.UUID,
    request: PaperUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新论文的用户关联信息

    - 可更新标签、笔记、分组
    - 不会修改论文本身的数据
    """
    return await paper_service.update_user_paper(
        db, current_user, paper_id, request
    )


@router.delete("/{paper_id}", response_model=PaperDeleteResponse)
async def delete_paper(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除论文

    - 同时删除上传的 PDF 文件
    - 级联删除用户关联和分块数据
    - 仅论文拥有者可操作
    """
    await paper_service.delete_paper(db, current_user, paper_id)
    return PaperDeleteResponse(detail="已删除")
