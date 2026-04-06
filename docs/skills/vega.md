---
name: vega
description: Vega 知识库操作，用于搜索、读写跨项目知识
---

当需要存储或检索跨项目知识、个人偏好、设计经验时，使用 Vega CLI。

## 命令

通过 bash 执行以下命令：

- `vega search "关键词, 关键词"` — 搜索知识库条目，逗号分隔多关键词，匹配标题、标签、描述和路径（不搜正文）
- `vega search --project "关键词"` — 搜索项目，匹配项目名、remote、description
- `vega read <路径>` — 读取条目，输出 md 原文
- `vega write <路径> --description "描述" --tags "标签1,标签2"` — 创建新条目，正文从 stdin 读取。写入新项目时自动创建 `_index.md`
- `vega edit <路径> --old "原文本" --new "新文本"` — 编辑已有条目，精确字符串替换。匹配多处时用 `--replace-all`
- `vega delete <路径>` — 删除条目

路径均为相对于 data/ 的相对路径。

## 写入规范

- description 和 tags 必填
- description：一到两句话概括内容，AI 只看这个判断是否需要读正文
- tags：使用具体可搜索的标签，同时标注中英文（如 `Python, 并发, async`）
- 存意图不存实现，不存具体代码

## 目录

- `projects/<项目名>/` — 项目记忆，项目名与 git 仓库名保持一致
- `user/` — 个人偏好和配置

## 首次使用

如果 `vega` 命令报错提示未初始化，运行 `vega init --help` 查看初始化方式。
