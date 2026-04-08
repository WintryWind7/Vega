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
    missing_from_index = actual_paths - indexed_paths
    extra_in_index = indexed_paths - actual_paths

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
    if missing_from_index or extra_in_index:
        issues = len(missing_from_index) + len(extra_in_index)
        lines.append(f"[索引一致] {issues} 个异常")
        for p in sorted(missing_from_index):
            lines.append(f"  缺失: {p}")
        for p in sorted(extra_in_index):
            lines.append(f"  多余: {p}")
        lines.append("  建议: 运行 vega rebuild 重建索引")
    else:
        lines.append("[索引一致] 全部通过")

    # 总结
    lines.append("")
    has_issues = format_errors or missing_from_index or extra_in_index
    if not has_issues:
        lines.append("结果: 全部通过")
    else:
        issue_count = len(format_errors) + len(missing_from_index) + len(extra_in_index)
        lines.append(f"结果: {total - len(format_errors)} 通过, {issue_count} 异常")

    return "\n".join(lines)
