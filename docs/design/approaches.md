# Vega 过程中探讨过的方式

## 编程语言

考虑过 Go、Rust、Node.js、Python。

最终选择 Python：几乎所有环境自带，无需编译，后期 GUI 扩展方便。

性能不是本项目的瓶颈，语言选择不影响检索方案。

## 安装分发

考虑过 `pip install -e .`、`pipx`、手动加 PATH、初始化脚本。

最终选择 `uv tool install`：uv 自动管理隔离环境和 Python，不污染全局，用户只需安装 uv 即可。

## 检索方案

考虑过文件直接扫描、轻量索引、SQLite FTS5。

选择 JSON 索引方案：维护一个索引文件存储所有条目的元数据摘要（path、title、description、tags），写入和删除时自动更新索引，检索时先查索引再读正文。提供全量重建索引的能力。

后期可扩展 MD 格式索引（给 AI 直接阅读）和内置 agent 自动维护。
