# 系统架构文档

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐             │
│  │  Nginx   │  │  FastAPI  │  │  Celery   │             │
│  │  (Vue    │──│  Backend  │  │  Worker   │             │
│  │  SPA)    │  │  :8000    │  │           │             │
│  │  :80     │  └─────┬─────┘  └─────┬─────┘             │
│  └──────────┘        │              │                   │
│                      │              │                   │
│          ┌───────────┼──────────────┼──────┐            │
│          │           │              │      │            │
│     ┌────▼────┐ ┌───▼────┐   ┌────▼────┐ │            │
│     │PostgreSQL│ │ Redis │   │ ArXiv   │ │            │
│     │+pgvector│ │ :6379 │   │ API     │ │            │
│     │  :5432  │ │        │   │(external)│ │            │
│     └─────────┘ └────────┘   └─────────┘ │            │
│                                           │            │
│     ┌─────────┐                           │            │
│     │Semantic │                           │            │
│     │Scholar  │ (external)                │            │
│     └─────────┘                           │            │
└─────────────────────────────────────────────────────────┘
```

## 2. 技术决策记录

### 2.1 为什么用 PostgreSQL + pgvector 而不是专用向量数据库？

- **一库多用**: 业务数据 + 向量数据 + 全文搜索，减少运维复杂度
- **pgvector**: 支持 HNSW 索引，千万级向量检索性能足够
- **tsvector**: PostgreSQL 原生全文搜索，实现 Hybrid Search 的关键词部分
- **事务**: 向量和元数据在同一事务中，保证一致性

### 2.2 为什么用 BGE-M3 而不是 DeepSeek Embedding？

- **免费**: 开源模型，无 API 调用费用
- **中英文**: BGE-M3 在多语言评测中表现优秀
- **本地部署**: 通过 sentence-transformers 本地加载，无网络依赖
- **向量维度**: 1024 维，平衡精度和存储

### 2.3 为什么用 Celery 而不是 FastAPI BackgroundTasks？

- **持久化**: 任务不丢失，重启后继续执行
- **重试机制**: 内置重试策略，适合 API 调用失败场景
- **定时任务**: Celery Beat 直接支持，不需要额外的调度器
- **监控**: Flower 提供任务监控面板
- **代价**: 多一个 Redis 和 Worker 容器

### 2.4 为什么用 LangGraph？

- **多步推理**: 深度分析需要"提取→摘要→搜索→对比"的 DAG 流程
- **状态管理**: 每一步的输出作为下一步的输入，LangGraph 天然支持
- **简历亮点**: LangGraph 是当前 AI 工程的热门技能

### 2.5 为什么用 SSE 而不是 WebSocket？

- **单向流**: AI 生成是服务端→客户端的单向数据流
- **简单**: SSE 基于 HTTP，不需要 ws 协议升级
- **重连**: EventSource API 原生支持自动重连
- **穿透**: HTTP 更容易穿透代理和防火墙

## 3. 请求流程

### 3.1 论文检索流程

```
用户输入关键词
    │
    ▼
┌──────────────────────────────────────┐
│         POST /api/v1/search          │
│         {query, filters}             │
└──────────┬───────────────────────────┘
           │
           ├──→ BGE-M3 Embedding ──→ pgvector cosine similarity (Top-20)
           │
           ├──→ to_tsvector @@ to_tsquery ──→ Full-text match (Top-20)
           │
           ├──→ ArXiv API ──→ External results (Top-20)
           │
           └──→ RRF (Reciprocal Rank Fusion) ──→ Merged Top-K
                                                      │
                                                      ▼
                                              返回统一结果列表
```

### 3.2 AI摘要生成流程

```
POST /api/v1/papers/{id}/summary
    │
    ▼
┌─────────────────────────────────────┐
│  检查 Redis 缓存                    │
│  └── 命中 → 直接返回 (SSE 流式)     │
│  └── 未命中 ↓                       │
├─────────────────────────────────────┤
│  从 pgvector 检索 Top-5 相关 chunk  │
├─────────────────────────────────────┤
│  BGE-Reranker 精排 → Top-3          │
├─────────────────────────────────────┤
│  构建 Prompt (system + context)      │
├─────────────────────────────────────┤
│  DeepSeek API (streaming=True)       │
├─────────────────────────────────────┤
│  FastAPI StreamingResponse (SSE)     │
│  └── data: {token} ... [DONE]       │
├─────────────────────────────────────┤
│  缓存结果到 Redis (24h TTL)         │
└──────────────┬──────────────────────┘
               ▼
   前端 useSSE composable 逐字渲染
```

### 3.3 LangGraph 深度分析流程

```
POST /api/v1/papers/{id}/analyze
    │
    ▼
┌──────────────────────────┐
│  Step 1: Extract         │
│  提取方法/贡献/数据集     │
│  → KeyInfo                │
├──────────────────────────┤
│  Step 2: Summarize       │
│  基于KeyInfo生成摘要     │
│  → StructuredSummary     │
├──────────────────────────┤
│  Step 3: Search          │
│  用KeyInfo关键词搜论文   │
│  → RelatedPapers         │
├──────────────────────────┤
│  Step 4: Compare         │
│  本文 vs RelatedPapers   │
│  → ComparisonReport      │
├──────────────────────────┤
│  Final: Compile          │
│  整合为分析报告           │
└──────────┬───────────────┘
           ▼
  SSE 流式输出完整报告
```

## 4. 目录结构

```
artical_assistant/
├── docker-compose.yml              # 5个服务编排
├── .env.example                    # 环境变量模板
├── docs/                           # 项目文档
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                    # 数据库迁移
│   ├── app/
│   │   ├── main.py                 # FastAPI入口, 生命周期
│   │   ├── config.py               # Pydantic Settings
│   │   ├── dependencies.py         # 依赖注入
│   │   ├── models/                 # SQLAlchemy ORM
│   │   ├── schemas/                # Pydantic 请求/响应
│   │   ├── api/                    # 路由层
│   │   ├── services/               # 业务逻辑层
│   │   ├── worker/                 # Celery
│   │   └── utils/                  # 工具函数
│   └── tests/
├── frontend/                       # Vue 3 + TS (现有)
│   ├── src/
│   │   ├── api/                    # axios 封装
│   │   ├── router/                 # 路由配置
│   │   ├── stores/                 # Pinia
│   │   ├── views/                  # 页面
│   │   ├── components/             # 组件
│   │   ├── composables/            # 组合式函数
│   │   └── utils/
│   └── ...
└── nginx/
    └── nginx.conf                  # 反代配置
```

## 5. 安全设计

| 层面 | 措施 |
|------|------|
| 认证 | JWT access(30min) + refresh(7d) token |
| 密码 | bcrypt 哈希存储 |
| 文件上传 | 类型校验（只允许PDF），大小限制(50MB)，病毒扫描(后续) |
| XSS | markdown-it 禁用HTML标签 |
| CORS | 开发环境 FastAPI CORSMiddleware，生产 Nginx 反代 |
| SQL注入 | SQLAlchemy ORM 参数化查询 |
| 限流 | slowapi — 登录接口5次/分钟，AI接口10次/分钟 |
| API密钥 | DeepSeek API Key 通过环境变量注入，不入库 |
