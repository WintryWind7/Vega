# Vega 文档规范

## 存储结构

```
data/
  index.json           # 条目索引（自动维护）
  projects/            # AI 按项目存储的跨项目记忆
    <项目名>/
      _index.md        # 项目定义文件（name、remote、description）
      *.md             # 知识条目
  user/                # 用户的个人偏好（给 AI 恢复用）
    *.md
```

### 项目定义文件 `_index.md`

每个项目目录下可选的元信息文件，不参与索引和自检。

```yaml
---
name: claude-code
remote: https://github.com/anthropics/claude-code
description: Claude Code CLI 工具的研究笔记
---

# claude-code

项目简介。
```

- `name`：项目名，自动从目录名提取
- `remote`：git 仓库 URL，可选
- `description`：项目描述，可选
- write 到新项目目录时自动创建（只填 name），AI 使用 edit 补充

## 条目格式

每个条目为一个 Markdown 文件，由两部分组成：

### Frontmatter（元数据）

位于文件开头，用 `---`（>=3 个 `-`）包裹，格式为 YAML：

```yaml
---
description: Python 异步编程的核心概念，包括 async/await、事件循环、协程
tags: [Python, async, 并发]
---
```

只匹配文件开头和紧接着的第二个分隔符，正文中的 `---` 不受影响。

#### 字段定义

| 字段 | 必填 | 说明 |
|---|---|---|
| `description` | 是 | 条目摘要，用于索引和检索，一到两句话概括内容 |
| `tags` | 是 | 标签列表，用于交叉索引，打破目录结构的限制 |

标题从文件名推断，不再单独设置字段。

### 正文

Frontmatter 之后即为正文，使用标准 Markdown 格式，无额外约束。

## 文件命名

- 使用条目标题作为文件名，可读性好
- 文件扩展名为 `.md`

## 目录与分类

- 目录结构按用途划分：`projects/`（项目记忆）、`user/`（个人偏好）
- `projects/` 下按项目名建子目录，项目名与实际项目名称一致
- 不再使用 `category` 字段，分类信息由目录路径隐含
