"""
论文业务逻辑层
- 论文 CRUD (创建/读取/更新/删除)
- 用户论文关联管理
- 分页与筛选
"""
import uuid
import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy import select, func, delete, desc, asc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, contains_eager

from app.config import settings
from app.models.paper import Paper, UserPaper
from app.models.user import User
from app.schemas.paper import (
    PaperCreate,
    PaperUpdate,
    PaperListParams,
    PaperResponse,
    PaperDetailResponse,
)
from app.utils.pdf_parser import extract_pdf_metadata


# ========== 论文 CRUD ==========


async def create_paper(
    db: AsyncSession,
    user: User,
    data: PaperCreate,
) -> PaperResponse:
    """
    手动创建论文，同时建立用户关联

    Args:
        db: 数据库会话
        user: 当前登录用户
        data: 论文数据

    Returns:
        PaperResponse
    """
    # 创建论文记录
    paper = Paper(
        title=data.title,
        authors=data.authors,
        abstract=data.abstract,
        doi=data.doi,
        arxiv_id=data.arxiv_id,
        source="manual",
        source_url=data.source_url,
        year=data.year,
        journal=data.journal,
    )
    db.add(paper)
    await db.flush()  # 获取 UUID

    # 创建用户关联
    user_paper = UserPaper(
        user_id=user.id,
        paper_id=paper.id,
        tags=data.tags,
        notes=data.notes,
        collection=data.collection,
    )
    db.add(user_paper)
    await db.flush()

    # 重新查询以预加载 user_papers 关系（异步下不能延迟加载）
    refreshed_paper = await get_paper_detail(db, user, paper.id)
    logger.info(f"用户 {user.email} 创建论文: {paper.title[:50]}")
    return paper_to_response(refreshed_paper)


async def get_papers(
    db: AsyncSession,
    user: User,
    params: PaperListParams,
) -> tuple[list[PaperResponse], int]:
    """
    获取当前用户的论文列表（分页 + 筛选）

    Args:
        db: 数据库会话
        user: 当前用户
        params: 查询参数

    Returns:
        (PaperResponse 列表, 总数)
    """
    # 基础查询：用户关联的论文
    base_query = (
        select(Paper)
        .join(UserPaper, UserPaper.paper_id == Paper.id)
        .where(UserPaper.user_id == user.id)
    )

    # 条件筛选
    if params.collection:
        base_query = base_query.where(UserPaper.collection == params.collection)

    if params.tag:
        # PostgreSQL 数组包含查询 (tags @> ARRAY[tag])
        base_query = base_query.where(UserPaper.tags.contains([params.tag]))

    if params.keyword:
        # 标题关键词搜索 (ILIKE 不区分大小写)
        keyword_filter = f"%{params.keyword}%"
        base_query = base_query.where(
            Paper.title.ilike(keyword_filter)
        )

    # 计数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 排序
    sort_column = getattr(Paper, params.sort, Paper.created_at)
    order_func = desc if params.order.lower() == "desc" else asc
    base_query = base_query.order_by(order_func(sort_column))

    # 分页
    offset = (params.page - 1) * params.size
    base_query = base_query.offset(offset).limit(params.size)

    # 加载用户关联信息 (用 contains_eager 复用已有 JOIN)
    base_query = base_query.options(
        contains_eager(Paper.user_papers)
    )

    result = await db.execute(base_query)
    papers = list(result.scalars().unique().all())

    return [paper_to_response(p) for p in papers], total


async def get_paper_detail(
    db: AsyncSession,
    user: User,
    paper_id: uuid.UUID,
) -> Paper:
    """
    获取论文详情（含用户关联信息）

    Args:
        db: 数据库会话
        user: 当前用户
        paper_id: 论文 ID

    Returns:
        Paper 对象

    Raises:
        HTTPException 404: 论文不存在或无权访问
    """
    query = (
        select(Paper)
        .join(UserPaper, UserPaper.paper_id == Paper.id)
        .where(
            UserPaper.user_id == user.id,
            Paper.id == paper_id,
        )
        .options(
            contains_eager(Paper.user_papers)
        )
    )

    result = await db.execute(query)
    paper = result.scalars().unique().first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在或无权访问",
        )

    return paper


async def delete_paper(
    db: AsyncSession,
    user: User,
    paper_id: uuid.UUID,
) -> None:
    """
    删除论文 (仅限论文拥有者，同时清理上传文件)

    Args:
        db: 数据库会话
        user: 当前用户
        paper_id: 论文 ID

    Raises:
        HTTPException 404: 论文不存在
        HTTPException 403: 无权操作
    """
    # 查找论文
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在",
        )

    # 检查是否为拥有者 (通过 user_papers 关联)
    user_paper_result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == paper_id,
        )
    )
    if not user_paper_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此论文",
        )

    # 清理上传的 PDF 文件
    if paper.file_path:
        file_path = Path(paper.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"已删除论文文件: {paper.file_path}")

    # 级联删除 (user_papers 已设置 cascade)
    await db.delete(paper)
    await db.flush()

    logger.info(f"用户 {user.email} 删除论文: {paper.title[:50]}")


async def update_user_paper(
    db: AsyncSession,
    user: User,
    paper_id: uuid.UUID,
    data: PaperUpdate,
) -> PaperResponse:
    """
    更新用户对论文的关联信息 (标签/笔记/分组)

    Args:
        db: 数据库会话
        user: 当前用户
        paper_id: 论文 ID
        data: 更新数据

    Returns:
        PaperResponse
    """
    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == paper_id,
        )
    )
    user_paper = result.scalar_one_or_none()

    if not user_paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不在您的论文库中",
        )

    # 更新字段
    if data.tags is not None:
        user_paper.tags = data.tags
    if data.notes is not None:
        user_paper.notes = data.notes
    if data.collection is not None:
        user_paper.collection = data.collection

    await db.flush()
    await db.refresh(user_paper)

    # 返回完整的论文响应（含更新后的用户关联信息）
    paper = await get_paper_detail(db, user, paper_id)
    return paper_to_response(paper)


# ========== PDF 上传处理 ==========


async def upload_and_parse_pdf(
    db: AsyncSession,
    user: User,
    file: UploadFile,
) -> Paper:
    """
    上传 PDF 并自动入库

    流程:
    1. 校验文件类型和大小
    2. 保存到 uploads 目录
    3. 解析 PDF 文本和元数据
    4. 创建 Paper 记录 + UserPaper 关联

    Args:
        db: 数据库会话
        user: 当前用户
        file: 上传的 PDF 文件

    Returns:
        新创建的 Paper 对象

    Raises:
        HTTPException 400: 文件类型不支持
        HTTPException 413: 文件过大
    """
    # 校验文件类型
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 PDF 文件格式",
        )

    # 校验文件大小 (读取文件内容)
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)

    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小 ({file_size_mb:.1f}MB) 超过限制 ({settings.MAX_UPLOAD_SIZE_MB}MB)",
        )

    # 生成唯一文件名并保存
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 文件名: {user_id}_{uuid}_{original_name}
    safe_filename = f"{user.id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = upload_dir / safe_filename
    file_path.write_bytes(file_bytes)

    logger.info(f"PDF 已保存: {file_path} ({file_size_mb:.1f}MB)")

    # 解析 PDF
    metadata = extract_pdf_metadata(str(file_path))
    logger.info(f"PDF 解析完成: 标题={metadata.get('title', 'N/A')}, 页数={metadata.get('pages_count', 0)}")

    # 创建论文记录
    paper = Paper(
        title=metadata.get("title") or file.filename.replace(".pdf", ""),
        authors=metadata.get("authors") or [],
        abstract=metadata.get("abstract"),
        year=metadata.get("year"),
        pages_count=metadata.get("pages_count") or 0,
        source="upload",
        file_path=str(file_path),
        full_text=metadata.get("full_text"),
    )
    db.add(paper)
    await db.flush()

    # 创建用户关联
    user_paper = UserPaper(
        user_id=user.id,
        paper_id=paper.id,
        tags=[],
        collection="default",
    )
    db.add(user_paper)
    await db.flush()

    # 重新查询以预加载 user_papers 关系（异步下不能延迟加载）
    refreshed_paper = await get_paper_detail(db, user, paper.id)
    logger.info(f"用户 {user.email} 上传论文入库: {paper.title[:50]}")
    return refreshed_paper


# ========== 工具函数 ==========


def paper_to_response(paper: Paper) -> PaperResponse:
    """
    将 Paper ORM 对象转为 PaperResponse
    合并 user_papers 中的用户关联信息
    """
    base = {
        "id": paper.id,
        "title": paper.title,
        "authors": paper.authors or [],
        "abstract": paper.abstract,
        "doi": paper.doi,
        "arxiv_id": paper.arxiv_id,
        "source": paper.source,
        "source_url": paper.source_url,
        "year": paper.year,
        "journal": paper.journal,
        "citation_count": paper.citation_count,
        "pages_count": paper.pages_count,
        "created_at": paper.created_at,
        "updated_at": paper.updated_at,
        # 默认用户关联字段
        "tags": [],
        "notes": None,
        "collection": "default",
        "added_at": None,
    }

    # 合并 user_papers 信息 (取第一条关联记录)
    if paper.user_papers:
        up = paper.user_papers[0]
        base["tags"] = up.tags or []
        base["notes"] = up.notes
        base["collection"] = up.collection
        base["added_at"] = up.added_at

    return PaperResponse(**base)


def paper_to_detail_response(paper: Paper) -> PaperDetailResponse:
    """
    将 Paper ORM 对象转为 PaperDetailResponse
    """
    base = paper_to_response(paper)
    return PaperDetailResponse(
        **base.model_dump(),
        full_text=paper.full_text,
        file_path=paper.file_path,
        chunks_count=0,
        has_summary=False,
    )
