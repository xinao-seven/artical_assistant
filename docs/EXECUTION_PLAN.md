# 执行方案

> 本文档是项目实施的唯一执行指南。每一步包含：目标、创建/修改的文件清单、具体任务、验证标准。

---

## 第1步：项目脚手架与环境搭建

**目标**: 建立完整的开发环境，所有服务可通过 `docker compose up` 启动。

### 创建/修改文件
```
backend/
├── Dockerfile                    # 新建
├── requirements.txt              # 新建
├── alembic.ini                   # 新建
├── alembic/env.py                # 新建
├── app/
│   ├── main.py                   # 新建 - FastAPI入口
│   ├── config.py                 # 新建 - 配置管理
│   └── __init__.py               # 新建

frontend/
├── src/
│   ├── main.ts                   # 修改 - 注册Element Plus/Router/Pinia
│   ├── App.vue                   # 修改 - 简化为router-view
│   ├── router/index.ts           # 新建
│   └── stores/                   # 新建 - Pinia空store
├── package.json                  # 修改 - 添加依赖

docker-compose.yml                # 新建
.env.example                      # 新建
nginx/nginx.conf                  # 新建
```

### 任务清单
1. [ ] 创建 `backend/` 目录结构（`app/`, `models/`, `schemas/`, `api/`, `services/`, `utils/`, `worker/`, `tests/`）
2. [ ] 编写 `backend/requirements.txt`（fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pgvector, langchain, langgraph, sentence-transformers, celery, redis, sse-starlette, loguru, slowapi, pydantic-settings, alembic, python-multipart, pypdf, pdfplumber, httpx, python-jose, passlib, pytest）
3. [ ] 编写 `backend/Dockerfile`（python:3.11-slim, 安装依赖, 启动uvicorn）
4. [ ] 编写 `backend/app/config.py`（Pydantic BaseSettings, 读取环境变量）
5. [ ] 编写 `backend/app/main.py`（FastAPI app, CORS, lifespan, /api/v1 router挂载, /health端点）
6. [ ] 编写 `docker-compose.yml`（5服务: nginx, backend, db(pgvector), redis, worker）
7. [ ] 编写 `env.example`
8. [ ] 编写 `nginx/nginx.conf`（SPA静态文件 + /api反代）
9. [ ] 前端安装依赖: `npm install element-plus vue-router pinia axios markdown-it highlight.js katex vue-virtual-scroller echarts vue-echarts pdfjs-dist`
10. [ ] 前端 `main.ts` 注册 Element Plus + Router + Pinia
11. [ ] 前端创建空的 `router/index.ts` 和 `stores/`
12. [ ] 编写 `alembic.ini` 和 `alembic/env.py`

### 验证标准
- [ ] `docker compose up -d` 所有5个服务正常启动
- [ ] `docker compose logs backend` 无错误
- [ ] 浏览器访问 `http://localhost:8000/docs` 能看到 Swagger 文档
- [ ] 浏览器访问 `http://localhost:8000/health` 返回 `{"status": "ok"}`
- [ ] 前端 `npm run dev` 正常启动 Vite 开发服务器

---

## 第2步：用户认证系统

**目标**: 实现注册/登录/Token刷新，前端路由守卫。

### 创建/修改文件
```
backend/
├── app/
│   ├── models/user.py             # 新建
│   ├── schemas/auth.py            # 新建
│   ├── api/auth.py                # 新建
│   ├── api/router.py              # 新建/修改
│   ├── services/auth_service.py   # 新建
│   ├── dependencies.py            # 新建
│   └── main.py                    # 修改 - 注册路由

frontend/
├── src/
│   ├── api/index.ts               # 新建 - axios实例+拦截器
│   ├── api/auth.ts                # 新建
│   ├── stores/user.ts             # 新建/修改
│   ├── router/index.ts            # 修改 - 路由守卫
│   ├── views/LoginView.vue        # 新建
│   ├── views/RegisterView.vue     # 新建
│   ├── utils/storage.ts           # 新建
│   └── App.vue                    # 修改

alembic/versions/001_create_users.py  # 新建
```

### 任务清单
1. [ ] 编写 `models/user.py`（User 模型: id, email, password_hash, is_active, created_at）
2. [ ] 编写 `alembic/versions/001_create_users.py` 迁移
3. [ ] 编写 `schemas/auth.py`（RegisterRequest, LoginRequest, TokenResponse）
4. [ ] 编写 `services/auth_service.py`（注册: bcrypt hash, 登录: verify + 生成JWT, refresh_token逻辑）
5. [ ] 编写 `api/auth.py`（POST /register, POST /login, POST /refresh）
6. [ ] 编写 `dependencies.py`（get_db, get_current_user 依赖）
7. [ ] 编写前端 `utils/storage.ts`（token存取）
8. [ ] 编写前端 `api/index.ts`（axios实例, 请求拦截器加Token, 响应拦截器处理401+refresh）
9. [ ] 编写前端 `api/auth.ts`（login, register, refresh API调用）
10. [ ] 编写前端 `stores/user.ts`（用户状态, login/logout actions）
11. [ ] 编写前端 `router/index.ts`（路由配置 + beforeEach守卫）
12. [ ] 编写前端 `views/LoginView.vue`（Element Plus 表单）
13. [ ] 编写前端 `views/RegisterView.vue`（Element Plus 表单）

### 验证标准
- [ ] `POST /api/v1/auth/register` 创建用户成功
- [ ] `POST /api/v1/auth/login` 返回 access_token + refresh_token
- [ ] `POST /api/v1/auth/refresh` 用 refresh_token 换取新 token
- [ ] 前端注册→登录→自动跳转 Dashboard
- [ ] 未登录访问 /dashboard → 自动跳转 /login
- [ ] 登录后 axios 请求自动携带 Authorization header

---

## 第3步：论文数据模型与CRUD

**目标**: 论文表的完整CRUD，PDF上传与解析，个人论文库页面。

### 创建/修改文件
```
backend/
├── app/
│   ├── models/paper.py            # 新建
│   ├── schemas/paper.py           # 新建
│   ├── api/papers.py              # 新建
│   ├── api/upload.py             # 新建
│   ├── api/router.py             # 修改
│   ├── services/paper_service.py # 新建
│   └── utils/pdf_parser.py       # 新建

frontend/
├── src/
│   ├── api/papers.ts              # 新建
│   ├── views/LibraryView.vue      # 新建
│   ├── components/paper/
│   │   ├── PaperCard.vue          # 新建
│   │   ├── PaperList.vue          # 新建
│   │   └── PaperUpload.vue        # 新建
│   └── router/index.ts            # 修改

alembic/versions/002_create_papers.py  # 新建
```

### 任务清单
1. [ ] 编写 `models/paper.py`（Paper, UserPaper 模型）
2. [ ] 编写迁移 `002_create_papers.py`
3. [ ] 编写 `schemas/paper.py`（PaperCreate, PaperResponse, PaperList, PaginatedResponse）
4. [ ] 编写 `utils/pdf_parser.py`（pdfplumber提取文本/元数据）
5. [ ] 编写 `services/paper_service.py`（CRUD, 分页, 筛选, 关联用户）
6. [ ] 编写 `api/papers.py`（GET列表, GET详情, POST创建, DELETE删除）
7. [ ] 编写 `api/upload.py`（POST /upload/pdf → 保存文件, 解析, 入库）
8. [ ] 编写前端 `api/papers.ts`（paper API调用封装）
9. [ ] 编写 `components/paper/PaperCard.vue`（论文卡片: 标题/作者/年份/标签）
10. [ ] 编写 `components/paper/PaperList.vue`（虚拟列表 + 卡片网格）
11. [ ] 编写 `components/paper/PaperUpload.vue`（el-upload + 进度条）
12. [ ] 编写 `views/LibraryView.vue`（我的论文库: 搜索+筛选+列表+分页）

### 验证标准
- [ ] `POST /api/v1/papers` 创建论文成功
- [ ] `GET /api/v1/papers` 分页返回论文列表
- [ ] `POST /api/v1/upload/pdf` 上传PDF → 入库 → 返回论文信息
- [ ] 前端 LibraryView 展示论文列表（空状态/有数据/加载中）
- [ ] 论文上传弹窗 → 选择文件 → 显示进度 → 上传成功刷新列表

---

## 第4步：论文检索

**目标**: 实现 Hybrid Search（语义+关键词+外部API），前端搜索页面。

### 创建/修改文件
```
backend/
├── app/
│   ├── api/search.py              # 新建
│   ├── api/router.py             # 修改
│   ├── services/search_service.py # 新建
│   └── schemas/search.py          # 新建

frontend/
├── src/
│   ├── api/search.ts              # 新建
│   ├── views/SearchView.vue       # 新建
│   ├── components/search/
│   │   ├── SearchBar.vue          # 新建
│   │   └── SearchFilters.vue      # 新建
│   └── router/index.ts            # 修改
```

### 任务清单
1. [ ] 编写 `schemas/search.py`（SearchRequest: query, filters, page; SearchResponse）
2. [ ] 编写 `services/search_service.py`
   - pgvector 语义搜索（query embedding → cosine similarity）
   - tsvector 关键词搜索（to_tsquery）
   - ArXiv API 集成（httpx 异步调用）
   - Semantic Scholar API 集成
   - RRF 融合排序
3. [ ] 编写 `api/search.py`（POST /api/v1/search）
4. [ ] 编写前端 `api/search.ts`
5. [ ] 编写 `components/search/SearchBar.vue`（el-input + el-autocomplete + 搜索按钮）
6. [ ] 编写 `components/search/SearchFilters.vue`（年份/领域/来源 筛选器）
7. [ ] 编写 `views/SearchView.vue`（SearchBar + Filters + 虚拟结果列表 + 分页）

### 验证标准
- [ ] 输入关键词 → 返回混合搜索结果（含内部论文 + ArXiv论文）
- [ ] 筛选条件生效（年份范围、领域、来源）
- [ ] 前端搜索结果列表正确渲染（带loading态）
- [ ] 空搜索结果显示"未找到相关论文"
- [ ] 搜索防抖（输入停止300ms后才发请求）

---

## 第5步：RAG向量化与摘要生成（核心步骤）

**目标**: 实现完整的RAG流水线，SSE流式AI摘要，论文详情页。

### 创建/修改文件
```
backend/
├── app/
│   ├── models/paper.py            # 修改 - 加embedding字段
│   ├── services/rag_service.py    # 新建
│   ├── utils/text_splitter.py     # 新建
│   ├── utils/sse.py               # 新建
│   ├── api/papers.py              # 修改 - 加summary端点
│   └── api/router.py             # 修改
├── app/config.py                   # 修改 - 加模型配置

frontend/
├── src/
│   ├── api/papers.ts              # 修改 - 加summary/analyze
│   ├── composables/
│   │   ├── useSSE.ts              # 新建
│   │   └── useMarkdown.ts         # 新建
│   ├── components/ai/
│   │   ├── SummaryStream.vue      # 新建
│   │   └── MarkdownViewer.vue     # 新建
│   ├── views/PaperDetailView.vue  # 新建
│   └── router/index.ts            # 修改

alembic/versions/003_add_vectors.py  # 新建
```

### 任务清单
1. [ ] 编写迁移 `003_add_vectors.py`（papers.embedding + paper_chunks表 + HNSW索引）
2. [ ] 编写 `utils/text_splitter.py`（RecursiveCharacterTextSplitter + 论文特定分隔符）
3. [ ] 编写 `utils/sse.py`（SSE事件格式化工具: event/data/id/retry）
4. [ ] 编写 `services/rag_service.py`
   - `index_paper()`: PDF文本→分块→BGE-M3 embedding→存储到paper_chunks
   - `generate_summary_stream()`: 检索Top-5→Reranker精排→构建Prompt→DeepSeek streaming→yield SSE
   - `generate_analysis()`: LangGraph工作流（提取→摘要→搜索→对比）
   - `_cache_key()` / `_get_cached()` / `_set_cache()`: Redis缓存
5. [ ] 编写 `api/papers.py` 新增端点:
   - `POST /api/v1/papers/{id}/index` — 向量化论文
   - `GET /api/v1/papers/{id}/summary` — SSE流式摘要
   - `GET /api/v1/papers/{id}/analyze` — SSE流式深度分析
6. [ ] 编写前端 `composables/useSSE.ts`
   - fetch + ReadableStream + SSE解析
   - onMessage / onError / onDone 回调
   - 自动重连（retry字段）
   - abort控制
7. [ ] 编写前端 `composables/useMarkdown.ts`（markdown-it + highlight.js + katex初始化）
8. [ ] 编写 `components/ai/SummaryStream.vue`（流式文本动画渲染）
9. [ ] 编写 `components/ai/MarkdownViewer.vue`（markdown渲染 + 数学公式 + 代码块复制）
10. [ ] 编写 `views/PaperDetailView.vue`
    - 论文元信息展示（标题/作者/摘要/年份/期刊/DOI）
    - PDF内嵌预览（pdfjs-dist）
    - 点击"AI摘要"→ SummaryStream 组件显示
    - 点击"深度分析"→ 多步分析流式展示
    - 操作按钮: 添加到库、翻译、查看引用

### 验证标准
- [ ] 上传PDF → 索引 → paper_chunks表有数据 + embedding不为空
- [ ] 点击"AI摘要" → 逐字流式输出摘要内容
- [ ] Markdown格式正确渲染（标题/列表/加粗/代码块）
- [ ] 数学公式（LaTeX）正确渲染
- [ ] 摘要生成完成后缓存 → 再次请求直接返回缓存
- [ ] 深度分析分步展示（提取→摘要→搜索→对比各阶段可见）
- [ ] SSE连接中断 → 自动重连
- [ ] 论文详情页显示完整元信息

---

## 第6步：引用关系图谱

**目标**: 获取论文引用关系，ECharts可视化。

### 创建/修改文件
```
backend/
├── app/
│   ├── models/citation.py         # 新建
│   ├── api/citations.py           # 新建
│   ├── services/citation_service.py # 新建
│   └── api/router.py              # 修改

frontend/
├── src/
│   ├── api/citations.ts           # 新建
│   ├── views/CitationGraphView.vue # 新建
│   └── router/index.ts            # 修改

alembic/versions/004_create_citations.py  # 新建
```

### 任务清单
1. [ ] 编写迁移 `004_create_citations.py`（citation_relations表）
2. [ ] 编写 `models/citation.py`（CitationRelation模型）
3. [ ] 编写 `services/citation_service.py`
   - Semantic Scholar API获取引用/被引
   - 存储引用关系到数据库
   - 构建图谱数据结构（nodes + edges）
   - BFS多级展开
4. [ ] 编写 `api/citations.py`
   - `GET /api/v1/papers/{id}/citations` — 获取引用图谱数据
   - `POST /api/v1/papers/{id}/citations/expand` — 展开更多节点
5. [ ] 编写前端 `api/citations.ts`
6. [ ] 编写 `views/CitationGraphView.vue`
   - ECharts 力导向图（节点:论文标题, 大小=引用数, 颜色=年份热力）
   - 交互: 拖拽、缩放、悬停显示详情、点击展开
   - 图例: 年份色带、引用方向箭头

### 验证标准
- [ ] 点击论文的"查看引用" → 跳转图谱页面
- [ ] 力导向图正确渲染节点和边
- [ ] 拖拽、缩放交互正常
- [ ] 悬停节点显示论文标题/作者/年份 tooltip
- [ ] 点击节点展开更多引用关系
- [ ] 节点颜色按年份渐变

---

## 第7步：搜索历史

**目标**: 记录搜索历史，Dashboard展示。

### 创建/修改文件
```
backend/
├── app/
│   ├── models/search_history.py   # 新建
│   ├── api/search.py              # 修改 - 加历史端点
│   ├── services/search_service.py # 修改

frontend/
├── src/
│   ├── views/DashboardView.vue    # 修改 - 加历史模块
│   └── components/DashboardView.vue相关

alembic/versions/005_create_search_history.py  # 新建
```

### 任务清单
1. [ ] 编写迁移 `005_create_search_history.py`（search_history表）
2. [ ] 编写 `models/search_history.py`
3. [ ] 修改 `services/search_service.py`（每次搜索记录到search_history）
4. [ ] 修改 `api/search.py`（GET /api/v1/search/history — 获取历史）
5. [ ] 修改前端 `views/DashboardView.vue`（搜索历史列表 + 点击重新搜索 + 删除历史）

### 验证标准
- [ ] 每次搜索自动记录
- [ ] Dashboard展示最近搜索历史（按时间倒序）
- [ ] 点击历史项 → 重新执行搜索
- [ ] 删除单条/清空历史

---

## 第8步：论文翻译

**目标**: Celery异步翻译，双语对照展示。

### 创建/修改文件
```
backend/
├── app/
│   ├── models/paper.py            # 修改 - 加translations关系
│   ├── api/translate.py           # 新建
│   ├── services/translate_service.py # 新建
│   ├── worker/tasks.py            # 新建/修改
│   ├── worker/celery_app.py       # 新建

frontend/
├── src/
│   ├── api/translate.ts           # 新建
│   ├── components/ai/TranslatePanel.vue # 新建
│   └── views/PaperDetailView.vue  # 修改 - 加翻译面板

alembic/versions/006_create_translations.py  # 新建
```

### 任务清单
1. [ ] 编写迁移 `006_create_translations.py`（translations表）
2. [ ] 编写 `worker/celery_app.py`（Celery实例, Redis broker, 任务队列配置）
3. [ ] 编写 `services/translate_service.py`（LangChain翻译链 + DeepSeek）
4. [ ] 编写 `worker/tasks.py`（translate_paper任务: 分块→翻译→聚合→更新状态）
5. [ ] 编写 `api/translate.py`
   - `POST /api/v1/papers/{id}/translate` → 返回task_id
   - `GET /api/v1/translate/{task_id}/status` → 轮询状态
   - `GET /api/v1/papers/{id}/translation` → 获取翻译结果
6. [ ] 编写前端 `api/translate.ts`
7. [ ] 编写 `components/ai/TranslatePanel.vue`（双语对照: 左侧原文段落, 右侧译文, 段落高亮同步）
8. [ ] 修改 `views/PaperDetailView.vue` 集成翻译面板

### 验证标准
- [ ] 点击"翻译"→ 返回task_id → 轮询显示进度
- [ ] 翻译完成后展示双语对照
- [ ] 左侧段落和右侧译文同步滚动高亮
- [ ] Celery worker日志显示任务执行
- [ ] 翻译失败 → 显示错误信息 + 重试按钮

---

## 第9步：定时追踪

**目标**: Celery Beat定时搜索新论文，站内通知。

### 创建/修改文件
```
backend/
├── app/
│   ├── models/tracking.py         # 新建
│   ├── api/tracking.py            # 新建
│   ├── services/tracking_service.py # 新建
│   ├── worker/tasks.py            # 修改 - 加追踪任务
│   ├── worker/celery_app.py       # 修改 - 加beat_schedule配置

frontend/
├── src/
│   ├── api/tracking.ts            # 新建
│   ├── views/SettingsView.vue     # 新建

alembic/versions/007_create_tracking.py  # 新建
```

### 任务清单
1. [ ] 编写迁移 `007_create_tracking.py`（tracking_queries表）
2. [ ] 编写 `models/tracking.py`（TrackingQuery模型）
3. [ ] 编写 `services/tracking_service.py`（创建/更新/删除追踪, 执行追踪搜索, 通知生成）
4. [ ] 修改 `worker/celery_app.py`（配置Celery Beat scheduler）
5. [ ] 修改 `worker/tasks.py`（添加 run_tracking_queries 定时任务）
6. [ ] 编写 `api/tracking.py`
   - `GET /api/v1/tracking` — 获取用户的追踪列表
   - `POST /api/v1/tracking` — 创建追踪
   - `PUT /api/v1/tracking/{id}` — 更新追踪
   - `DELETE /api/v1/tracking/{id}` — 删除追踪
7. [ ] 编写前端 `api/tracking.ts`
8. [ ] 编写 `views/SettingsView.vue`
   - 追踪列表展示
   - 添加追踪（关键词+领域+频率）
   - 启用/禁用开关
   - 最近发现的新论文预览

### 验证标准
- [ ] 创建追踪 → Celery Beat按频率执行
- [ ] 追踪任务执行后搜索到新论文
- [ ] 前端Settings页面展示追踪状态和结果
- [ ] 启用/禁用切换生效

---

## 第10步：Docker部署与端到端测试

**目标**: 完整的Docker Compose部署，验证所有功能。

### 任务清单
1. [ ] 完善 `docker-compose.yml`（环境变量, 卷挂载, 健康检查, depends_on）
2. [ ] 完善 `nginx/nginx.conf`（SPA路由fallback, gzip, 静态资源缓存）
3. [ ] 编写 `.env.example` 完整版
4. [ ] 端到端功能测试
5. [ ] 编写 `README.md`（项目介绍, 技术栈, 快速开始, 截图）

### 验证标准
- [ ] `docker compose up -d` 一键启动所有服务
- [ ] 注册→登录→搜索论文→上传PDF→AI摘要→查看引用的完整流程
- [ ] SSE流式输出正常
- [ ] Celery异步翻译正常
- [ ] 所有容器健康检查通过
