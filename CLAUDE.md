# Research Paper Assistant — 项目手册

## 项目概述
全栈AI科研论文检索和分析工具。支持本地上传PDF和网络检索论文，AI自动生成摘要、翻译、对比分析，引用关系图谱可视化。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + ECharts |
| 后端 | FastAPI (Python 3.11) + LangChain + LangGraph |
| AI | DeepSeek v4 (flash/pro) + BGE-M3 Embedding + BGE-Reranker |
| 数据库 | PostgreSQL 16 + pgvector (向量) + tsvector (全文搜索) |
| 缓存/队列 | Redis (Celery broker + LLM 缓存) |
| 异步任务 | Celery + Celery Beat |
| 部署 | Docker Compose (5容器: nginx/backend/db/redis/worker) |

## 项目结构

```
artical_assistant/
├── docker-compose.yml       # 5 服务编排
├── .env                     # DeepSeek API Key 等配置
├── CLAUDE.md                # 本文件
├── docs/                    # 项目文档 (7份)
├── tech-notes/              # 核心技术实现笔记 (逐步积累)
├── backend/                 # FastAPI 后端
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/             # 数据库迁移
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # Pydantic Settings
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── api/             # 路由层
│   │   ├── services/        # 业务逻辑
│   │   ├── worker/          # Celery
│   │   └── utils/           # 工具
│   └── tests/
├── src/                     # Vue 3 前端 (根目录)
│   ├── main.ts              # 入口 (Element Plus/Router/Pinia)
│   ├── App.vue              # 根组件
│   ├── router/index.ts      # 9条路由 + 守卫
│   ├── stores/              # Pinia (user.ts)
│   ├── api/index.ts         # Axios + Token 刷新
│   ├── utils/storage.ts     # localStorage 封装
│   ├── views/               # 9个页面
│   ├── components/layout/   # AppLayout/AppHeader/AppSidebar
│   └── composables/         # useSSE/useMarkdown (待实现)
├── nginx/nginx.conf
├── vite.config.ts
└── package.json
```

## 数据库 (9张表)

| 表 | 状态 | 说明 |
|-----|------|------|
| users | ✅ 已实现(第2步) | 用户 |
| refresh_tokens | ✅ 已实现(第2步) | JWT刷新令牌 |
| papers | ✅ 已实现(第3步) | 论文主表 |
| user_papers | ✅ 已实现(第3步) | 用户论文关联 |
| search_history | 待实现(第7步) | 搜索记录 |
| citation_relations | 待实现(第6步) | 引用关系 |
| paper_chunks | 待实现(第5步) | 论文分块+向量 |
| translations | 待实现(第8步) | 翻译记录 |
| tracking_queries | 待实现(第9步) | 定时追踪 |

## 当前进度: 第3步完成

已实现：
- [x] 后端目录结构、FastAPI 入口、配置管理
- [x] Docker Compose 5容器 (nginx/backend/db/redis/worker)
- [x] Alembic 数据库迁移框架
- [x] 前端 Element Plus + Router + Pinia + Axios
- [x] 前端布局组件 (AppLayout/AppHeader/AppSidebar)
- [x] 路由守卫 (认证检查)
- [x] Axios Token自动刷新
- [x] Celery 占位文件 (worker不报错)
- [x] `docker compose up -d` 全部正常启动
- [x] 数据库迁移成功
- [x] JWT 双Token 用户认证 (注册/登录/登出/刷新)
- [x] 论文 CRUD (手动录入/列表/详情/更新/删除)
- [x] PDF 上传与自动解析入库（真实上传进度）

下一步：第4步 - 论文检索 (ArXiv/Semantic Scholar/Hybrid Search)

## 实施顺序

1. ✅ 项目脚手架
2. ✅ 用户认证 (JWT + 登录/注册) → 详见 `tech-notes/双Token刷新机制.md`
3. ✅ 论文CRUD (PDF上传/解析/论文库)
4. ⬜ 论文检索 (ArXiv/Semantic Scholar/Hybrid Search)
5. ⬜ RAG摘要 (Embedding/pgvector/LangChain/SSE流式)
6. ⬜ 引用图谱 (ECharts力导向图)
7. ⬜ 搜索历史
8. ⬜ 论文翻译 (Celery异步)
9. ⬜ 定时追踪 (Celery Beat)
10. ⬜ Docker部署完善

## 关键命令

```bash
# Docker
docker compose up -d          # 启动所有服务
docker compose down           # 停止并清理
docker compose ps             # 查看状态
docker compose logs -f        # 跟踪日志
docker compose exec backend alembic upgrade head  # 数据库迁移

# 前端
npm run dev                   # Vite 开发服务器
npx vite build                # 生产构建
npx vue-tsc -b                # TypeScript类型检查
```

## API 端点 (基础路径 /api/v1)

- `GET /health` - 健康检查
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/refresh` - 刷新Token
- `GET /papers` - 论文列表 (分页/筛选)
- `GET /papers/{id}` - 论文详情
- `POST /papers` - 手动创建论文
- `PATCH /papers/{id}` - 更新论文
- `DELETE /papers/{id}` - 删除论文
- `POST /upload/pdf` - 上传PDF论文
- 后续逐步增加

## 开发注意事项

- 前端在根目录，后端在 `backend/`
- 注释全中文
- 所有 Python 文件需能被 `from app` 导入
- Alembic env.py 需要 `sys.path.insert` 才能找到 app 模块
- Nginx 配置了 SSE 缓冲关闭 (proxy_buffering off)
- pgvector HNSW 索引在建表后创建
- 前端 api/index.ts 已封装 Token 自动刷新逻辑

## 技术笔记 (`tech-notes/`)

`tech-notes/` 目录存放项目核心技术实现的详细文档。每个关键技术问题独立成篇，在实现对应功能时逐步积累。

| 文档 | 覆盖内容 |
|------|----------|
| `双Token刷新机制.md` | Axios 拦截器、并发刷新锁、Promise 队列 |
| *(待添加)* | 后续步骤的技术要点... |

> 新增技术笔记后请同步更新此表。
