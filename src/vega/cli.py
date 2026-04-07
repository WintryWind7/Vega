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


def _load_config() -> str | None:
    """从 ~/.vega/settings.json 读取 data 目录路径。"""
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("data_dir")


def _read_stdin_json() -> dict:
    """从 stdin 读取 JSON，空输入返回空字典。"""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"JSON 解析失败: {e}"}, ensure_ascii=False))
        sys.exit(1)


def _require_data_dir() -> str:
    """获取 data 目录，未配置则报错。"""
    config_dir = _load_config()
    if config_dir:
        return config_dir

    print(json.dumps({
        "error": "未配置知识库路径，请先运行 vega init"
    }, ensure_ascii=False))
    sys.exit(1)


def cmd_init(args):
    """初始化知识库，从 stdin 读取 JSON。"""
    data = _read_stdin_json()

    data_path = data.get("data")
    if not data_path:
        print(json.dumps({"error": "data 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    data_dir = os.path.abspath(data_path)
    os.makedirs(os.path.join(data_dir, "projects"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "user"), exist_ok=True)

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"data_dir": data_dir}, f, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "data_dir": data_dir}, ensure_ascii=False))


def cmd_search(args):
    """搜索条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_stdin_json()

    query = data.get("query", "")
    limit = data.get("limit", 50)
    project = data.get("project", False)

    if project:
        keywords = [kw.strip().lower() for kw in query.split(",") if kw.strip()]
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
        for i, proj in enumerate(results[:limit], 1):
            line = f"{i}. {proj['path']}"
            if proj["description"]:
                line += f": {proj['description']}"
            print(line)
        return

    # 条目级搜索
    results = search(data_dir, query, limit=limit)
    if not results:
        print("无匹配结果")
        return
    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry['path']}: {entry['description']}")


def cmd_read(args):
    """读取条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_stdin_json()

    path = data.get("path", "")
    if not path:
        print(json.dumps({"error": "path 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    full_path = os.path.join(data_dir, path)

    if not os.path.exists(full_path):
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        sys.exit(1)

    with open(full_path, "r", encoding="utf-8") as f:
        print(f.read())


def cmd_write(args):
    """创建新条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_stdin_json()

    path = data.get("path", "")
    description = data.get("description", "")
    tags = data.get("tags", [])
    content = data.get("content", "")

    if not path:
        print(json.dumps({"error": "path 字段必填"}, ensure_ascii=False))
        sys.exit(1)
    if not description:
        print(json.dumps({"error": "description 字段必填"}, ensure_ascii=False))
        sys.exit(1)
    if not tags:
        print(json.dumps({"error": "tags 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    rel_path = path.replace("\\", "/")
    full_path = os.path.join(data_dir, rel_path)

    if os.path.exists(full_path):
        print(json.dumps({"error": f"条目已存在: {path}，请使用 vega edit 修改"}, ensure_ascii=False))
        sys.exit(1)

    meta = {
        "description": description,
        "tags": tags,
    }

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
            "path": path,
            "new_project": project_name,
            "message": f"新项目 {project_name}，已自动创建 _index.md，建议使用 vega edit 补充 remote 和 description",
        }, ensure_ascii=False))
    else:
        print(json.dumps({"status": "ok", "path": path}, ensure_ascii=False))


def cmd_edit(args):
    """编辑已有条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_stdin_json()

    path = data.get("path", "")
    if not path:
        print(json.dumps({"error": "path 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    old = data.get("old")
    new = data.get("new")
    replace_all = data.get("replace_all", False)

    if not old or not new:
        print(json.dumps({"error": "old 和 new 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    full_path = os.path.join(data_dir, path)

    if not os.path.exists(full_path):
        print(json.dumps({"error": f"条目不存在: {path}，请使用 vega write 创建"}, ensure_ascii=False))
        sys.exit(1)

    with open(full_path, "r", encoding="utf-8") as f:
        text = f.read()

    if old == new:
        print(json.dumps({"error": "old 和 new 不能相同"}, ensure_ascii=False))
        sys.exit(1)

    if old not in text:
        print(json.dumps({"error": "未找到要替换的文本"}, ensure_ascii=False))
        sys.exit(1)

    if not replace_all and text.count(old) > 1:
        print(json.dumps({"error": f"匹配到 {text.count(old)} 处，请提供更精确的文本或设置 replace_all: true"}, ensure_ascii=False))
        sys.exit(1)

    if replace_all:
        text = text.replace(old, new)
    else:
        text = text.replace(old, new, 1)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(json.dumps({"status": "ok", "path": path}, ensure_ascii=False))


def cmd_delete(args):
    """删除条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_stdin_json()

    path = data.get("path", "")
    if not path:
        print(json.dumps({"error": "path 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    full_path = os.path.join(data_dir, path)

    if not os.path.exists(full_path):
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        sys.exit(1)

    delete_entry(full_path)

    print(json.dumps({"status": "ok", "path": path}, ensure_ascii=False))


def cmd_rebuild(args):
    """重建索引。"""
    data_dir = _require_data_dir()
    index = rebuild(data_dir)
    print(
        json.dumps({"status": "ok", "entries": len(index["entries"])}, ensure_ascii=False)
    )


def cmd_list(args):
    """列出指定目录下的条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_stdin_json()

    prefix = data.get("prefix", "").rstrip("/")

    index = load_index(data_dir)
    entries = index["entries"]
    if prefix:
        entries = [e for e in entries if e["path"].startswith(prefix)]

    if not entries:
        print("无条目")
        return

    for i, entry in enumerate(entries, 1):
        print(f"{i}. {entry['path']}: {entry['description']}")


def cmd_check(args):
    """知识库自检。"""
    data_dir = _require_data_dir()
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
    sub = parser.add_subparsers(dest="command")

    # help
    sub.add_parser("help", help="显示帮助信息")

    # init
    sub.add_parser("init", help="初始化知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
初始化 Vega 知识库，从 stdin 读取 JSON。

JSON 字段：
  data  (必填)  知识库路径

示例：
  vega init <<< '{"data": "~/vega-data"}'
  vega init <<< '{"data": "D:/Vega/data"}'

注意：AI 务必向用户确认 data 目录路径，不要自行决定。""")

    # search
    sub.add_parser("search", help="搜索条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
搜索知识库条目，从 stdin 读取 JSON。

JSON 字段：
  query    (必填)  搜索关键词，逗号分隔多关键词（OR 关系）
  limit    (可选)  最大返回条数，默认 50
  project  (可选)  搜索项目而非条目，默认 false

示例：
  vega search <<< '{"query": "editor"}'
  vega search <<< '{"query": "Python, async", "limit": 20}'
  vega search <<< '{"query": "Vega", "project": true}'""")

    # read
    sub.add_parser("read", help="读取条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
读取条目完整内容，从 stdin 读取 JSON。

JSON 字段：
  path  (必填)  条目路径（相对于 data/，需带 .md 后缀）

示例：
  vega read <<< '{"path": "user/editor-preferences.md"}'""")

    # write
    sub.add_parser("write", help="创建新条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
创建新条目，从 stdin 读取 JSON。

JSON 字段：
  path         (必填)  条目路径（相对于 data/，需带 .md 后缀）
  description  (必填)  条目描述
  tags         (必填)  标签数组
  content      (必填)  正文内容

同路径已存在时报错，请使用 edit 修改。
写入新项目目录时自动创建 _index.md。

示例：
  vega write <<< '{"path": "projects/Vega/async.md", "description": "Python 异步编程", "tags": ["Python", "async", "并发"], "content": "# Python async\\n\\nasyncio 核心概念"}'""")

    # edit
    sub.add_parser("edit", help="编辑已有条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
编辑已有条目，从 stdin 读取 JSON。

JSON 字段：
  path         (必填)  条目路径（相对于 data/，需带 .md 后缀）
  old          (必填)  要替换的文本
  new          (必填)  替换后的文本
  replace_all  (可选)  替换所有匹配，默认 false

示例：
  vega edit <<< '{"path": "projects/Vega/async.md", "old": "旧描述", "new": "新描述"}'
  vega edit <<< '{"path": "projects/Vega/async.md", "old": "旧词", "new": "新词", "replace_all": true}'""")

    # delete
    sub.add_parser("delete", help="删除条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
删除条目，从 stdin 读取 JSON。

JSON 字段：
  path  (必填)  条目路径（相对于 data/，需带 .md 后缀）

示例：
  vega delete <<< '{"path": "projects/Vega/old-note.md"}'""")

    # list
    sub.add_parser("list", help="列出条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
列出条目，从 stdin 读取 JSON。

JSON 字段：
  prefix  (可选)  路径前缀过滤，不填则列出全部

示例：
  vega list <<< '{}'
  vega list <<< '{"prefix": "projects/Vega"}'
  vega list <<< '{"prefix": "user"}'""")

    # rebuild
    sub.add_parser("rebuild", help="全量扫描", description="全量扫描 data/ 下所有 .md 文件")

    # check
    sub.add_parser("check", help="知识库自检", description="检查知识库健康状态：frontmatter 格式、键一致性")

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
