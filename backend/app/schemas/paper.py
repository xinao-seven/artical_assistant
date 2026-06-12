"""
论文相关 Pydantic 模型 (请求/响应)
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ========== 请求模型 ==========

class PaperCreate(BaseModel):
    """手动创建论文请求"""
    title: str = Field(..., min_length=1, max_length=1000, description="论文标题")
    authors: list[str] = Field(default_factory=list, description="作者列表")
    abstract: str | None = Field(None, description="摘要")
    doi: str | None = Field(None, max_length=255, description="DOI")
    arxiv_id: str | None = Field(None, max_length=100, description="arXiv ID")
    year: int | None = Field(None, ge=1900, le=2100, description="发表年份")
    journal: str | None = Field(None, max_length=500, description="期刊/会议名称")
    source_url: str | None = Field(None, max_length=1000, description="来源链接")
    # 用户关联
    tags: list[str] = Field(default_factory=list, description="用户标签")
    notes: str | None = Field(None, description="个人笔记")
    collection: str = Field(default="default", max_length=100, description="收藏分组")


class PaperUpdate(BaseModel):
    """更新论文请求（用户侧，仅更新关联信息）"""
    tags: list[str] | None = Field(None, description="更新标签")
    notes: str | None = Field(None, description="更新笔记")
    collection: str | None = Field(None, max_length=100, description="移动分组")


class PaperListParams(BaseModel):
    """论文列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort: str = Field(default="created_at", description="排序字段")
    order: str = Field(default="desc", description="排序方向 (asc/desc)")
    collection: str | None = Field(None, description="按分组筛选")
    tag: str | None = Field(None, description="按标签筛选")
    keyword: str | None = Field(None, description="标题/作者关键词搜索")


# ========== 响应模型 ==========

class PaperResponse(BaseModel):
    """论文响应"""
    id: uuid.UUID
    title: str
    authors: list[str]
    abstract: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    source: str
    source_url: str | None = None
    year: int | None = None
    journal: str | None = None
    citation_count: int = 0
    pages_count: int | None = None
    # 用户关联信息
    tags: list[str] = []
    notes: str | None = None
    collection: str = "default"
    added_at: datetime | None = None
    # 元数据
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaperDetailResponse(PaperResponse):
    """论文详情响应（含完整文本和分块统计）"""
    full_text: str | None = None
    file_path: str | None = None
    chunks_count: int = 0
    has_summary: bool = False


class PaginatedResponse(BaseModel):
    """分页响应包装"""
    items: list[PaperResponse]
    total: int
    page: int
    size: int


class PaperDeleteResponse(BaseModel):
    """删除响应"""
    detail: str = "已删除"


class UploadResponse(BaseModel):
    """PDF上传响应"""
    paper_id: uuid.UUID
    title: str
    authors: list[str]
    abstract: str | None = None
    file_path: str
    pages_count: int | None = None
