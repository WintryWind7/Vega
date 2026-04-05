"""搜索模块，即时扫描文件进行检索，无持久索引。"""

import os

from .storage import read_entry, list_entries


def _make_entry(rel_path: str, meta: dict) -> dict:
    """将条目转为索引记录，title 从文件名推断。"""
    title = os.path.splitext(os.path.basename(rel_path))[0]
    return {
        "path": rel_path,
        "title": title,
        "description": meta.get("description", ""),
        "tags": meta.get("tags", []),
    }


def load_index(data_dir: str) -> dict:
    """即时扫描所有条目，返回兼容格式。"""
    entries = []
    for rel_path in list_entries(data_dir):
        full_path = os.path.join(data_dir, rel_path)
        try:
            result = read_entry(full_path)
            entries.append(_make_entry(rel_path, result["meta"]))
        except Exception:
            continue
    return {"entries": entries}


def rebuild(data_dir: str) -> dict:
    """全量扫描条目，返回统计信息。"""
    return load_index(data_dir)


def search(data_dir: str, query: str, limit: int = 50) -> list:
    """搜索条目，即时扫描文件，广泛召回。

    支持逗号分隔多关键词，按 path/title/tags/description 匹配。
    返回 score > 0 的结果，按相关度降序排列，最多 limit 条。
    """
    keywords = [kw.strip().lower() for kw in query.split(",") if kw.strip()]
    results = []

    for rel_path in list_entries(data_dir):
        full_path = os.path.join(data_dir, rel_path)
        try:
            result = read_entry(full_path)
            meta = result["meta"]
        except Exception:
            continue

        entry = _make_entry(rel_path, meta)
        score = 0
        title = entry["title"].lower()
        desc = entry["description"].lower()
        tags = [t.lower() for t in entry.get("tags", [])]

        for kw in keywords:
            if kw in title:
                score += 3
            for tag in tags:
                if kw in tag:
                    score += 2
            if kw in desc:
                score += 1
            if kw in entry["path"].lower():
                score += 1

        if score > 0:
            results.append({**entry, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
