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

| 命令 | 输出格式 | 用途 | 索引同步 |
|---|---|---|---|
| `vega init --data <路径>` | JSON | 初始化知识库 | — |
| `vega search <关键词>` | 可读列表 | 搜索条目索引，逗号分隔多关键词，广泛召回 | 查索引 |
| `vega search --project <关键词>` | 可读列表 | 搜索项目，匹配项目名、remote、description | 查 _index.md |
| `vega read <路径>` | md 原文 | 读取完整条目（含 frontmatter 和正文） | — |
| `vega write <路径>` | JSON | 创建新条目，description 和 tags 必填，正文从 stdin 读取 | 自动更新 |
| `vega edit <路径>` | JSON | 编辑已有条目，--old/--new 精确字符串替换 | 自动更新 |
| `vega delete <路径>` | JSON | 删除条目 | 自动更新 |
| `vega check` | 可读文本 | 知识库自检（格式、键统计、索引一致性） | — |
| `vega help` | 可读文本 | 显示完整命令列表 | — |

write、edit、delete 三个写操作会自动更新索引，AI 无需手动维护索引。

### 项目定义文件

每个项目目录下有 `_index.md`，存储项目元信息（name、remote、description），不参与索引和自检。

- write 到新项目目录时自动创建，只填 name，remote 和 description 留空
- AI 收到提示后使用 edit 补充信息
- `search --project` 直接扫描 `_index.md` 进行匹配

## 接口设计原则

- 写操作（write/edit/delete）输出 JSON，read 输出 md 原文，search 和 check 输出可读文本
- 命令简洁直观，AI 看命令名就能理解用途
- write 创建新条目，edit 编辑已有条目，职责分离
- edit 为精确字符串替换（--old/--new），AI 判断替换什么，灵活可控
- 新建条目时 description 和 tags 必填
- search 广泛召回，返回最多 50 条候选结果，精确筛选交给 AI
- search --project 提供项目级搜索，匹配 _index.md 中的 name/remote/description
- 不封装为 MCP tool，AI 统一通过 bash 调用

## 备份同步

write、edit、delete 触发 git commit，按日/月/main 分支策略自动提交。备份为可选功能，用户配置远程仓库后通过 push 备份。
