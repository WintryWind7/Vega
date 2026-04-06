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
| `vega search <关键词>` | 可读列表 | 搜索条目，逗号分隔多关键词，广泛召回（匹配标题、标签、描述、路径，不搜正文） | 即时扫描 |
| `vega search --project <关键词>` | 可读列表 | 搜索项目，匹配项目名、remote、description | 查 _index.md |
| `vega read <路径>` | md 原文 | 读取完整条目（含 frontmatter 和正文） | — |
| `vega write <路径>` | JSON | 创建新条目，description 和 tags 必填，正文从 stdin 读取 | — |
| `vega edit <路径>` | JSON | 编辑已有条目，--old/--new 精确字符串替换 | — |
| `vega delete <路径>` | JSON | 删除条目 | — |
| `vega check` | 可读文本 | 知识库自检（格式、键统计） | — |
| `vega list [路径前缀]` | 可读列表 | 列出指定目录下的条目 | 即时扫描 |
| `vega help` | 可读文本 | 显示完整命令列表 | — |

write、edit、delete 无需维护索引，search 即时扫描文件。详见[无索引方案](indexless.md)。

### 项目定义文件

每个项目目录下有 `_index.md`，存储项目元信息（name、remote、description），不参与索引和自检。

- write 到新项目目录时自动创建，只填 name，remote 和 description 留空
- AI 收到提示后使用 edit 补充信息
- `search --project` 直接扫描 `_index.md` 进行匹配

## 接口设计原则

- 写操作（write/edit/delete）输出 JSON，read 输出 md 原文，search、list 和 check 输出可读文本
- 命令简洁直观，AI 看命令名就能理解用途
- write 创建新条目，edit 编辑已有条目，职责分离
- edit 为精确字符串替换（--old/--new），AI 判断替换什么，灵活可控
- search 即时扫描所有文件，无持久索引，无一致性问题
- 新建条目时 description 和 tags 必填
- search 广泛召回，返回最多 50 条候选结果，精确筛选交给 AI。多关键词 OR 关系，子串匹配
- write 同路径已存在时报错，AI 应使用 edit 修改
- search --project 提供项目级搜索，匹配 _index.md 中的 name/remote/description
- 不封装为 MCP tool，AI 统一通过 bash 调用

## 备份同步

write、edit、delete 触发 git commit，按日/月/main 分支策略自动提交。备份为可选功能，用户配置远程仓库后通过 push 备份。

## 设计记录

### search 不输出根目录路径

search 输出只包含匹配结果列表，不输出 `vega data path`、查询关键字回显、路径格式说明等头部信息。理由：

- search 的职责是返回匹配结果，路径格式已在提示词中说明
- 如果 CLI 能用 search，read 也应该能用，不存在"search 成功但 read 失败需要降级"的真实场景
- 如果将来确实需要降级通道（AI 绕过 CLI 直接读文件），可通过新增 `vega config` 命令按需获取根目录路径
