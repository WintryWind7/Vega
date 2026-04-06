# Vega — AI Agent 指引

## 项目简介

Vega 是一个 AI 优先的个人知识库，用于跨项目持久存储和检索知识。主要读写方是 AI，人偶尔介入。

详细的设计理念和决策记录在以下文档中：

- [使用说明](usage.md) — 安装、命令用法、AI 接入方式
- [设计理念](design/philosophy.md) — 为什么这样设计，痛点是什么
- [探讨过的方式](design/approaches.md) — 考虑过哪些方案，为什么选择现在的方案
- [无索引方案](design/indexless.md) — 为什么去掉持久索引，性能数据
- [文档规范](design/document-spec.md) — 知识条目的格式定义
- [CLI 设计思路](design/cli-design.md) — 接口设计原则

## 知识库结构

知识库数据位于 `data/` 目录（不纳入版本控制）：

```
data/
  projects/        # AI 存储的项目记忆（按项目名分目录）
  user/            # 用户的个人偏好和文档
```

## 操作要点

- 每个知识条目是一个 Markdown 文件，包含 YAML frontmatter（description、tags）和正文，标题从文件名推断
- AI 通过 bash 调用 CLI 命令操作，首次使用需 `vega init --data <路径>` 初始化，路径保存在 `~/.vega/settings.json`
- search 即时扫描所有文件进行检索，无需维护索引，多关键词 OR 关系，子串匹配，不搜正文
- write 创建新条目（description 和 tags 必填，正文从 stdin 读取），同路径已存在时报错，写入新项目时自动创建 `_index.md`
- edit 从 stdin 读取 JSON 格式的替换内容（必须包含 old 和 new 字段）
- list 列出指定目录下的条目，可按路径前缀过滤
- search --project 模糊搜索项目名，不确定项目名时使用，匹配 `_index.md` 中的 name、remote、description
- 人可以直接编辑 Markdown 文件，不影响使用
