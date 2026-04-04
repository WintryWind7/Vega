# Vega CLI 设计思路

## 定位

CLI 是给 AI 用的接口，不是给人类的。人类直接操作 Markdown 文件。

交互模型：

```
人类 ←→ Markdown 文件 ←→ AI（通过 bash 调用 CLI）
```

AI 通过 bash 工具执行 `vega` 命令，不需要封装为 MCP tool。接入方式为 skill 或 CLAUDE.md 中写明命令用法。

## 安装与分发

使用 `uv` 作为分发工具，`uv tool install` 安装后全局可用。

## 配置

首次使用需 `vega init --data <路径>` 初始化，data 目录的绝对路径保存在 `~/.vega/settings.json`。后续命令自动读取配置，无需重复指定。

## 命令

所有命令输出 JSON 格式（check 除外，输出可读文本）。

| 命令 | 用途 | 索引同步 |
|---|---|---|
| `vega init --data <路径>` | 初始化知识库 | — |
| `vega search <关键词>` | 搜索索引，逗号分隔多关键词，广泛召回 | 查索引 |
| `vega read <路径>` | 读取完整条目 | — |
| `vega write <路径>` | 创建新条目，description 和 tags 必填 | 自动更新 + git commit |
| `vega edit <路径>` | 编辑已有条目，增量修改 | 自动更新 + git commit |
| `vega delete <路径>` | 删除条目 | 自动更新 + git commit |
| `vega check` | 知识库自检（格式、键统计、索引一致性） | — |

write、edit、delete 三个写操作会自动更新索引并触发 git commit，AI 无需手动维护索引。

## 接口设计原则

- 输出 JSON 格式（check 除外，输出可读文本）
- 命令简洁直观，AI 看命令名就能理解用途
- write 创建新条目，edit 编辑已有条目，职责分离
- edit 为增量修改：只改传入的字段，正文追加而非覆盖
- 新建条目时 description 和 tags 必填
- search 广泛召回，返回最多 50 条候选结果，精确筛选交给 AI
- 不封装为 MCP tool，AI 统一通过 bash 调用

## 备份同步

write、edit、delete 触发 git commit，按日/月/main 分支策略自动提交。备份为可选功能，用户配置远程仓库后通过 push 备份。
