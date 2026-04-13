# Vega 知识库

我为你配置了一个外置知识库 Vega，用于跨项目持久存储和检索知识。你可以通过 bash 调用 `vega` 命令操作。

## 什么时候读

- 新话题或新任务开始时，先搜一下有没有相关记录
- 用户提到"之前记过"、"上次说过"时搜索
- 不确定用户偏好或历史决策时，搜索相关关键词

## 什么时候写

- 用户明确要求存到 Vega 时，直接写
- 任务完成或提交后，主动询问是否需要将过程中的设计决策、踩坑经验等写入 Vega，给出建议的 path 和内容
- 长讨论得出有价值结论后，主动询问是否需要记录

不要自己决定写入。每次写入都应经过用户确认。

## 什么不该存

- 代码片段或具体实现细节 — 代码本身就是记录
- git 历史、recent changes — `git log` 是权威来源
- 调试过程和临时状态 — 对话结束就过期
- 项目结构、文件路径、约定 — 可以从代码直接看到

## 目录结构

所有路径相对于知识库根目录（data/）：

- `projects/<项目名>/` — 项目相关知识，项目名与 git 仓库名保持一致
- `user/` — 个人偏好和配置

路径示例：`projects/Vega/async-programming.md`、`user/editor-preferences.md`

## 写入规范

description 和 tags 必填。

### 写入流程

write 或 edit 前先搜索是否已有相关条目或项目目录，避免重复或分散存储。如果不确定要存什么，或认为存的内容与写入规范有冲突，向用户询问以确保充分理解意图。

### 粒度

一个条目围绕一个方面——一个设计决策、一个踩坑经验、一组相关偏好。当一个条目的内容超出 description 能概括的范围时，应拆分为多个条目。

### description

写这条记录讲了什么。description 是搜索结果的唯一预览，AI 靠它判断是否需要 read 正文。因此要足够具体：`Python asyncio 中 gather 与 TaskGroup 的区别和选坑经验` 比 `关于 Python 异步的笔记` 有用。包含具体实现时需注明，如 `包含原子写入的具体实现`。

### tags

从内容中提取专业术语和核心技术概念，中英文标注。tags 的作用是跨语言检索：description 里写了"异步"，tags 补上 `async`。

### body

记录设计意图、决策原因、关键认知。不存具体代码，除非实现本身独特且值得保留（例如分析源码、code review 时记录的实现），此时 description 需注明包含实现。

### 文件排布

projects/ 按项目名分目录，一个条目一个文件。user/ 按主题分文件，内容少的偏好可以合并在一个文件里。

## 条目可能过时

条目是写入时的快照，内容可能已变化。对关键信息（路径、函数名、配置值）使用前应验证当前状态。

## 命令

所有命令通过 stdin 读取 JSON 参数。有必填字段的命令必须传入 JSON；全部字段可选或无字段的命令可以不传。

| 命令 | 必填字段 | 可选字段 | 说明 |
|---|---|---|---|
| `vega search` | query | limit（默认 50）、type（默认 "file"，可选 "project"）、mode（默认 "and"，可选 "or"） | 搜索条目，query 逗号分隔多关键词，默认要求所有关键词都匹配 |
| `vega read` | path | — | 读取条目，输出 md 原文 |
| `vega write` | path、description、tags、content | — | 创建新条目。已存在时报错，用 edit 修改。写入新项目时自动创建 `_index.md` |
| `vega edit` | path、old、new | replace_all（默认 false） | 编辑已有条目，精确字符串替换 |
| `vega delete` | path | — | 删除条目（`.md` 后缀）或项目（路径以 `/` 结尾） |
| `vega move` | from、to | — | 移动/重命名条目或项目 |
| `vega list` | — | prefix（默认空） | 列出条目，可不传 JSON |

路径示例：`projects/Vega/async.md`。不确定路径时用 search 或 list 查看已有条目的路径格式。

不确定命令用法时用 `vega <command> --help` 查看详细说明。如遇未知错误可以尝试 `vega help`。
