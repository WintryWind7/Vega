"""自检模块，扫描知识库的格式、键统计和索引一致性。"""

import os
from collections import Counter

from .parser import validate
from .storage import list_entries, read_entry
from .index import load_index


def run(data_dir: str) -> str:
    """执行全部检查，返回格式化的文本报告。"""
    files = list_entries(data_dir)
    total = len(files)

    # 格式校验
    format_errors = []
    for rel_path in files:
        full_path = os.path.join(data_dir, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            result = validate(f.read())
        if not result["valid"]:
            format_errors.append({"path": rel_path, "errors": result["errors"]})

    # 键统计
    key_counter = Counter()
    for rel_path in files:
        full_path = os.path.join(data_dir, rel_path)
        try:
            entry = read_entry(full_path)
            key_counter.update(entry["meta"].keys())
        except Exception:
            pass

    # 索引一致性
    index = load_index(data_dir)
    indexed_paths = {e["path"] for e in index["entries"]}
    actual_paths = set(files)

    missing_files = indexed_paths - actual_paths
    missing_entries = actual_paths - indexed_paths

    # 索引内容与文件实际内容不一致
    content_mismatch = []
    for entry in index["entries"]:
        if entry["path"] not in actual_paths:
            continue
        full_path = os.path.join(data_dir, entry["path"])
        try:
            actual = read_entry(full_path)
            actual_title = os.path.splitext(os.path.basename(entry["path"]))[0]
            if (entry["title"] != actual_title
                    or entry["description"] != actual["meta"].get("description", "")
                    or entry["tags"] != actual["meta"].get("tags", [])):
                content_mismatch.append(entry["path"])
        except Exception:
            pass

    # 生成报告
    passed = total - len(format_errors)
    lines = [
        "Vega 知识库自检报告",
        "====================",
        f"总计 {total} 个条目",
        "",
    ]

    # 格式问题
    if format_errors:
        lines.append(f"[格式问题] {len(format_errors)} 个异常")
        for item in format_errors:
            lines.append(f"  {item['path']}")
            for err in item["errors"]:
                lines.append(f"    x {err}")
    else:
        lines.append("[格式问题] 全部通过")

    # 键统计
    lines.append("")
    lines.append("[键统计]")
    # 找出标准键（出现次数最多的）
    if key_counter:
        max_count = max(key_counter.values())
        stats = []
        for key, count in sorted(key_counter.items()):
            if count < max_count:
                stats.append(f"{key}: {count}  < anomaly")
            else:
                stats.append(f"{key}: {count}")
        lines.append("  " + ", ".join(stats))

    # 索引一致性
    lines.append("")
    index_ok = not missing_files and not missing_entries and not content_mismatch
    if index_ok:
        lines.append("[索引一致性] 正常")
    else:
        lines.append("[索引一致性] 异常")
        for p in sorted(missing_files):
            lines.append(f"  {p} — 索引有记录但文件不存在")
        for p in sorted(missing_entries):
            lines.append(f"  {p} — 文件存在但索引无记录")
        for p in content_mismatch:
            lines.append(f"  {p} — 索引内容与文件不一致")

    # 总结
    lines.append("")
    failed = len(format_errors) + (1 if not index_ok else 0)
    if failed == 0:
        lines.append("结果: 全部通过")
    else:
        lines.append(f"结果: {passed} 通过, {failed} 异常")

    return "\n".join(lines)
