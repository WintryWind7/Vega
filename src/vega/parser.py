"""Frontmatter 解析器，纯标准库实现，零外部依赖。"""

import re

# 分隔符：>=3 个 -，独占一行
_OPEN = re.compile(r"^(-{3,})[ \t]*\n")
_CLOSE = re.compile(r"\n(-{3,})[ \t]*\n")


def parse(text: str) -> dict:
    """解析 Markdown 字符串，返回结构化数据。

    返回格式：
        {"meta": {"description": "...", "tags": [...]}, "content": "正文..."}

    只匹配文件开头和紧接着的第二个分隔符，正文中的 --- 不受影响。
    如果文件没有 frontmatter，meta 为空 dict，content 为原文。
    """
    open_match = _OPEN.match(text)
    if not open_match:
        return {"meta": {}, "content": text}

    after_open = text[open_match.end():]

    close_match = _CLOSE.search(after_open)
    if not close_match:
        return {"meta": {}, "content": text}

    meta_text = after_open[:close_match.start()]
    content = after_open[close_match.end():]

    meta = _parse_meta(meta_text)
    return {"meta": meta, "content": content}


def validate(text: str) -> dict:
    """检查条目格式是否正确，返回校验结果。

    用于搜索引擎和返回结果前的格式验证，确保数据格式正确。
    """
    errors = []

    # 检查 frontmatter 是否存在
    open_match = _OPEN.match(text)
    if not open_match:
        return {"valid": False, "errors": ["缺少 frontmatter 分隔符"]}

    after_open = text[open_match.end():]
    close_match = _CLOSE.search(after_open)
    if not close_match:
        return {"valid": False, "errors": ["frontmatter 未闭合"]}

    meta_text = after_open[:close_match.start()]
    content = after_open[close_match.end():]
    meta = _parse_meta(meta_text)

    # 检查必填字段
    if "description" not in meta:
        errors.append("缺少必填字段: description")
    elif not meta["description"].strip():
        errors.append("description 不能为空")

    if "tags" not in meta:
        errors.append("缺少必填字段: tags")
    elif isinstance(meta["tags"], list) and not meta["tags"]:
        errors.append("tags 不能为空列表")

    # 检查正文
    if not content.strip():
        errors.append("正文不能为空")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "meta": meta,
    }


def dump(meta: dict, content: str) -> str:
    """将结构化数据反向生成为 Markdown 字符串。"""
    if not meta:
        return content

    lines = []
    for key, value in meta.items():
        lines.append(_format_field(key, value))

    frontmatter = "\n".join(lines)
    return f"---\n{frontmatter}\n---\n{content}"


def _parse_meta(text: str) -> dict:
    """解析 frontmatter 文本为 dict。"""
    meta = {}
    lines = text.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # 跳过空行
        if not line.strip():
            i += 1
            continue

        # key: value 格式
        colon_pos = line.find(":")
        if colon_pos == -1:
            i += 1
            continue

        key = line[:colon_pos].strip()
        value = line[colon_pos + 1:].strip()

        # tags 特殊处理：行内数组 [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            meta[key] = _parse_inline_list(value)
            i += 1
            continue

        # 列表格式（下一行以 - 开头）
        if not value:
            items = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:].strip())
                i += 1
            if items:
                meta[key] = items
            continue

        # 普通值
        meta[key] = value
        i += 1

    return meta


def _parse_inline_list(text: str) -> list:
    """解析行内数组 [a, b, c]。"""
    inner = text[1:-1].strip()
    if not inner:
        return []
    return [item.strip() for item in inner.split(",")]


def _format_field(key: str, value) -> str:
    """格式化单个字段为 key: value 字符串。"""
    if isinstance(value, list):
        return f"{key}: [{', '.join(value)}]"
    return f"{key}: {value}"
