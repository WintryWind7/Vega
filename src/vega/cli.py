"""CLI 入口，所有命令输出 JSON。"""

import argparse
import json
import os
import sys

from .storage import read_entry, write_entry, delete_entry
from .index import load_index, add_or_update, remove, rebuild, search


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".vega")
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")


def _save_config(data_dir: str) -> None:
    """将 data 目录路径写入 ~/.vega/settings.json。"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"data_dir": os.path.abspath(data_dir)}, f, ensure_ascii=False, indent=2)


def _load_config() -> str | None:
    """从 ~/.vega/settings.json 读取 data 目录路径。"""
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("data_dir")


def _resolve_data_dir(args) -> str:
    """获取 data 目录：--data 参数 > ~/.vega.json > 报错。"""
    explicit = getattr(args, "data", None)
    if explicit:
        return explicit

    config_dir = _load_config()
    if config_dir:
        return config_dir

    print(json.dumps({
        "error": "未配置知识库路径，请先运行 vega init --data <路径>"
    }, ensure_ascii=False))
    sys.exit(1)


def cmd_init(args):
    """初始化知识库，必须指定 --data 路径。"""
    if not args.data:
        print(json.dumps({
            "error": "init 必须指定 --data <路径>，例如: vega init --data /path/to/data"
        }, ensure_ascii=False))
        sys.exit(1)

    data_dir = os.path.abspath(args.data)
    os.makedirs(os.path.join(data_dir, "projects"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "user"), exist_ok=True)

    index_path = os.path.join(data_dir, "index.json")
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"entries": []}, f, ensure_ascii=False, indent=2)

    _save_config(data_dir)

    print(json.dumps({"status": "ok", "data_dir": data_dir}, ensure_ascii=False))


def cmd_search(args):
    """搜索索引。"""
    data_dir = _resolve_data_dir(args)
    results = search(data_dir, args.query)
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))


def cmd_read(args):
    """读取条目。"""
    data_dir = _resolve_data_dir(args)
    path = os.path.join(data_dir, args.path)

    if not os.path.exists(path):
        print(json.dumps({"error": f"文件不存在: {args.path}"}, ensure_ascii=False))
        sys.exit(1)

    result = read_entry(path)
    result["path"] = args.path
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_write(args):
    """写入条目，支持增量修改。

    新建时 description 和 tags 必填。
    更新时只修改传入的参数，未传入的保留原值，正文追加。
    """
    data_dir = _resolve_data_dir(args)
    full_path = os.path.join(data_dir, args.path)
    rel_path = args.path.replace("\\", "/")
    exists = os.path.exists(full_path)

    if exists:
        existing = read_entry(full_path)
        meta = dict(existing["meta"])
        content = existing["content"]

        if args.description:
            meta["description"] = args.description
        if args.tags:
            meta["tags"] = [t.strip() for t in args.tags.split(",")]

        stdin_content = sys.stdin.read()
        if stdin_content:
            content = content.rstrip("\n") + "\n\n" + stdin_content
    else:
        if not args.description:
            print(json.dumps({"error": "新建条目必须提供 --description"}, ensure_ascii=False))
            sys.exit(1)
        if not args.tags:
            print(json.dumps({"error": "新建条目必须提供 --tags"}, ensure_ascii=False))
            sys.exit(1)

        meta = {
            "description": args.description,
            "tags": [t.strip() for t in args.tags.split(",")],
        }
        content = sys.stdin.read()

    write_entry(full_path, meta, content)
    add_or_update(data_dir, rel_path, meta)

    print(json.dumps({"status": "ok", "path": args.path}, ensure_ascii=False))


def cmd_delete(args):
    """删除条目。"""
    data_dir = _resolve_data_dir(args)
    path = os.path.join(data_dir, args.path)

    if not os.path.exists(path):
        print(json.dumps({"error": f"文件不存在: {args.path}"}, ensure_ascii=False))
        sys.exit(1)

    delete_entry(path)
    remove(data_dir, args.path.replace("\\", "/"))

    print(json.dumps({"status": "ok", "path": args.path}, ensure_ascii=False))


def cmd_rebuild(args):
    """重建索引。"""
    data_dir = _resolve_data_dir(args)
    index = rebuild(data_dir)
    print(
        json.dumps({"status": "ok", "entries": len(index["entries"])}, ensure_ascii=False)
    )


def cmd_list(args):
    """列出条目。"""
    data_dir = _resolve_data_dir(args)
    index = load_index(data_dir)

    entries = index["entries"]
    if args.prefix:
        entries = [e for e in entries if e["path"].startswith(args.prefix)]

    print(json.dumps({"entries": entries}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="vega", description="Vega 知识库 CLI")

    # 公共参数，所有子命令共享
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", "-D", help="data 目录路径", default=None)

    sub = parser.add_subparsers(dest="command")

    # init
    sub.add_parser("init", parents=[common], help="初始化知识库")

    # search
    p = sub.add_parser("search", parents=[common], help="搜索索引")
    p.add_argument("query", help="搜索关键词，逗号分隔多关键词")

    # read
    p = sub.add_parser("read", parents=[common], help="读取条目")
    p.add_argument("path", help="条目路径（相对于 data/）")

    # write
    p = sub.add_parser("write", parents=[common], help="写入条目，正文从 stdin 读取")
    p.add_argument("path", help="条目路径（相对于 data/）")
    p.add_argument("--description", "-d", help="条目描述")
    p.add_argument("--tags", "-t", help="标签，逗号分隔")

    # delete
    p = sub.add_parser("delete", parents=[common], help="删除条目")
    p.add_argument("path", help="条目路径（相对于 data/）")

    # rebuild
    sub.add_parser("rebuild", parents=[common], help="重建索引")

    # list
    p = sub.add_parser("list", parents=[common], help="列出条目")
    p.add_argument("prefix", nargs="?", default="", help="路径前缀过滤")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    {
        "init": cmd_init,
        "search": cmd_search,
        "read": cmd_read,
        "write": cmd_write,
        "delete": cmd_delete,
        "rebuild": cmd_rebuild,
        "list": cmd_list,
    }[args.command](args)


if __name__ == "__main__":
    main()
