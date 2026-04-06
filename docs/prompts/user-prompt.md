# Vega 知识库

我为你配置了一个外置知识库 Vega，用于跨项目持久存储和检索知识。你可以通过 bash 调用 `vega` 命令操作。

## 什么时候用

- 需要记住跨项目的知识（设计决策、踩坑经验、技术偏好）
- 需要检索过去记录的知识
- 需要存储用户的个人偏好或配置习惯

## 目录结构

所有路径相对于知识库根目录（data/）：

- `projects/<项目名>/` — 项目记忆，项目名与 git 仓库名保持一致
- `user/` — 个人偏好和配置

路径示例：`projects/Vega/async-programming.md`、`user/editor-preferences.md`

## 命令

通过 bash 执行以下命令（路径均为相对于 data/ 的相对路径，需带 .md 后缀）：

- `vega search "关键词, 关键词"` — 搜索知识库条目，逗号分隔多关键词（OR 关系，子串匹配），匹配标题、标签、描述和路径，不搜正文
- `vega list [路径前缀]` — 列出指定目录下的条目，如 `vega list projects/Vega` 或 `vega list user`。无参数时列出全部
- `vega search --project "项目名"` — 模糊搜索项目，不确定项目名时使用
- `vega read <路径>` — 读取条目，输出 md 原文
- `vega write <路径> --description "描述" --tags "标签1,标签2"` — 创建新条目，正文从 stdin 读取。同路径已存在时会报错，应用 edit 修改。写入新项目时自动创建 `_index.md`
- `vega edit <路径>` — 编辑已有条目，stdin 读取 JSON 格式的替换内容。JSON 必须包含 `old` 和 `new` 字段，可选 `replace_all` 字段。示例：`vega edit path <<< '{"old": "旧文本", "new": "新文本"}'`
- `vega delete <路径>` — 删除条目

## 写入规范

- description 和 tags 必填
- description：一到两句话概括内容，你只看这个判断是否需要读正文
- tags：用名词或名词短语，具体可搜索，同时标中英文（如 `Python, 并发, async`）
- 存意图不存实现，不存具体代码

## 首次使用

如果 `vega` 命令报错提示未初始化，运行 `vega init --help` 查看初始化方式。
