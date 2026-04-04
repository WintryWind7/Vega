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
vega init --data /path/to/data
```

这会做三件事：
1. 创建 `data/projects/` 和 `data/user/` 目录
2. 创建空的 `data/index.json` 索引文件
3. 将 data 目录的绝对路径写入 `~/.vega/settings.json`

后续所有命令自动读取配置，无需再指定路径。

## 命令参考

所有命令输出 JSON 格式（check 除外，输出可读文本）。AI 通过 bash 调用。

### vega init --data \<路径\>

初始化知识库。必须指定 `--data`，这是唯一需要指定路径的命令。

```bash
vega init --data ~/vega-data
```

### vega search \<关键词\>

搜索索引，逗号分隔多关键词。按标题（权重 3）、标签（权重 2）、描述和路径（权重 1）匹配，子串匹配，广泛召回，评分降序排列。

```bash
vega search "editor"
vega search "Python, async"
vega search "编辑器" --limit 20
```

`--limit` / `-n` 控制最大返回条数，默认 50。

### vega read \<路径\>

读取完整条目，返回结构化 JSON（frontmatter 与正文分开）。

```bash
vega read user/editor-preferences.md
```

### vega write \<路径\>

创建新条目。`--description` 和 `--tags` 必填，正文从 stdin 读取。自动更新索引。

```bash
echo "# Python async\n\nasyncio 核心概念" | vega write projects/Vega/async.md -d "Python 异步编程" -t "Python,async,并发"
```

### vega edit \<路径\>

编辑已有条目。增量修改：只更新传入的字段，正文追加而非覆盖。自动更新索引。

```bash
# 改 description
vega edit projects/Vega/async.md -d "更新后的描述"

# 追加正文
echo "补充内容" | vega edit projects/Vega/async.md
```

### vega delete \<路径\>

删除条目，同时从索引中移除。

```bash
vega delete projects/Vega/old-note.md
```

### vega check

知识库自检，输出可读文本报告。检查三项：
- 格式问题：frontmatter 是否完整、必填字段是否存在
- 键统计：所有条目的 frontmatter 键是否一致
- 索引一致性：索引记录与实际文件是否一一对应、内容是否同步

```bash
vega check
```

### 内部命令

以下命令代码层面保留，但不作为外部接口暴露：

| 命令 | 用途 |
|---|---|
| `vega list` | 列出条目，可按路径前缀过滤 |
| `vega rebuild` | 全量重建索引 |

## 知识库结构

```
data/
  index.json       # 索引文件（自动维护）
  projects/        # AI 存储的项目记忆
    <项目名>/
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
- 同时标注中英文标签，方便不同语言搜索：`tags: [Python, 并发, async]`
- 标注领域和技术栈：`tags: [React, 前端, 状态管理]`

### description 怎么写

- 一到两句话概括，不要写正文里才有的细节
- 假设 AI 只看 description 判断是否需要读正文
- 好的写法：`Python 异步编程的核心概念，包括 async/await、事件循环、协程`
- 差的写法：`一些笔记`

### 目录怎么组织

- `projects/<项目名>/` — 每个项目一个目录，项目名与实际项目一致
- `user/` — 个人偏好、配置信息，内部自由组织
- 文件名即标题，用可读的名字：`async-programming.md` 或 `异步编程.md`
