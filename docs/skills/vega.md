---
name: vega
description: Vega 知识库操作，用于搜索、读写跨项目知识
---

当需要存储或检索跨项目知识、个人偏好、设计经验时，使用 Vega CLI。

## 命令

所有命令通过 stdin 读取 JSON 参数。有必填字段的命令必须传入 JSON；全部字段可选或无字段的命令可以不传：

```bash
vega write <<< '{"path": "...", "description": "...", "tags": [...], "content": "..."}'
vega list                    # 无需传 JSON，直接列出全部
```

- `vega init` — 初始化知识库。`{"data": "路径"}`（必填）
- `vega search` — 搜索条目。`{"query": "关键词"}`（必填），`limit`（可选，默认 50），`project`（可选，默认 false，搜索项目而非条目）
- `vega read` — 读取条目，输出 md 原文。`{"path": "路径"}`（必填）
- `vega write` — 创建新条目。`{"path", "description", "tags", "content"}`（均必填）。同路径已存在时报错，用 edit 修改。写入新项目时自动创建 `_index.md`
- `vega edit` — 编辑已有条目。`{"path", "old", "new"}`（必填），`replace_all`（可选，默认 false）
- `vega delete` — 删除条目。`{"path": "路径"}`（必填）
- `vega list` — 列出条目。`{"prefix": "路径前缀"}`（可选）。可不传 JSON，直接 `vega list`
- `vega check` — 知识库自检。可不传 JSON
- `vega rebuild` — 全量扫描。可不传 JSON

路径均为相对于 data/ 的相对路径，需带 `.md` 后缀。

## 写入规范

- description 和 tags 必填
- description：一到两句话概括内容，AI 只看这个判断是否需要读正文
- tags：用名词或名词短语，具体可搜索，同时标中英文（如 `Python, 并发, async`）
- 存意图不存实现，不存具体代码

## 目录

- `projects/<项目名>/` — 项目记忆，项目名与 git 仓库名保持一致
- `user/` — 个人偏好和配置

## 首次使用

如果 `vega` 命令报错提示未初始化，运行 `vega init --help` 查看初始化方式。
