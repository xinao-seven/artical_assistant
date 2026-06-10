# API 接口规范

- 基础路径: `/api/v1`
- 认证方式: `Authorization: Bearer <access_token>`
- 内容类型: `application/json`
- 流式接口: `text/event-stream` (SSE)

---

## 1. 认证模块 `/api/v1/auth`

### POST /register
```
Request:  { email: str, password: str, username?: str }
Response: { id: uuid, email: str, created_at: datetime } | 201
Errors:   409 Email已注册, 422 验证失败
```

### POST /login
```
Request:  { email: str, password: str }
Response: { access_token: str, refresh_token: str, token_type: "bearer" } | 200
Errors:   401 邮箱或密码错误
```

### POST /refresh
```
Request:  { refresh_token: str }
Response: { access_token: str, refresh_token: str } | 200
Errors:   401 Token无效或过期
```

### GET /me
```
Headers:  Authorization: Bearer <token>
Response: { id, email, username, avatar, is_active, created_at } | 200
Errors:   401 未认证
```

---

## 2. 论文模块 `/api/v1/papers`

### GET / — 论文列表
```
Query:    page=1, size=20, sort=created_at, order=desc, collection?, tag?
Response: { items: [PaperResponse], total: int, page: int, size: int } | 200
```

### GET /{id} — 论文详情
```
Response: { ...PaperResponse, chunks_count: int, has_summary: bool } | 200
Errors:   404 论文不存在
```

### POST / — 创建论文（手动录入）
```
Request:  { title, authors[], abstract?, doi?, arxiv_id?, year?, journal? }
Response: PaperResponse | 201
```

### DELETE /{id} — 删除论文
```
Response: { detail: "已删除" } | 200
Errors:   404 论文不存在, 403 无权操作
```

### POST /{id}/index — 向量化论文
```
触发:   PDF文本→分块→embedding→存储到paper_chunks
Response: { chunks_count: int, status: "indexed" } | 200
Errors: 404 论文不存在, 400 无可索引文本
```

### GET /{id}/summary — SSE流式摘要
```
Headers: Accept: text/event-stream
Events:  data: {"token": "..."}  → 逐token输出
         data: [DONE]            → 生成完成
         event: error, data: {"message": "..."}
```

### GET /{id}/analyze — SSE流式深度分析 (LangGraph)
```
Events:  event: step, data: {"step": "extracting", "message": "正在提取关键信息..."}
         data: {"token": "..."}
         event: step, data: {"step": "summarizing", "message": "正在生成结构化摘要..."}
         data: {"token": "..."}
         event: step, data: {"step": "searching", "message": "正在搜索相关论文..."}
         data: {"token": "..."}
         event: step, data: {"step": "comparing", "message": "正在对比分析..."}
         data: {"token": "..."}
         data: [DONE]
```

---

## 3. 上传模块 `/api/v1/upload`

### POST /pdf — 上传PDF
```
Request:  multipart/form-data { file: pdf }
Response: { paper_id, title, authors, abstract, file_path, pages_count } | 201
Errors:   400 文件类型不支持, 413 文件过大(>50MB)
Notes:    上传后自动解析文本和元数据，但不自动向量化
```

---

## 4. 搜索模块 `/api/v1/search`

### POST / — 搜索论文
```
Request: {
  query: str,                          // 搜索关键词
  filters?: {
    year_from?: int,
    year_to?: int,
    sources?: ["arxiv" | "semantic_scholar" | "local"],
    categories?: str[]                 // ArXiv分类
  },
  page?: int,                          // 默认1
  size?: int                           // 默认20
}
Response: {
  items: [{
    ...PaperResponse,
    source: "local" | "arxiv" | "semantic_scholar",
    relevance_score: float
  }],
  total: int,
  page: int,
  size: int,
  search_id: uuid                      // 用于记录搜索历史
} | 200
```

### GET /history — 搜索历史
```
Query:    page=1, size=20
Response: { items: [SearchHistoryResponse], total, page, size } | 200
```

### DELETE /history/{id} — 删除历史记录
```
Response: { detail: "已删除" } | 200
```

---

## 5. 引用模块 `/api/v1/papers/{id}/citations`

### GET / — 引用图谱数据
```
Query:    depth=1 (展开层数), limit=50 (节点上限)
Response: {
  nodes: [{ id, title, authors, year, citation_count, is_center }],
  edges: [{ source, target, relation: "cites" | "cited_by" }]
} | 200
```

### POST /expand — 展开更多节点
```
Request:  { paper_ids: [uuid], depth?: int }
Response: { nodes: [...], edges: [...] } | 200
```

---

## 6. 翻译模块 `/api/v1`

### POST /papers/{id}/translate — 发起翻译
```
Request:  { target_lang?: str }  // 默认 "zh"
Response: { task_id: uuid, status: "pending" } | 202
```

### GET /translate/{task_id}/status — 查询翻译进度
```
Response: {
  task_id: uuid,
  status: "pending" | "processing" | "completed" | "failed",
  progress: int,           // 0-100
  error?: str              // 失败时
} | 200
```

### GET /papers/{id}/translation — 获取翻译结果
```
Response: {
  paper_id: uuid,
  target_lang: str,
  paragraphs: [{
    original: str,
    translated: str,
    index: int
  }],
  completed_at: datetime
} | 200
Errors: 404 翻译不存在
```

---

## 7. 追踪模块 `/api/v1/tracking`

### GET / — 追踪列表
```
Response: { items: [TrackingResponse] } | 200
```

### POST / — 创建追踪
```
Request:  {
  keywords: str[],
  category?: str,
  frequency: "daily" | "weekly",
  is_active?: bool    // 默认true
}
Response: TrackingResponse | 201
```

### PUT /{id} — 更新追踪
```
Request:  { keywords?, category?, frequency?, is_active? }
Response: TrackingResponse | 200
```

### DELETE /{id} — 删除追踪
```
Response: { detail: "已删除" } | 200
```

---

## 通用错误格式

```json
{
  "detail": "错误描述",
  "code": "ERROR_CODE",
  "timestamp": "2026-06-10T12:00:00Z"
}
```

## HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 202 | 已接受（异步处理中） |
| 400 | 请求参数错误 |
| 401 | 未认证 / Token过期 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如邮箱已注册） |
| 413 | 文件过大 |
| 422 | 请求体验证失败 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |
