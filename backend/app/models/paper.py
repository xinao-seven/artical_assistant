"""
论文相关 ORM 模型
- Paper: 论文主表
- UserPaper: 用户论文关联表
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class Paper(Base):
    """论文主表"""
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    authors: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list, server_default="{}"
    )
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="manual", server_default="'manual'"
    )
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    journal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pages_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # BGE-M3 1024维向量 (第5步填充)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    # PDF 解析后的完整文本
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联
    user_papers = relationship(
        "UserPaper", back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Paper {self.title[:50]}>"


class UserPaper(Base):
    """用户论文关联表"""
    __tablename__ = "user_papers"
    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list, server_default="{}"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    collection: Mapped[str] = mapped_column(
        String(100), nullable=False, default="default", server_default="'default'"
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 反向关联
    paper = relationship("Paper", back_populates="user_papers")
    user = relationship("User", back_populates="user_papers")

    def __repr__(self) -> str:
        return f"<UserPaper user={self.user_id} paper={self.paper_id}>"
