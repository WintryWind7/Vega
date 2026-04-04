---
name: vega
description: Vega 知识库操作，用于搜索、读写跨项目知识
---

当需要存储或检索跨项目知识、个人偏好、设计经验时，使用 Vega CLI。

## 命令

通过 bash 执行以下命令：

- `vega search "关键词, 关键词"` — 搜索知识库，逗号分隔多关键词，广泛召回，返回按相关度排序的结果
- `vega read <路径>` — 读取完整条目（结构化 JSON，frontmatter 与正文分开）
- `vega write <路径> -d "描述" -t "标签1,标签2"` — 创建新条目，正文从 stdin 读取
- `vega edit <路径>` — 编辑已有条目，支持修改 description、tags、追加正文
- `vega delete <路径>` — 删除条目
- `vega check` — 知识库自检，输出格式问题、键统计、索引一致性报告

write、edit、delete 会自动更新索引，无需手动 rebuild。

## 写入规范

- description 和 tags 必填
- description：一到两句话概括内容，AI 只看这个判断是否需要读正文
- tags：使用具体可搜索的标签，同时标注中英文（如 `Python, 并发, async`）
- 存意图不存实现，不存具体代码

## 目录

- `projects/<项目名>/` — 项目记忆，按项目名建子目录
- `user/` — 个人偏好和配置

## 首次使用

如果 `vega` 命令报错提示未初始化，运行：
```bash
vega init --data <知识库路径>
```
