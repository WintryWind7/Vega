# Vega 使用说明

## 安装

需要先安装 [uv](https://docs.astral.sh/uv/)，然后：

```bash
# 开发模式（改代码立即生效）
uv tool install -e .

# 正式安装
uv tool install .
```

安装后 `vega` 命令全局可用。

## 初始化

```bash
vega init <<< '{"data": "/path/to/data"}'
```

这会做两件事：
1. 创建 `data/projects/` 和 `data/user/` 目录
2. 将 data 目录的绝对路径写入 `~/.vega/settings.json`

后续所有命令自动读取配置，无需再指定路径。

## 命令参考

所有命令通过 stdin 读取 JSON 参数。有必填字段的命令必须传入 JSON；全部字段可选或无字段的命令可以不传。

### vega init

初始化知识库。

| 字段 | 必填 | 说明 |
|---|---|---|
| data | 是 | 知识库路径 |

```bash
vega init <<< '{"data": "~/vega-data"}'
```

### vega search

搜索条目，逗号分隔多关键词，默认 AND 关系（所有关键词都匹配才返回），`"mode": "or"` 切换为任一匹配。从索引读取，按标题（权重 3）、标签（权重 2）、描述和路径（权重 1）匹配，不搜正文。子串匹配，评分降序排列。

`"type": "project"` 时模糊搜索项目名而非条目，不确定项目名时使用。匹配 `_index.md` 中的 name（权重 3）、remote（权重 2）、description（权重 1）。

| 字段 | 必填 | 说明 |
|---|---|---|
| query | 是 | 搜索关键词，逗号分隔多关键词 |
| mode | 否 | 匹配模式，"and"（默认）或 "or" |
| limit | 否 | 最大返回条数，默认 50 |
| type | 否 | 搜索类型，"file"（条目，默认）或 "project"（项目） |

```bash
vega search <<< '{"query": "editor"}'
vega search <<< '{"query": "Python, async", "limit": 20}'
vega search <<< '{"query": "Vega", "type": "project"}'
```

### vega read

读取完整条目，直接输出 md 原文（含 frontmatter 和正文）。

| 字段 | 必填 | 说明 |
|---|---|---|
| path | 是 | 条目路径（相对于 data/，需带 .md 后缀） |

```bash
vega read <<< '{"path": "user/editor-preferences.md"}'
```

### vega write

创建新条目。同路径已存在时会报错，应用 edit 修改。写入新项目目录时自动创建 `_index.md`。

| 字段 | 必填 | 说明 |
|---|---|---|
| path | 是 | 条目路径（相对于 data/，需带 .md 后缀） |
| description | 是 | 条目描述 |
| tags | 是 | 标签数组 |
| content | 是 | 正文内容 |

```bash
vega write <<< '{"path": "projects/Vega/async.md", "description": "Python 异步编程", "tags": ["Python", "async", "并发"], "content": "# Python async\n\nasyncio 核心概念"}'
```

### vega edit

编辑已有条目，精确字符串替换。

| 字段 | 必填 | 说明 |
|---|---|---|
| path | 是 | 条目路径（相对于 data/，需带 .md 后缀） |
| old | 是 | 要替换的文本 |
| new | 是 | 替换后的文本 |
| replace_all | 否 | 替换所有匹配，默认 false |

```bash
# 单次替换
vega edit <<< '{"path": "projects/Vega/async.md", "old": "旧描述", "new": "新描述"}'

# 批量替换
vega edit <<< '{"path": "projects/Vega/async.md", "old": "旧词", "new": "新词", "replace_all": true}'
```

### vega delete

删除条目或整个项目。删除条目时返回被删条目的完整内容（便于确认删对了）；删除项目时返回 `entries_deleted` 计数。

| 字段 | 必填 | 说明 |
|---|---|---|
| path | 是 | 条目路径（需带 .md 后缀）或项目路径 |

```bash
vega delete <<< '{"path": "projects/Vega/old-note.md"}'
vega delete <<< '{"path": "projects/OldProject/"}'
```

### vega move

移动或重命名条目/项目。目标路径已存在时报错。项目重命名会同步更新 `_index.md` 中的 name 和索引中所有受影响条目的路径。

| 字段 | 必填 | 说明 |
|---|---|---|
| from | 是 | 源路径 |
| to | 是 | 目标路径 |

```bash
vega move <<< '{"from": "projects/Vega/async.md", "to": "projects/Vega/concurrency.md"}'
vega move <<< '{"from": "projects/Vega/", "to": "projects/Vega2/"}'
vega move <<< '{"from": "user/note.md", "to": "projects/Vega/note.md"}'
```

### vega list

列出指定目录下的条目，输出可读列表（序号、路径、描述）。

| 字段 | 必填 | 说明 |
|---|---|---|
| prefix | 否 | 路径前缀过滤，不填列出全部 |

```bash
vega list
vega list <<< '{"prefix": "projects/Vega"}'
vega list <<< '{"prefix": "user"}'
```

### vega check

知识库自检，输出可读文本报告。无需传入 JSON。检查两项：
- 格式问题：frontmatter 是否完整、必填字段是否存在
- 键统计：所有条目的 frontmatter 键是否一致

```bash
vega check
```

### vega rebuild

全量扫描，返回条目数。无需传入 JSON。

```bash
vega rebuild
```

## 备注

人可以直接编辑 Markdown 文件，不影响使用。Vega 维护 `data/index.json` 持久索引，write/edit/delete 会自动同步；人直接改过文件后运行 `vega rebuild` 重建即可。`vega check` 可校验索引与实际文件是否一致。

## 知识库结构

```
data/
  index.json       # 条目索引，由 CLI 自动维护
  projects/        # AI 存储的项目记忆
    <项目名>/
      _index.md    # 项目元信息（name、remote、description），不参与索引
      *.md
  user/            # 用户的个人偏好
    *.md
```

### 条目格式

每个条目是一个 Markdown 文件，由 frontmatter 和正文组成：

```markdown
---
description: 一到两句话概括内容
tags: [标签1, 标签2, 标签3]
---

正文内容，标准 Markdown 格式。
```

- **description**（必填）：条目摘要，用于索引和检索
- **tags**（必填）：标签列表，用于交叉索引
- 标题从文件名推断，不需要单独设字段
- frontmatter 分隔符支持 `>=3` 个 `-`

## AI 接入（以 Claude Code 为例）

Vega 的 CLI 是给 AI 用的接口。AI 需要知道 `vega` 命令的存在和用法，接入方式取决于具体平台。以 Claude Code 为例：

项目中提供了 `docs/skills/vega.md`，这是一个完整可用的 skill 文件。将其复制到 Claude Code 的 skills 目录即可：

```bash
cp docs/skills/vega.md ~/.claude/skills/vega.md
```

其他 AI 平台的接入方式类似：将 Vega 的命令用法写入 AI 能读取的配置文件或提示词中。

## 最佳实践

### tags 怎么写

- 使用具体、可搜索的标签，避免太泛（如 "笔记"）
- 用名词或名词短语，不用动词和形容词（如 `Python` 而非 `学习Python`）
- 同时标注中英文标签，方便不同语言搜索：`tags: [Python, 并发, async]`
- 标注领域和技术栈：`tags: [React, 前端, 状态管理]`

### description 怎么写

- 一到两句话概括，不要写正文里才有的细节
- 假设 AI 只看 description 判断是否需要读正文
- 好的写法：`Python 异步编程的核心概念，包括 async/await、事件循环、协程`
- 差的写法：`一些笔记`

### 目录怎么组织

- `projects/<项目名>/` — 每个项目一个目录，项目名与 git 仓库名保持一致
- `user/` — 个人偏好、配置信息，内部自由组织
- 文件名即标题，用可读的名字：`async-programming.md` 或 `异步编程.md`，路径需带 `.md` 后缀
