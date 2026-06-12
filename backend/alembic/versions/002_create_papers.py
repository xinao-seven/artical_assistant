"""create papers and user_papers tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 papers 和 user_papers 表，启用 pgvector 和 pg_trgm 扩展"""
    # 启用扩展 (如果尚未启用)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ========== papers 表 ==========
    op.create_table(
        "papers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column(
            "authors",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("doi", sa.String(255), unique=True, nullable=True),
        sa.Column("arxiv_id", sa.String(100), unique=True, nullable=True),
        sa.Column(
            "source",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'manual'"),
        ),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("journal", sa.String(500), nullable=True),
        sa.Column(
            "citation_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("pages_count", sa.Integer(), nullable=True),
        # BGE-M3 1024维向量 (第5步填充)
        sa.Column("embedding", Vector(1024), nullable=True),
        # 全文搜索 tsvector
        sa.Column("full_text_tsv", postgresql.TSVECTOR(), nullable=True),
        # PDF 解析后的完整文本
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 论文表索引
    op.create_index("idx_papers_year", "papers", ["year"], unique=False)
    op.create_index("idx_papers_source", "papers", ["source"], unique=False)
    op.create_index("idx_papers_arxiv_id", "papers", ["arxiv_id"], unique=False)
    op.create_index("idx_papers_doi", "papers", ["doi"], unique=False)
    # 标题模糊搜索 (trigram)
    op.create_index(
        "idx_papers_title_trgm",
        "papers",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )

    # ========== user_papers 表 ==========
    op.create_table(
        "user_papers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "collection",
            sa.String(100),
            nullable=False,
            server_default=sa.text("'default'"),
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),
    )

    # 用户论文关联表索引
    op.create_index("idx_user_papers_user", "user_papers", ["user_id"], unique=False)
    op.create_index("idx_user_papers_paper", "user_papers", ["paper_id"], unique=False)
    op.create_index(
        "idx_user_papers_collection", "user_papers", ["user_id", "collection"], unique=False
    )
    op.create_index(
        "idx_user_papers_tags",
        "user_papers",
        ["tags"],
        unique=False,
        postgresql_using="gin",
    )

    # ========== 全文搜索自动更新触发器 ==========
    op.execute("""
        CREATE OR REPLACE FUNCTION papers_tsvector_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.full_text_tsv :=
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.abstract, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.full_text, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER tsvector_update BEFORE INSERT OR UPDATE ON papers
            FOR EACH ROW EXECUTE FUNCTION papers_tsvector_trigger();
    """)


def downgrade() -> None:
    """回滚迁移"""
    op.execute("DROP TRIGGER IF EXISTS tsvector_update ON papers")
    op.execute("DROP FUNCTION IF EXISTS papers_tsvector_trigger()")

    op.drop_table("user_papers")
    op.drop_table("papers")
