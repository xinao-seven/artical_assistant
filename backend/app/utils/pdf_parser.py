"""
PDF 解析工具
- 使用 pdfplumber 提取文本和元数据
- 使用 pypdf 提取 PDF 信息
"""
import re
from pathlib import Path

import pdfplumber
from loguru import logger


def extract_pdf_metadata(file_path: str) -> dict:
    """
    从 PDF 文件中提取元数据

    Args:
        file_path: PDF 文件路径

    Returns:
        dict: {
            "title": str | None,
            "authors": list[str],
            "abstract": str | None,
            "year": int | None,
            "pages_count": int,
            "full_text": str,
        }
    """
    result = {
        "title": None,
        "authors": [],
        "abstract": None,
        "year": None,
        "pages_count": 0,
        "full_text": "",
    }

    path = Path(file_path)
    if not path.exists():
        logger.error(f"PDF 文件不存在: {file_path}")
        return result

    try:
        with pdfplumber.open(file_path) as pdf:
            result["pages_count"] = len(pdf.pages)

            # 提取所有文本
            all_text_parts = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    all_text_parts.append(page_text)

            full_text = "\n".join(all_text_parts)
            result["full_text"] = full_text

            # 尝试从第一页提取标题和作者
            if all_text_parts:
                first_page = all_text_parts[0]
                result["title"] = _extract_title(first_page)
                result["authors"] = _extract_authors(first_page)
                result["abstract"] = _extract_abstract(full_text)
                result["year"] = _extract_year(full_text)

    except Exception as e:
        logger.error(f"PDF 解析失败 {file_path}: {e}")

    # 使用 pypdf 补充元数据
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        meta = reader.metadata

        # pypdf 元数据优先
        if meta and not result["title"]:
            result["title"] = meta.get("/Title", None)
        if meta and not result["authors"]:
            author_str = meta.get("/Author", None)
            if author_str:
                result["authors"] = [a.strip() for a in re.split(r"[,;，；]", author_str) if a.strip()]
        if meta and not result["year"]:
            # 尝试从 /CreationDate 提取年份
            creation = meta.get("/CreationDate", "")
            year_match = re.search(r"(\d{4})", str(creation))
            if year_match:
                result["year"] = int(year_match.group(1))
    except Exception as e:
        logger.warning(f"pypdf 元数据提取失败: {e}")

    return result


def _extract_title(first_page_text: str) -> str | None:
    """
    从第一页文本中提取标题
    启发式: 第一页的第一个非空短行（通常论文标题在顶部）
    """
    lines = [l.strip() for l in first_page_text.split("\n") if l.strip()]
    if not lines:
        return None

    # 跳过明显不是标题的内容 (如期刊名、会议名等元信息)
    skip_patterns = [
        r"^(proceedings|journal|conference|IEEE|ACM|Springer|Elsevier)",
        r"^\d{4}\s",
        r"^Vol[. ]\d+",
        r"^pp[. ]\d+",
        r"^©",
        r"^arxiv",
        r"^preprint",
        r"^submitted",
        r"^received",
        r"^published",
        r"^abstract$",
        r"^key ?words",
    ]

    for line in lines[:20]:  # 只在前20行中搜索
        if len(line) < 5 or len(line) > 500:
            continue
        skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                skip = True
                break
        if not skip:
            # 标题通常是句子形式，包含多个单词
            if len(line.split()) >= 2:
                return line

    return lines[0] if lines else None


def _extract_authors(first_page_text: str) -> list[str]:
    """
    从第一页提取作者列表
    启发式: 标题下方紧跟的作者行
    """
    lines = [l.strip() for l in first_page_text.split("\n") if l.strip()]
    if len(lines) < 2:
        return []

    # 常见作者分隔符
    for line in lines[:30]:
        # 包含多个逗号或分号，或包含 email/@符号，或包含数字上标
        if re.search(r"[,;，；].*[,;，；]", line) or "@" in line:
            # 清理数字上标和机构标记
            cleaned = re.sub(r"[\d*†‡§¶#]+", "", line)
            cleaned = re.sub(r"\(.*?\)", "", cleaned)
            # 按分隔符拆分
            parts = re.split(r"[,;，；]", cleaned)
            authors = [p.strip() for p in parts if len(p.strip()) > 2]
            if 1 <= len(authors) <= 30:  # 合理作者数量
                return authors

    return []


def _extract_abstract(full_text: str) -> str | None:
    """
    从全文中提取摘要
    启发式: 搜索 "Abstract" 标记后的段落
    """
    # 尝试多种摘要标记
    patterns = [
        r"(?i)abstract\s*\n+(.*?)(?:\n\s*\n|\n(?:1[. ]|I[. ]|Introduction|Keywords|Key words))",
        r"(?i)abstract[：:]\s*(.*?)(?:\n\s*\n|\n(?:1[. ]|I[. ]|Introduction|Keywords|Key words))",
        r"(?i)a\s*b\s*s\s*t\s*r\s*a\s*c\s*t\s*\n+(.*?)(?:\n\s*\n)",
    ]

    for pattern in patterns:
        match = re.search(pattern, full_text, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # 清理多余空白
            abstract = re.sub(r"\s+", " ", abstract)
            if len(abstract) >= 30:
                return abstract[:5000]  # 限制摘要长度

    return None


def _extract_year(full_text: str) -> int | None:
    """
    从全文中提取发表年份
    启发式: 搜索常见的年份标记
    """
    patterns = [
        r"(?:©|copyright|published)[^\d]*(\d{4})",
        r"(?:conference|proceedings)[^\d]*(\d{4})",
        r"(\d{4})\s*(?:ACM|IEEE|Springer|Elsevier)",
    ]

    for pattern in patterns:
        match = re.search(pattern, full_text[:2000], re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 1900 <= year <= 2030:
                return year

    return None
