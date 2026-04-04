# Vega — AI Agent 指引

## 项目简介

Vega 是一个 AI 优先的个人知识库，用于跨项目持久存储和检索知识。主要读写方是 AI，人偶尔介入。

详细的设计理念和决策记录在以下文档中：

- [设计理念](design/philosophy.md) — 为什么这样设计，痛点是什么
- [探讨过的方式](design/approaches.md) — 考虑过哪些方案，为什么选择现在的方案
- [文档规范](design/document-spec.md) — 知识条目的格式定义
- [CLI 设计思路](design/cli-design.md) — 接口设计原则

## 知识库结构

知识库数据位于 `data/` 目录（不纳入版本控制）：

```
data/
  index.json       # 元数据索引（自动维护）
  projects/        # AI 存储的项目记忆（按项目名分目录）
  user/            # 用户的个人偏好和文档
```

## 操作要点

- 每个知识条目是一个 Markdown 文件，包含 YAML frontmatter（description、tags）和正文，标题从文件名推断
- 通过 CLI 命令进行操作，首次使用需 `vega init --data <路径>` 初始化，路径保存在 `~/.vega/settings.json`
- 写入和删除时索引会自动更新，写入已有条目时为增量修改
- 人可以直接编辑 Markdown 文件，不影响使用
