"""索引管理模块，维护 index.json 的读写和检索。"""

import json
import os

from .storage import read_entry


INDEX_FILE = "index.json"


def load_index(data_dir: str) -> dict:
    """加载索引，不存在则返回空索引。"""
    path = os.path.join(data_dir, INDEX_FILE)
    if not os.path.exists(path):
        return {"entries": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(data_dir: str, index: dict) -> None:
    """保存索引到文件。"""
    path = os.path.join(data_dir, INDEX_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _make_entry(rel_path: str, meta: dict) -> dict:
    """将条目转为索引记录，title 从文件名推断。"""
    title = os.path.splitext(os.path.basename(rel_path))[0]
    return {
        "path": rel_path,
        "title": title,
        "description": meta.get("description", ""),
        "tags": meta.get("tags", []),
    }


def add_or_update(data_dir: str, rel_path: str, meta: dict) -> None:
    """添加或更新索引中的条目。"""
    index = load_index(data_dir)
    entry = _make_entry(rel_path, meta)

    for i, e in enumerate(index["entries"]):
        if e["path"] == rel_path:
            index["entries"][i] = entry
            break
    else:
        index["entries"].append(entry)

    save_index(data_dir, index)


def remove(data_dir: str, rel_path: str) -> None:
    """从索引中移除条目。"""
    index = load_index(data_dir)
    index["entries"] = [e for e in index["entries"] if e["path"] != rel_path]
    save_index(data_dir, index)


def rebuild(data_dir: str) -> dict:
    """全量重建索引，扫描 data_dir 下所有 .md 文件。"""
    from .storage import list_entries

    entries = []
    for rel_path in list_entries(data_dir):
        full_path = os.path.join(data_dir, rel_path)
        try:
            result = read_entry(full_path)
            entries.append(_make_entry(rel_path, result["meta"]))
        except Exception:
            continue

    index = {"entries": entries}
    save_index(data_dir, index)
    return index


def search(data_dir: str, query: str) -> list:
    """搜索索引，支持多关键词（空格分隔），按 title/tags/description 匹配。"""
    index = load_index(data_dir)
    keywords = [kw.strip().lower() for kw in query.split(",") if kw.strip()]
    results = []

    for entry in index["entries"]:
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

        if score > 0:
            results.append({**entry, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
