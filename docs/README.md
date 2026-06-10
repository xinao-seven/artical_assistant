# Research Paper Retrieval & Analysis Tool — 文档索引

全栈AI科研论文检索和分析工具。支持本地上传PDF和网络检索论文，AI自动生成摘要、翻译、对比分析，并提供引用关系图谱可视化。

## 技术栈概览

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + ECharts |
| 后端 | FastAPI + LangChain + LangGraph + Celery |
| AI | DeepSeek v4 + BGE-M3 Embedding + BGE-Reranker |
| 数据库 | PostgreSQL + pgvector + tsvector |
| 缓存/队列 | Redis (Celery broker + LLM缓存) |
| 部署 | Docker Compose |

## 文档导航

| 文档 | 内容 |
|------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 系统架构、技术决策、数据流、目录结构 |
| [EXECUTION_PLAN.md](./EXECUTION_PLAN.md) | 10步执行方案，每步的具体任务和验证标准 |
| [API_SPEC.md](./API_SPEC.md) | REST API 接口规范（端点、请求/响应、错误码） |
| [DB_SCHEMA.md](./DB_SCHEMA.md) | 数据库表设计、索引策略、迁移方案 |
| [RAG_DESIGN.md](./RAG_DESIGN.md) | RAG流水线设计、分块策略、Prompt模板、LangGraph工作流 |
| [FRONTEND_DESIGN.md](./FRONTEND_DESIGN.md) | 前端组件树、路由设计、状态管理、SSE流式渲染 |

## 快速开始

```bash
# 1. 克隆项目后启动所有服务
docker compose up -d

# 2. 初始化数据库
docker compose exec backend alembic upgrade head

# 3. 访问
# 前端: http://localhost:80
# API文档: http://localhost:8000/docs
```

## 项目状态

- [ ] 第1步: 项目脚手架与环境搭建
- [ ] 第2步: 用户认证系统
- [ ] 第3步: 论文数据模型与CRUD
- [ ] 第4步: 论文检索
- [ ] 第5步: RAG向量化与摘要生成
- [ ] 第6步: 引用关系图谱
- [ ] 第7步: 搜索历史
- [ ] 第8步: 论文翻译
- [ ] 第9步: 定时追踪
- [ ] 第10步: Docker完整部署与测试
