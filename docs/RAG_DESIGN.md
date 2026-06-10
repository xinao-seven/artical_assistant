# RAG 流水线设计

## 1. 整体流水线

```
PDF上传
  │
  ▼
pdfplumber 文本提取 ──→ 元数据提取 (标题/作者/DOI)
  │
  ▼
RecursiveCharacterTextSplitter 分块
  (chunk_size=1000, overlap=200)
  │
  ▼
BGE-M3 Embedding (sentence-transformers)
  │
  ▼
pgvector 存储 (paper_chunks表, HNSW索引)
  │
  ▼
用户触发 "AI摘要" ──→ 向量检索 Top-5
  │
  ▼
BGE-Reranker 精排 → Top-3
  │
  ▼
LangChain Prompt 构建
  │
  ▼
DeepSeek v4 (streaming=True)
  │
  ▼
SSE 流式输出 → 前端逐字渲染
  │
  ▼
Redis 缓存结果 (24h TTL)
```

## 2. 文本分块策略

### 2.1 论文特定分隔符

```python
PAPER_SEPARATORS = [
    "\n\n## ",           # Markdown 二级标题
    "\n\n### ",          # Markdown 三级标题
    "\n\nAbstract",
    "\n\nIntroduction",
    "\n\nMethod",
    "\n\nRelated Work",
    "\n\nExperiment",
    "\n\nConclusion",
    "\n\nReferences",
    "\n\n",              # 段落
    "\n",                # 句子
    " ",                 # 词
]
```

### 2.2 分块参数

```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,        # 每块约1000字符
    chunk_overlap=200,      # 重叠200字符（保持上下文连贯）
    separators=PAPER_SEPARATORS,
    length_function=len,
    is_separator_regex=False,
)
```

### 2.3 元数据保留

每个chunk保留: `{paper_id, chunk_index, section_title, page_number}`

## 3. Embedding 模型配置

```python
# BGE-M3 模型
model_name = "BAAI/bge-m3"
model_kwargs = {"device": "cpu"}     # Docker中无GPU; 本地可改"cuda"
encode_kwargs = {
    "normalize_embeddings": True,    # 归一化，用于cosine相似度
    "batch_size": 8,
}
# 输出维度: 1024
```

### 为什么选BGE-M3
- 多语言: 中英文混合检索效果好
- 维度合理: 1024维，存储和速度平衡好
- 指令感知: 支持 query/passage 双编码模式
- 免费: 无需API费用

## 4. LangChain Prompt 模板

### 4.1 摘要生成
```python
SUMMARY_SYSTEM_PROMPT = """你是一个专业的科研论文分析助手。
请根据提供的论文片段，生成一份结构化的论文摘要。
摘要应包含以下部分：
1. 研究背景与动机
2. 方法与技术
3. 主要贡献与创新点
4. 实验结果与结论

要求：
- 使用中文撰写
- 语言专业、准确、简洁
- 总字数控制在300-500字
- 使用Markdown格式输出"""

SUMMARY_USER_PROMPT = """请根据以下论文内容生成摘要：

**论文标题**: {title}
**作者**: {authors}
**年份**: {year}

**论文内容片段**:
{context}

请生成结构化摘要："""
```

### 4.2 翻译
```python
TRANSLATE_SYSTEM_PROMPT = """你是一个专业的学术论文翻译专家。
请将以下英文论文段落翻译成中文。
要求：
- 保持学术语言的严谨性和准确性
- 专业术语翻译恰当
- 保持原文的段落结构
- 长难句合理拆分，保证中文流畅性"""
```

### 4.3 LangGraph 分析步骤

```python
# Step 1: Extract
EXTRACT_PROMPT = """从以下论文中提取关键信息：
- 核心方法/算法
- 主要贡献
- 使用的数据集
- 对比的基线方法
以JSON格式输出。"""

# Step 2: Summarize
# 使用上面的 SUMMARY_PROMPT

# Step 3: Search Related
SEARCH_KEYWORDS_PROMPT = """基于以下论文的关键信息，
生成3-5个用于搜索相关论文的关键词（英文）。
直接输出关键词，每行一个。"""

# Step 4: Compare
COMPARE_PROMPT = """请对比分析以下两篇论文：
**论文A**: {paper_a_title}  ({paper_a_year})
{paper_a_keyinfo}

**论文B**: {paper_b_title} ({paper_b_year})
{paper_b_keyinfo}

从方法、贡献、实验设置等维度进行对比。"""
```

## 5. LangGraph 工作流

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AnalysisState(TypedDict):
    paper_id: str
    title: str
    authors: str
    full_text: str
    # Step outputs
    key_info: dict
    summary: str
    search_keywords: List[str]
    related_papers: List[dict]
    comparison: str
    # Stream control
    current_step: str

graph = StateGraph(AnalysisState)

# 定义节点
graph.add_node("extract", extract_key_info)      # → key_info
graph.add_node("summarize", generate_summary)     # → summary
graph.add_node("search", search_related)          # → search_keywords, related_papers
graph.add_node("compare", compare_papers)         # → comparison

# 定义边
graph.set_entry_point("extract")
graph.add_edge("extract", "summarize")
graph.add_edge("summarize", "search")
graph.add_edge("search", "compare")
graph.add_edge("compare", END)

# 编译
app = graph.compile()
```

### 流式事件

每个节点开始/结束时发送 SSE step 事件:
```
event: step
data: {"step": "extract", "status": "start", "message": "正在提取关键信息..."}

... (中间流式token)

event: step
data: {"step": "extract", "status": "done"}
```

## 6. Hybrid Search + RRF

```python
async def hybrid_search(query: str, limit: int = 20):
    # 1. 语义搜索
    query_emb = embedding_model.encode(query)
    semantic_results = await db.execute(
        select(Paper.id, Paper.title, 
               1 - Paper.embedding.cosine_distance(query_emb))
        .order_by(Paper.embedding.cosine_distance(query_emb))
        .limit(limit)
    )
    
    # 2. 关键词搜索
    keyword_results = await db.execute(
        select(Paper.id, Paper.title,
               ts_rank(Paper.full_text_tsv, websearch_to_tsquery('english', query)))
        .where(Paper.full_text_tsv.match(query))
        .order_by(ts_rank_desc)
        .limit(limit)
    )
    
    # 3. RRF 融合 (k=60)
    scores = {}
    for rank, (paper_id, _) in enumerate(semantic_results):
        scores[paper_id] = scores.get(paper_id, 0) + 1/(60 + rank + 1)
    for rank, (paper_id, _) in enumerate(keyword_results):
        scores[paper_id] = scores.get(paper_id, 0) + 1/(60 + rank + 1)
    
    # 4. 按RRF分数排序
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return sorted_ids[:limit]
```

## 7. LLM 缓存策略

```python
import hashlib, json
from redis import asyncio as aioredis

redis = aioredis.from_url(REDIS_URL)

def _cache_key(paper_id: str, prompt_type: str) -> str:
    """生成缓存键，基于论文ID和prompt类型"""
    return f"llm_cache:{paper_id}:{prompt_type}"

async def get_cached_or_generate(paper_id, prompt_type, generate_fn):
    cache_key = _cache_key(paper_id, prompt_type)
    cached = await redis.get(cache_key)
    if cached:
        return cached.decode()
    
    result = await generate_fn()
    await redis.setex(cache_key, 86400, result)  # 24h TTL
    return result
```

## 8. Fallback 策略

当 DeepSeek API 不可用时（网络问题/额度耗尽/超时），降级为**提取式摘要**：

```python
async def fallback_extractive_summary(chunks: list[str]) -> str:
    """提取每段首句 + 关键词密度最高的段落"""
    # 1. 取每个chunk的第一句
    first_sentences = [chunk.split('.')[0] for chunk in chunks]
    # 2. 关键词匹配选择核心段落
    # ...
    return compiled_summary
```
