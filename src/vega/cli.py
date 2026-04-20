"""CLI 入口，所有命令输出 JSON。"""

import argparse
import json
import os
import sys

from .storage import write_entry, read_entry, delete_entry, _atomic_write
from .parser import parse
from .index import load_index, save_index, rebuild, search, add_or_update, remove
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



def _read_input(args) -> dict:
    """从 stdin 读取 JSON，stdin 为空时取位置参数。两者都无则返回空字典。"""
    raw = sys.stdin.read()
    if raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"JSON 解析失败: {e}"}, ensure_ascii=False))
            sys.exit(1)
    if hasattr(args, 'json') and args.json:
        try:
            return json.loads(args.json)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"JSON 解析失败: {e}"}, ensure_ascii=False))
            sys.exit(1)
    return {}


def _require_data_dir() -> str:
    """获取 data 目录，未配置则报错。"""
    config_dir = _load_config()
    if config_dir:
        return config_dir

    print(json.dumps({
        "error": "未配置知识库路径，请先运行 vega init"
    }, ensure_ascii=False))
    sys.exit(1)


def _path_not_found(data_dir: str, path: str):
    """路径不存在时输出智能建议并退出。"""
    full_path = os.path.join(data_dir, path)

    # 场景 1：路径是目录
    if os.path.isdir(full_path):
        entries = sorted(f for f in os.listdir(full_path) if not f.startswith('_'))
        msg = f"路径是目录: {path}"
        if entries:
            msg += f"，目录内容: {', '.join(entries)}"
        print(json.dumps({"error": msg}, ensure_ascii=False))
        sys.exit(1)

    # 场景 2 & 3：路径不存在，检查父目录
    parent_full = os.path.dirname(full_path)
    basename = os.path.basename(path)

    if os.path.isdir(parent_full):
        siblings = sorted(os.listdir(parent_full))

        # 场景 2：前缀完全匹配（同词干不同扩展名）
        stem_matches = [f for f in siblings if os.path.splitext(f)[0] == basename]
        if stem_matches:
            parent_rel = os.path.dirname(path)
            suggested = (parent_rel + "/" + stem_matches[0]) if parent_rel else stem_matches[0]
            print(json.dumps({
                "error": f"文件不存在: {path}",
                "hint": f"未找到 {path}，但找到了 {suggested}",
            }, ensure_ascii=False))
            sys.exit(1)

        # 场景 3：无前缀匹配，列出目录内容
        entries = [f for f in siblings if not f.startswith('_')]
        if entries:
            print(json.dumps({
                "error": f"文件不存在: {path}",
                "hint": f"该目录下的文件: {', '.join(entries)}",
            }, ensure_ascii=False))
            sys.exit(1)

    print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
    sys.exit(1)


def cmd_init(args):
    """初始化知识库，从 stdin 读取 JSON。"""
    data = _read_input(args)

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
    data = _read_input(args)

    query = data.get("query", "")
    if not query:
        print(json.dumps({"error": "query 字段必填"}, ensure_ascii=False))
        sys.exit(1)
    limit = data.get("limit", 50)
    search_type = data.get("type", "file")
    mode = data.get("mode", "and")

    if search_type == "project":
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
                        kw_score = 0
                        if kw in proj_name:
                            kw_score += 3
                        if kw in proj_remote:
                            kw_score += 2
                        if kw in proj_desc:
                            kw_score += 1
                        if mode == "and" and kw_score == 0:
                            break
                        score += kw_score
                    else:
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
        shown = results[:limit]
        print(f"共 {len(shown)} 个匹配")
        for i, proj in enumerate(shown, 1):
            line = f"{i}. {proj['path']}"
            if proj["description"]:
                line += f": {proj['description']}"
            print(line)
        return

    # 条目级搜索
    results = search(data_dir, query, limit=limit, mode=mode)
    if not results:
        print("无匹配结果")
        return
    print(f"共 {len(results)} 个匹配")
    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry['path']}: {entry['description']}")


def cmd_read(args):
    """读取条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_input(args)

    path = data.get("path", "")
    if not path:
        print(json.dumps({"error": "path 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    full_path = os.path.join(data_dir, path)

    if not os.path.isfile(full_path):
        _path_not_found(data_dir, path)

    with open(full_path, "r", encoding="utf-8") as f:
        print(f.read())


def cmd_write(args):
    """创建新条目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_input(args)

    path = data.get("path", "")
    description = data.get("description", "")
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
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
    add_or_update(data_dir, rel_path, meta)

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
    data = _read_input(args)

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

    if not os.path.isfile(full_path):
        _path_not_found(data_dir, path)

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

    _atomic_write(full_path, text)

    # 重新解析文件更新索引
    try:
        result = read_entry(full_path)
        add_or_update(data_dir, path, result["meta"])
    except Exception:
        pass

    print(json.dumps({"status": "ok", "path": path}, ensure_ascii=False))


def cmd_delete(args):
    """删除条目或项目，从 stdin 读取 JSON。"""
    import shutil

    data_dir = _require_data_dir()
    data = _read_input(args)

    path = data.get("path", "").replace("\\", "/")
    if not path:
        print(json.dumps({"error": "path 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    full_path = os.path.join(data_dir, path.rstrip("/"))

    if not os.path.exists(full_path):
        _path_not_found(data_dir, path)

    # 项目级删除（实际路径为目录）
    if os.path.isdir(full_path):
        project_prefix = path.rstrip("/")
        index = load_index(data_dir)
        deleted_entries = [e for e in index["entries"] if e["path"].startswith(project_prefix + "/")]

        shutil.rmtree(full_path)

        index["entries"] = [e for e in index["entries"] if not e["path"].startswith(project_prefix + "/")]
        save_index(data_dir, index)

        print(json.dumps({
            "status": "ok",
            "path": path,
            "entries_deleted": len(deleted_entries),
        }, ensure_ascii=False))
        return

    # 条目级删除
    # 删除前读取内容，用于返回确认信息
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    delete_entry(full_path)
    remove(data_dir, path)

    print(json.dumps({"status": "ok", "path": path, "content": content}, ensure_ascii=False))


def cmd_move(args):
    """移动/重命名条目或项目，从 stdin 读取 JSON。"""
    data_dir = _require_data_dir()
    data = _read_input(args)

    from_path = data.get("from", "").replace("\\", "/")
    to_path = data.get("to", "").replace("\\", "/")

    if not from_path or not to_path:
        print(json.dumps({"error": "from 和 to 字段必填"}, ensure_ascii=False))
        sys.exit(1)

    if from_path == to_path:
        print(json.dumps({"error": "from 和 to 不能相同"}, ensure_ascii=False))
        sys.exit(1)

    src_full = os.path.join(data_dir, from_path.rstrip("/"))
    dst_full = os.path.join(data_dir, to_path.rstrip("/"))

    if not os.path.exists(src_full):
        _path_not_found(data_dir, from_path)

    if os.path.exists(dst_full):
        print(json.dumps({"error": f"目标路径已存在: {to_path}"}, ensure_ascii=False))
        sys.exit(1)

    # 项目级移动（源路径为目录）
    if os.path.isdir(src_full):
        old_prefix = from_path.rstrip("/")
        index = load_index(data_dir)
        affected = [e for e in index["entries"] if e["path"].startswith(old_prefix + "/")]

        os.makedirs(os.path.dirname(dst_full), exist_ok=True)
        os.rename(src_full, dst_full)

        # 更新 _index.md 中的 name（如果项目名变了）
        old_name = os.path.basename(src_full)
        new_name = os.path.basename(dst_full)
        if old_name != new_name:
            index_file = os.path.join(dst_full, "_index.md")
            if os.path.isfile(index_file):
                with open(index_file, "r", encoding="utf-8") as f:
                    text = f.read()
                text = text.replace(f"name: {old_name}", f"name: {new_name}")
                text = text.replace(f"# {old_name}", f"# {new_name}")
                _atomic_write(index_file, text)

        # 批量更新索引
        new_prefix = to_path.rstrip("/")
        for entry in affected:
            entry["path"] = new_prefix + entry["path"][len(old_prefix):]

        save_index(data_dir, index)

        print(json.dumps({
            "status": "ok",
            "from": from_path,
            "to": to_path,
            "entries_moved": len(affected),
        }, ensure_ascii=False))
    else:
        # 条目级移动
        os.makedirs(os.path.dirname(dst_full), exist_ok=True)
        os.rename(src_full, dst_full)

        # 更新索引：先移除旧路径，再添加新路径
        remove(data_dir, from_path)
        try:
            result = read_entry(dst_full)
            add_or_update(data_dir, to_path, result["meta"])
        except Exception:
            pass

        # 清理源空目录
        src_dir = os.path.dirname(src_full)
        if os.path.isdir(src_dir) and not os.listdir(src_dir):
            os.rmdir(src_dir)

        print(json.dumps({"status": "ok", "from": from_path, "to": to_path}, ensure_ascii=False))


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
    data = _read_input(args)

    prefix = data.get("prefix", "").rstrip("/")

    index = load_index(data_dir)
    entries = index["entries"]
    if prefix:
        entries = [e for e in entries if e["path"].startswith(prefix)]

    if not entries:
        print("无条目")
        return

    print(f"共 {len(entries)} 个条目")
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

    parser = argparse.ArgumentParser(
        prog="vega",
        description="Vega 知识库 CLI。所有命令通过 stdin 读取 JSON 参数。",
        epilog="路径示例：projects/Vega/async.md、user/editor-preferences.md。不确定路径时用 list 查看。",
    )
    sub = parser.add_subparsers(dest="command")

    # help
    sub.add_parser("help", help="显示帮助信息")

    # init
    p = sub.add_parser("init", help="初始化知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
初始化 Vega 知识库，从 stdin 读取 JSON。

JSON 字段：
  data  (必填)  知识库路径

示例：
  vega init <<< '{"data": "~/vega-data"}'
  vega init <<< '{"data": "D:/Vega/data"}'

注意：务必向用户确认 data 目录路径，不要自行决定。""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # search
    p = sub.add_parser("search", help="搜索条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
搜索知识库条目，从 stdin 读取 JSON。

JSON 字段：
  query    (必填)  搜索关键词，逗号分隔多关键词
  mode     (可选)  匹配模式："and"（所有关键词都匹配）或 "or"（任一匹配），默认 "and"
  limit    (可选)  最大返回条数，默认 50
  type     (可选)  搜索类型："file"（条目）或 "project"（项目），默认 "file"

结果按相关度降序排列（title 权重 3，tags 2，description/path 1）。

示例：
  vega search <<< '{"query": "editor"}'
  vega search <<< '{"query": "Python, async", "mode": "or", "limit": 20}'
  vega search <<< '{"query": "Vega", "type": "project"}'""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # read
    p = sub.add_parser("read", help="读取条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
读取条目完整内容，从 stdin 读取 JSON。

JSON 字段：
  path  (必填)  条目路径，如 projects/Vega/async.md

示例：
  vega read <<< '{"path": "user/editor-preferences.md"}'""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # write
    p = sub.add_parser("write", help="创建新条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
创建新条目，从 stdin 读取 JSON。

JSON 字段：
  path         (必填)  条目路径，如 projects/Vega/async.md
  description  (必填)  条目描述
  tags         (必填)  标签数组
  content      (必填)  正文内容

同路径已存在时报错，请使用 edit 修改。
写入新项目目录时自动创建 _index.md。

示例：
  vega write <<< '{"path": "projects/Vega/async.md", "description": "Python 异步编程", "tags": ["Python", "async", "并发"], "content": "# Python async\\n\\nasyncio 核心概念"}'""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # edit
    p = sub.add_parser("edit", help="编辑已有条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
编辑已有条目，从 stdin 读取 JSON。

JSON 字段：
  path         (必填)  条目路径，如 projects/Vega/async.md
  old          (必填)  要替换的文本
  new          (必填)  替换后的文本
  replace_all  (可选)  替换所有匹配，默认 false

示例：
  vega edit <<< '{"path": "projects/Vega/async.md", "old": "旧描述", "new": "新描述"}'
  vega edit <<< '{"path": "projects/Vega/async.md", "old": "旧词", "new": "新词", "replace_all": true}'""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # delete
    p = sub.add_parser("delete", help="删除条目或项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
删除条目或项目，从 stdin 读取 JSON。

JSON 字段：
  path  (必填)  条目路径（如 projects/Vega/note.md）或项目路径（以 / 结尾，如 projects/Vega/）

示例：
  vega delete <<< '{"path": "projects/Vega/old-note.md"}'
  vega delete <<< '{"path": "projects/OldProject/"}'""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # move
    p = sub.add_parser("move", help="移动/重命名条目或项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
移动或重命名条目/项目，从 stdin 读取 JSON。

JSON 字段：
  from  (必填)  源路径
  to    (必填)  目标路径

条目路径带 .md 后缀，项目路径以 / 结尾。
目标路径已存在时报错。

示例：
  vega move <<< '{"from": "projects/Vega/async.md", "to": "projects/Vega/concurrency.md"}'
  vega move <<< '{"from": "projects/Vega/", "to": "projects/Vega2/"}'
  vega move <<< '{"from": "user/note.md", "to": "projects/Vega/note.md"}'""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # list
    p = sub.add_parser("list", help="列出条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
列出条目，从 stdin 读取 JSON。

JSON 字段：
  prefix  (可选)  路径前缀过滤，不填则列出全部

示例：
  vega list <<< '{}'
  vega list <<< '{"prefix": "projects/Vega"}'
  vega list <<< '{"prefix": "user"}'""")
    p.add_argument("json", nargs="?", help="JSON 参数（也可通过 stdin 传入）")

    # rebuild
    sub.add_parser("rebuild", help="全量扫描", description="全量扫描知识库下所有 .md 文件并重建索引")

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
        "move": cmd_move,
        "rebuild": cmd_rebuild,
        "list": cmd_list,
        "check": cmd_check,
    }[args.command](args)


if __name__ == "__main__":
    main()
