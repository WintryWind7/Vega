# Vega CLI 设计思路

## 定位

CLI 是给 AI 用的接口，不是给人类的。人类直接操作 Markdown 文件。

交互模型：

```
人类 ←→ Markdown 文件 ←→ AI（通过 CLI/MCP）
```

## 安装与分发

使用 `uv` 作为分发工具，`uv tool install` 安装后全局可用。

## 配置

首次使用需 `vega init --data <路径>` 初始化，data 目录的绝对路径保存在 `~/.vega/settings.json`。后续命令自动读取配置，无需重复指定。

## 命令

所有命令输出 JSON 格式。

| 命令 | 用途 |
|---|---|
| `vega init --data <路径>` | 初始化知识库，创建目录结构和索引，必须指定 data 路径 |
| `vega list [前缀]` | 列出条目，可按路径前缀过滤 |
| `vega search <关键词>` | 搜索索引，逗号分隔多关键词，按标题/标签/描述匹配 |
| `vega read <路径>` | 读取完整条目 |
| `vega write <路径>` | 写入条目，正文从 stdin 读取；已有条目为增量修改 |
| `vega delete <路径>` | 删除条目 |
| `vega rebuild` | 全量重建索引 |

## 接口设计原则

- 输出 JSON 格式，方便 AI 解析
- 命令简洁直观，AI 看命令名就能理解用途
- 写入已有条目时为增量修改：只更新传入的字段，正文追加而非覆盖
- 新建条目时 description 和 tags 必填
