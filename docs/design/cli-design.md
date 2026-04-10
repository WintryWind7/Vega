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

首次使用需 `vega init` 初始化，data 目录路径通过 stdin JSON 传入，保存在 `~/.vega/settings.json`。后续命令自动读取配置，无需重复指定。不支持 `--data` 参数覆盖，统一靠 init 配置。

## 输入方式

所有命令统一通过 stdin 读取 JSON 参数。空 stdin 等同于 `{}`，因此全部字段可选的命令（如 `vega list`）和无字段命令（`vega check`、`vega rebuild`）可以不传 JSON 直接运行。

统一 stdin JSON 的理由：
- 避开 shell 参数转义问题，与 AI 的 function_call 模型一致
- 文档只需说明一次输入格式，各命令只列 JSON 字段
- 可扩展性好，加字段不影响 CLI 接口

## 命令

| 命令 | 输出格式 | stdin JSON 必填字段 | stdin JSON 可选字段 |
|---|---|---|---|
| `vega init` | JSON | data | — |
| `vega search` | 可读列表 | query | limit（默认 50）、type（默认 "file"，可选 "project"） |
| `vega read` | md 原文 | path | — |
| `vega write` | JSON | path、description、tags、content | — |
| `vega edit` | JSON | path、old、new | replace_all（默认 false） |
| `vega delete` | JSON | path | — |
| `vega move` | JSON | from、to | — |
| `vega list` | 可读列表 | — | prefix（默认空） |
| `vega check` | 可读文本 | — | — |
| `vega rebuild` | JSON | — | — |
| `vega help` | 可读文本 | — | — |

write、edit、delete 同步维护索引，search 从索引读取。详见[索引方案](index.md)。

## 接口设计原则

- 每个项目目录下有 `_index.md`，存储项目元信息（name、remote、description），不参与索引和自检。write 到新项目目录时自动创建，AI 收到提示后使用 edit 补充信息
- 所有命令通过 stdin JSON 传入参数，无 CLI 位置参数或选项
- 写操作（init/write/edit/delete/move/rebuild）输出 JSON，read 输出 md 原文，search、list 和 check 输出可读文本
- 命令简洁直观，AI 看命令名就能理解用途
- write 创建新条目，edit 编辑已有条目，职责分离
- edit 使用精确字符串替换（old/new/replace_all），与 AI 内置 Edit 工具设计思路一致
- search 即时扫描所有文件，无持久索引，无一致性问题
- 新建条目时 description 和 tags 必填
- search 广泛召回，返回最多 50 条候选结果，精确筛选交给 AI。多关键词 OR 关系，子串匹配
- write 同路径已存在时报错，AI 应使用 edit 修改
- search `type: "project"` 提供项目级搜索，匹配 _index.md 中的 name/remote/description；默认 `type: "file"` 搜条目
- 不封装为 MCP tool，AI 统一通过 bash 调用
- 不提供 --data 参数覆盖，数据目录统一由 init 配置

## 设计记录

### search 不输出根目录路径

search 输出只包含匹配结果列表，不输出 `vega data path`、查询关键字回显、路径格式说明等头部信息。理由：

- search 的职责是返回匹配结果，路径格式已在提示词中说明
- 如果 CLI 能用 search，read 也应该能用，不存在"search 成功但 read 失败需要降级"的真实场景
- 如果将来确实需要降级通道（AI 绕过 CLI 直接读文件），可通过新增 `vega config` 命令按需获取根目录路径

### 统一 stdin JSON 输入

早期版本混合使用 CLI 参数和 stdin：write 用 `--description`/`--tags` 参数 + stdin 正文，edit 用 `--old`/`--new` 参数。后改为 edit stdin JSON 解决 shell 转义问题，最终统一所有命令为 stdin JSON。

统一 stdin JSON 的考量：
- AI 的 function_call 本身就是 JSON 参数模型，stdin JSON 与之一致
- write 的正文放 JSON content 字段时需要 JSON 转义，但这和 AI 使用内置 Edit 工具时的转义完全相同，不构成实际困难
- 统一格式后文档只需说明一次"stdin JSON"，各命令只列字段，减少维护成本

### tags 的定位：中英文对照的搜索桥梁

tags 的核心价值是解决中英文语义鸿沟。description 用中文撰写，但搜索时可能用英文关键词（如搜 "editor" 而非 "编辑器"）。tags 要求同时标中英文，让子串匹配就能跨语言检索。

tags 不是冗余字段：
- description 写的是"讲什么"，tags 写的是"别人可能用什么词搜到它"——不同视角
- description 限制一到两句话，不可能覆盖所有同义词和中英文对照
- tags 在搜索中权重高于 description（+2 vs +1），标注核心主题

不使用向量索引做语义搜索的理由：
- Vega 定位纯 Markdown + 纯标准库，引入向量索引与"易迁移"理念冲突
- 知识库体量（几十到几百条），全文搜索 + tags 标注足够

### search 结果不含匹配位置指示

搜索结果只显示 `path: description`，不标注关键词命中了哪个字段（title/tags/description/path）。

理由：
- description 本身就是预览，AI 看到就能判断相关性
- Vega 的设计是广泛召回 + AI 自行筛选，不确定时 read 正文确认
- 标注匹配位置增加输出复杂度，对 AI 判断相关性的实际帮助有限
