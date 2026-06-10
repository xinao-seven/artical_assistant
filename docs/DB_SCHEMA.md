# 数据库设计

## 1. 完整表结构

### 1.1 users — 用户表
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    avatar VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
```

### 1.2 refresh_tokens — JWT刷新令牌
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
```

### 1.3 papers — 论文主表
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- 用于模糊搜索

CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(1000) NOT NULL,
    authors TEXT[] NOT NULL DEFAULT '{}',
    abstract TEXT,
    doi VARCHAR(255) UNIQUE,
    arxiv_id VARCHAR(100) UNIQUE,
    source VARCHAR(50) NOT NULL DEFAULT 'manual',  -- 'upload', 'arxiv', 'semantic_scholar', 'manual'
    source_url VARCHAR(1000),
    file_path VARCHAR(1000),                        -- 上传PDF本地路径
    year INTEGER,
    journal VARCHAR(500),
    citation_count INTEGER DEFAULT 0,
    pages_count INTEGER,
    embedding vector(1024),                         -- BGE-M3 1024维
    full_text_tsv tsvector,                         -- 全文搜索
    full_text TEXT,                                 -- PDF解析的完整文本
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW 向量索引 (构建慢，查得快)
CREATE INDEX idx_papers_embedding ON papers USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- 全文搜索 GIN 索引
CREATE INDEX idx_papers_tsv ON papers USING gin(full_text_tsv);

-- 标题模糊搜索
CREATE INDEX idx_papers_title_trgm ON papers USING gin(title gin_trgm_ops);

-- 常用查询索引
CREATE INDEX idx_papers_year ON papers(year DESC);
CREATE INDEX idx_papers_source ON papers(source);
CREATE INDEX idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX idx_papers_doi ON papers(doi);
```

### 1.4 user_papers — 用户论文关联
```sql
CREATE TABLE user_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    tags TEXT[] DEFAULT '{}',
    notes TEXT,
    collection VARCHAR(100) DEFAULT 'default',  -- 分组/收藏夹
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, paper_id)
);
CREATE INDEX idx_user_papers_user ON user_papers(user_id);
CREATE INDEX idx_user_papers_paper ON user_papers(paper_id);
CREATE INDEX idx_user_papers_collection ON user_papers(user_id, collection);
CREATE INDEX idx_user_papers_tags ON user_papers USING gin(tags);
```

### 1.5 paper_chunks — 论文分块
```sql
CREATE TABLE paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_tsv tsvector,
    embedding vector(1024),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW 向量索引
CREATE INDEX idx_chunks_embedding ON paper_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

CREATE INDEX idx_chunks_paper ON paper_chunks(paper_id);
CREATE INDEX idx_chunks_tsv ON paper_chunks USING gin(content_tsv);

-- 全文搜索自动更新触发器
CREATE TRIGGER tsvector_update BEFORE INSERT OR UPDATE ON paper_chunks
    FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(content_tsv, 'pg_catalog.english', content);
```

### 1.6 search_history — 搜索记录
```sql
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query VARCHAR(1000) NOT NULL,
    filters JSONB DEFAULT '{}',
    result_count INTEGER DEFAULT 0,
    search_id UUID,                               -- 关联搜索结果
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_search_history_user ON search_history(user_id, created_at DESC);
```

### 1.7 citation_relations — 引用关系
```sql
CREATE TABLE citation_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    to_paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    relation_type VARCHAR(20) NOT NULL CHECK (relation_type IN ('cites', 'cited_by')),
    is_influential BOOLEAN DEFAULT FALSE,         -- Semantic Scholar 标记
    context TEXT,                                 -- 引用上下文
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(from_paper_id, to_paper_id, relation_type)
);
CREATE INDEX idx_citation_from ON citation_relations(from_paper_id);
CREATE INDEX idx_citation_to ON citation_relations(to_paper_id);
```

### 1.8 translations — 翻译记录
```sql
CREATE TABLE translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL UNIQUE,                 -- Celery task_id
    target_lang VARCHAR(10) NOT NULL DEFAULT 'zh',
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    paragraphs JSONB,                             -- [{original, translated, index}]
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_translations_paper ON translations(paper_id);
CREATE INDEX idx_translations_task ON translations(task_id);
```

### 1.9 tracking_queries — 定时追踪
```sql
CREATE TABLE tracking_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    category VARCHAR(100),
    frequency VARCHAR(20) NOT NULL DEFAULT 'weekly'
        CHECK (frequency IN ('daily', 'weekly')),
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    last_result_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tracking_user ON tracking_queries(user_id);
CREATE INDEX idx_tracking_active ON tracking_queries(is_active, frequency);
```

## 2. 索引策略总结

| 表 | 索引类型 | 用途 |
|----|---------|------|
| papers.embedding | HNSW (vector_cosine_ops) | 语义相似度搜索 |
| paper_chunks.embedding | HNSW (vector_cosine_ops) | RAG分块检索 |
| papers.full_text_tsv | GIN (tsvector) | 全文关键词搜索 |
| paper_chunks.content_tsv | GIN (tsvector) | 分块全文搜索 |
| papers.title | GIN (trigram) | 标题模糊匹配 |
| user_papers.tags | GIN (array) | 标签搜索 |

## 3. Hybrid Search 查询示例

```sql
-- 语义搜索 (cosine similarity)
SELECT id, title, 1 - (embedding <=> $query_embedding) AS similarity
FROM papers
WHERE embedding IS NOT NULL
ORDER BY embedding <=> $query_embedding
LIMIT 20;

-- 关键词搜索 (ts_rank)
SELECT id, title, ts_rank(full_text_tsv, to_tsquery('english', $query)) AS rank
FROM papers
WHERE full_text_tsv @@ to_tsquery('english', $query)
ORDER BY rank DESC
LIMIT 20;

-- RRF 融合 (应用层实现)
-- score = Σ 1/(k + rank_i)  其中 k=60 (经典值)
```

## 4. 迁移版本

| 版本 | 文件名 | 内容 |
|------|--------|------|
| 001 | create_users | users + refresh_tokens |
| 002 | create_papers | papers + user_papers |
| 003 | add_vectors | embedding字段 + paper_chunks + HNSW索引 |
| 004 | create_citations | citation_relations |
| 005 | create_search_history | search_history |
| 006 | create_translations | translations |
| 007 | create_tracking | tracking_queries |
