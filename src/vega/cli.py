"""CLI 入口，所有命令输出 JSON。"""

import argparse
import json
import os
import sys

from .storage import write_entry, delete_entry
from .parser import parse
from .index import load_index, rebuild, search
from .check import run as check_run


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

    _save_config(data_dir)

    print(json.dumps({"status": "ok", "data_dir": data_dir}, ensure_ascii=False))


def cmd_search(args):
    """搜索索引，广泛召回。"""
    data_dir = _resolve_data_dir(args)

    if args.project:
        # 项目级搜索：扫描 projects/*/_index.md
        keywords = [kw.strip().lower() for kw in args.query.split(",") if kw.strip()]
        projects_dir = os.path.join(data_dir, "projects")
        results = []

        if os.path.isdir(projects_dir):
            for name in os.listdir(projects_dir):
                index_path = os.path.join(projects_dir, name, "_index.md")
                if not os.path.isfile(index_path):
                    continue
                try:
                    with open(index_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    result = parse(content)
                    meta = result["meta"]
                    proj_name = meta.get("name", name).lower()
                    proj_remote = meta.get("remote", "").lower()
                    proj_desc = meta.get("description", "").lower()

                    score = 0
                    for kw in keywords:
                        if kw in proj_name:
                            score += 3
                        if kw in proj_remote:
                            score += 2
                        if kw in proj_desc:
                            score += 1

                    if score > 0:
                        results.append({
                            "name": meta.get("name", name),
                            "remote": meta.get("remote", ""),
                            "description": meta.get("description", ""),
                            "path": f"projects/{name}/",
                            "score": score,
                        })
                except Exception:
                    continue

        if not results:
            print("无匹配结果")
            return

        results.sort(key=lambda x: x["score"], reverse=True)
        print(f"vega data path: {data_dir}")
        print(f"查询关键字: {args.query}")
        print("文件路径: vega data path/<相对路径>")
        print()
        for i, proj in enumerate(results[:args.limit], 1):
            line = f"{i}. {proj['path']}"
            if proj["description"]:
                line += f": {proj['description']}"
            print(line)
        return

    # 条目级搜索（原有逻辑）
    results = search(data_dir, args.query, limit=args.limit)
    if not results:
        print("无匹配结果")
        return
    print(f"vega data path: {data_dir}")
    print(f"查询关键字: {args.query}")
    print("文件路径: vega data path/<相对路径>")
    print()
    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry['path']}: {entry['description']}")


def cmd_read(args):
    """读取条目，直接输出 md 原文。"""
    data_dir = _resolve_data_dir(args)
    path = os.path.join(data_dir, args.path)

    if not os.path.exists(path):
        print(json.dumps({"error": f"文件不存在: {args.path}"}, ensure_ascii=False))
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        print(f.read())


def cmd_write(args):
    """创建新条目，description 和 tags 必填，正文从 stdin 读取。"""
    data_dir = _resolve_data_dir(args)
    full_path = os.path.join(data_dir, args.path)
    rel_path = args.path.replace("\\", "/")

    if os.path.exists(full_path):
        print(json.dumps({"error": f"条目已存在: {args.path}，请使用 vega edit 修改"}, ensure_ascii=False))
        sys.exit(1)

    meta = {
        "description": args.description,
        "tags": [t.strip() for t in args.tags.split(",")],
    }
    content = sys.stdin.read()

    # 检测是否为新项目目录，自动创建 _index.md
    new_project = False
    if rel_path.startswith("projects/"):
        parts = rel_path.split("/")
        if len(parts) >= 2:
            project_dir = os.path.join(data_dir, "projects", parts[1])
            index_file = os.path.join(project_dir, "_index.md")
            if not os.path.exists(project_dir):
                new_project = True
            elif not os.path.exists(index_file):
                new_project = True

            if new_project:
                project_name = parts[1]
                index_content = (
                    f"---\n"
                    f"name: {project_name}\n"
                    f"remote:\n"
                    f"description:\n"
                    f"---\n\n"
                    f"# {project_name}\n"
                )
                os.makedirs(project_dir, exist_ok=True)
                with open(index_file, "w", encoding="utf-8") as f:
                    f.write(index_content)

    write_entry(full_path, meta, content)

    if new_project:
        project_name = rel_path.split("/")[1]
        print(json.dumps({
            "status": "ok",
            "path": args.path,
            "new_project": project_name,
            "message": f"新项目 {project_name}，已自动创建 _index.md，建议使用 vega edit 补充 remote 和 description",
        }, ensure_ascii=False))
    else:
        print(json.dumps({"status": "ok", "path": args.path}, ensure_ascii=False))


def cmd_edit(args):
    """编辑已有条目，精确字符串替换。"""
    data_dir = _resolve_data_dir(args)
    full_path = os.path.join(data_dir, args.path)
    rel_path = args.path.replace("\\", "/")

    if not os.path.exists(full_path):
        print(json.dumps({"error": f"条目不存在: {args.path}，请使用 vega write 创建"}, ensure_ascii=False))
        sys.exit(1)

    if not args.old or not args.new:
        print(json.dumps({"error": "edit 必须提供 --old 和 --new，且不能为空"}, ensure_ascii=False))
        sys.exit(1)

    with open(full_path, "r", encoding="utf-8") as f:
        text = f.read()

    old = args.old
    new = args.new

    if old == new:
        print(json.dumps({"error": "--old 和 --new 不能相同"}, ensure_ascii=False))
        sys.exit(1)

    if old not in text:
        print(json.dumps({"error": f"未找到要替换的文本"}, ensure_ascii=False))
        sys.exit(1)

    if not args.replace_all and text.count(old) > 1:
        print(json.dumps({"error": f"匹配到 {text.count(old)} 处，请提供更精确的文本或使用 --replace-all"}, ensure_ascii=False))
        sys.exit(1)

    if args.replace_all:
        text = text.replace(old, new)
    else:
        text = text.replace(old, new, 1)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(json.dumps({"status": "ok", "path": args.path}, ensure_ascii=False))


def cmd_delete(args):
    """删除条目。"""
    data_dir = _resolve_data_dir(args)
    path = os.path.join(data_dir, args.path)

    if not os.path.exists(path):
        print(json.dumps({"error": f"文件不存在: {args.path}"}, ensure_ascii=False))
        sys.exit(1)

    delete_entry(path)

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


def cmd_check(args):
    """知识库自检。"""
    data_dir = _resolve_data_dir(args)
    print(check_run(data_dir))


def main():
    # Windows 默认编码可能不是 UTF-8，强制统一
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="vega", description="Vega 知识库 CLI")

    # 公共参数，所有子命令共享
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", "-D", help="data 目录路径", default=None)

    sub = parser.add_subparsers(dest="command")

    # help
    sub.add_parser("help", help="显示帮助信息")

    # init
    sub.add_parser("init", parents=[common], help="初始化知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
初始化 Vega 知识库。

必须指定 --data <路径>，Vega 会在该路径下创建 projects/、user/ 目录。
配置信息保存在 ~/.vega/settings.json 中，后续所有命令自动读取，无需再指定。

如果你是 AI:
  请务必向用户确认 data 目录路径，不要自行决定。

示例:
  vega init --data ~/vega-data
  vega init --data "D:/Vega/data" """)

    # search
    p = sub.add_parser("search", parents=[common], help="搜索条目", description="搜索知识库条目。逗号分隔多关键词，广泛召回，评分降序排列。输出可读列表和完整路径提示")
    p.add_argument("query", help="搜索关键词，逗号分隔多关键词")
    p.add_argument("--limit", "-n", type=int, default=50, help="最大返回条数")
    p.add_argument("--project", action="store_true", help="搜索项目而非条目，匹配项目名、remote、description")

    # read
    p = sub.add_parser("read", parents=[common], help="读取条目", description="读取条目的完整内容，直接输出 md 原文（含 frontmatter 和正文）")
    p.add_argument("path", help="条目路径（相对于 data/）")

    # write
    p = sub.add_parser("write", parents=[common], help="创建新条目，正文从 stdin 读取", description="创建新条目。--description 和 --tags 必填，正文通过 stdin 传入，例如: printf '内容' | vega write path --description '描述' --tags '标签'")
    p.add_argument("path", help="条目路径（相对于 data/）")
    p.add_argument("--description", required=True, help="条目描述（必填）")
    p.add_argument("--tags", required=True, help="标签，逗号分隔（必填）")

    # edit
    p = sub.add_parser("edit", parents=[common], help="编辑已有条目，精确字符串替换", description="编辑已有条目，用 --old 和 --new 进行精确字符串替换。匹配多处时需提供更精确的文本或使用 --replace-all")
    p.add_argument("path", help="条目路径（相对于 data/）")
    p.add_argument("--old", required=True, help="要替换的原文本")
    p.add_argument("--new", required=True, help="替换后的新文本")
    p.add_argument("--replace-all", action="store_true", help="替换所有匹配项")

    # delete
    p = sub.add_parser("delete", parents=[common], help="删除条目", description="删除指定条目")
    p.add_argument("path", help="条目路径（相对于 data/）")

    # rebuild
    sub.add_parser("rebuild", parents=[common], help="全量扫描", description="全量扫描 data/ 下所有 .md 文件")

    # list
    p = sub.add_parser("list", parents=[common], help="列出条目", description="列出所有条目，可按路径前缀过滤")
    p.add_argument("prefix", nargs="?", default="", help="路径前缀过滤")

    # check
    sub.add_parser("check", parents=[common], help="知识库自检", description="检查知识库健康状态：frontmatter 格式、键一致性")

    args = parser.parse_args()
    if args.command is None or args.command == "help":
        parser.print_help()
        sys.exit(0)

    {
        "init": cmd_init,
        "search": cmd_search,
        "read": cmd_read,
        "write": cmd_write,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "rebuild": cmd_rebuild,
        "list": cmd_list,
        "check": cmd_check,
    }[args.command](args)


if __name__ == "__main__":
    main()
