"""
PDF 解析工具 (v3 — AI 直解析)

流程:
  1. pdfplumber 提取 PDF 全文本
  2. 截取前 ~5000 字符发给 DeepSeek
  3. DeepSeek 返回结构化 JSON: {title, authors, abstract, year}
  4. pypdf 元数据作为补充
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pdfplumber
from loguru import logger

from app.config import settings

# ============================================================
# 主入口
# ============================================================

# 送给 AI 的最大字符数（控制 token 消耗）
AI_MAX_CHARS = 5000


def extract_pdf_metadata(file_path: str) -> dict:
    """
    从 PDF 提取元数据（AI 直解析 + pypdf 补充）

    Returns:
        {"title": str|None, "authors": list[str], "abstract": str|None,
         "year": int|None, "pages_count": int, "full_text": str}
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"PDF 文件不存在: {file_path}")
        return _empty_result()

    try:
        # ---------- 第1步: 提取文本 ----------
        with pdfplumber.open(file_path) as pdf:
            pages_text: list[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            full_text = "\n".join(pages_text)
            pages_count = len(pdf.pages)

        if not full_text.strip():
            logger.warning(f"PDF 无文本内容: {file_path}")
            result = _empty_result()
            result["pages_count"] = pages_count
            return result

        # ---------- 第2步: AI 解析元数据 ----------
        ai_data = _call_deepseek(full_text[:AI_MAX_CHARS])

        # ---------- 第3步: pypdf 补充 ----------
        pypdf_data = _extract_pypdf_meta(file_path)

        # ---------- 第4步: 合并结果（AI优先，pypdf补充） ----------
        title = ai_data.get("title") or pypdf_data.get("title")
        authors = ai_data.get("authors") or pypdf_data.get("authors") or []
        abstract = ai_data.get("abstract") or pypdf_data.get("abstract")
        year = ai_data.get("year") or pypdf_data.get("year")

        # 后处理
        title = _clean_text(title)
        authors = [_clean_author(a) for a in authors if a and len(str(a).strip()) > 2]
        abstract = _clean_text(abstract)

        logger.info(
            f"PDF 解析完成 | 标题={title[:60] if title else 'N/A'} | "
            f"作者数={len(authors)} | 年份={year} | 页数={pages_count}"
        )

        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "year": year,
            "pages_count": pages_count,
            "full_text": full_text,
        }

    except Exception as e:
        logger.error(f"PDF 解析失败 {file_path}: {e}", exc_info=True)
        return _empty_result()


# ============================================================
# DeepSeek AI 解析
# ============================================================

def _call_deepseek(text: str) -> dict:
    """调用 DeepSeek 从论文文本中提取结构化元数据"""
    if not settings.DEEPSEEK_API_KEY:
        logger.warning("未配置 DEEPSEEK_API_KEY，跳过 AI 解析")
        return {}

    prompt = f"""你是学术论文元数据提取专家。从以下论文文本中提取信息，严格按 JSON 格式返回。

规则:
- title: 论文完整标题（去除换行和多余空格）
- authors: 作者姓名数组，只保留人名，去除数字上标、机构名、邮箱
  例如: ["John Smith", "Alice Wang"]
- abstract: 摘要正文（去除 Abstract 标签），如果没有摘要返回空字符串
- year: 发表年份（整数），优先从 DOI/版权声明中提取；找不到返回 null

只返回 JSON，不要任何解释文字。

论文文本:
{text[:AI_MAX_CHARS]}
"""

    try:
        response = httpx.post(
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,       # 低温，追求确定性
                "max_tokens": 800,
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)
        logger.debug(f"DeepSeek 解析结果: {json.dumps(result, ensure_ascii=False)[:200]}")
        return result

    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek API HTTP 错误: {e.response.status_code} - {e.response.text[:200]}")
        return {}
    except Exception as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        return {}


# ============================================================
# pypdf 元数据补充
# ============================================================

def _extract_pypdf_meta(file_path: str) -> dict:
    """从 PDF 内嵌元数据提取信息（作为 AI 的补充）"""
    result: dict = {}
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        meta = reader.metadata
        if not meta:
            return result

        # 标题
        t = meta.get("/Title")
        if t and str(t).strip():
            result["title"] = str(t).strip()

        # 作者
        a = meta.get("/Author")
        if a:
            parts = [p.strip() for p in str(a).replace(";", ",").split(",") if p.strip()]
            if parts:
                result["authors"] = parts

        # 年份 (从 /CreationDate)
        import re
        creation = str(meta.get("/CreationDate", ""))
        m = re.search(r"(19\d{2}|20\d{2})", creation)
        if m:
            year = int(m.group(1))
            if 1900 <= year <= 2030:
                result["year"] = year

    except Exception as e:
        logger.debug(f"pypdf 元数据读取失败: {e}")

    return result


# ============================================================
# 后处理
# ============================================================

def _clean_text(text: str | None) -> str | None:
    """清理文本: 合并空白、去除首尾噪音"""
    if not text:
        return None
    import re
    text = re.sub(r"\s+", " ", str(text)).strip()
    text = text.strip(".,;:!?\"' \t\n\r-")
    return text if len(text) >= 3 else None


def _clean_author(name: str) -> str:
    """清理作者名: 去除上标数字、特殊符号"""
    import re
    name = re.sub(r"\s+", " ", str(name)).strip()
    name = re.sub(r"[\d*†‡§¶#★☆●◎○▲△▼▽]+", "", name)
    name = name.strip(".,;: \t\n\r")
    return name


def _empty_result() -> dict:
    """返回空结果"""
    return {
        "title": None,
        "authors": [],
        "abstract": None,
        "year": None,
        "pages_count": 0,
        "full_text": "",
    }

