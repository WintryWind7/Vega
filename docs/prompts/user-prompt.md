# Vega 知识库

我为你配置了一个外置知识库 Vega，用于跨项目持久存储和检索知识。你可以通过 bash 调用 `vega` 命令操作。

## 什么时候用

- 需要记住跨项目的知识（设计决策、踩坑经验、技术偏好）
- 需要检索过去记录的知识
- 需要存储用户的个人偏好或配置习惯

## 目录结构

所有路径相对于知识库根目录（data/）：

- `projects/<项目名>/` — 项目记忆，按项目名建子目录
- `user/` — 个人偏好和配置

路径示例：`projects/Vega/async-programming.md`、`user/editor-preferences.md`

## 命令

通过 bash 执行以下命令（路径均为相对于 data/ 的相对路径）：

- `vega search "关键词, 关键词"` — 搜索知识库条目，逗号分隔多关键词。
- `vega search --project "关键词"` — 搜索项目，匹配项目名、remote、description
- `vega write <路径> --description "描述" --tags "标签1,标签2"` — 创建新条目，正文从 stdin 读取（用 `printf "正文" | vega write ...`）。写入新项目时自动创建 `_index.md`

## 写入规范

- description 和 tags 必填
- description：一到两句话概括内容，你只看这个判断是否需要读正文
- tags：具体可搜索，同时标中英文（如 `Python, 并发, async`）
- 存意图不存实现，不存具体代码

## 首次使用

如果 `vega` 命令报错提示未初始化，运行 `vega init --help` 查看初始化方式。
