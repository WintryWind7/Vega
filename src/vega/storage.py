"""文件读写模块，基于解析器封装条目的增删改查。"""

import os
from .parser import parse, dump


def read_entry(path: str) -> dict:
    """读取条目，返回解析后的 dict。"""
    with open(path, "r", encoding="utf-8") as f:
        return parse(f.read())


def write_entry(path: str, meta: dict, content: str) -> None:
    """写入条目，自动创建父目录。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(meta, content))


def delete_entry(path: str) -> None:
    """删除条目文件，并清理空的父目录。"""
    if not os.path.exists(path):
        return
    os.remove(path)
    # 清理空目录（只清理一层）
    dir_path = os.path.dirname(path)
    if os.path.isdir(dir_path) and not os.listdir(dir_path):
        os.rmdir(dir_path)


def list_entries(data_dir: str) -> list:
    """列出 data_dir 下所有 .md 文件的相对路径。"""
    entries = []
    for root, _dirs, files in os.walk(data_dir):
        for f in files:
            if f.endswith(".md"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, data_dir)
                entries.append(rel_path.replace("\\", "/"))
    return sorted(entries)
