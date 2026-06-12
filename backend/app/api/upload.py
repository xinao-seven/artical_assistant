"""
文件上传 API 路由
- POST /upload/pdf - 上传 PDF 论文
"""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.paper import UploadResponse
from app.services import paper_service

router = APIRouter(prefix="/upload", tags=["上传"])


@router.post("/pdf", response_model=UploadResponse, status_code=201)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF 论文文件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传 PDF 论文

    - 支持最大 50MB 的 PDF 文件 (由 config 配置)
    - 上传后自动解析文本和元数据
    - 自动入库并关联当前用户
    - 不会自动向量化 (需手动调用索引接口)

    返回:
    - paper_id: 入库后的论文 ID
    - title: 解析出的标题
    - authors: 解析出的作者列表
    - abstract: 解析出的摘要
    - file_path: 服务器存储路径
    - pages_count: 页数
    """
    paper = await paper_service.upload_and_parse_pdf(db, current_user, file)

    return UploadResponse(
        paper_id=paper.id,
        title=paper.title,
        authors=paper.authors or [],
        abstract=paper.abstract,
        file_path=paper.file_path or "",
        pages_count=paper.pages_count,
    )
