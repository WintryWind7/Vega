# 索引方案

## 决策

Vega 使用 `data/index.json` 持久索引存储条目元数据。write/edit/delete 时同步更新索引，search 和 list 从索引读取。

## 背景

早期版本维护 index.json，后改为即时扫描（无索引方案）。实测后发现加回索引更合理：

- AI 所有操作都走 Vega CLI，一致性风险低
- 即时扫描每次都要解析所有文件的 frontmatter，文件增多后不优雅
- `load_index` 名义上"加载索引"实际每次扫描，名不副实

## 索引结构

```json
{
  "entries": [
    {
      "path": "projects/Vega/async.md",
      "title": "async",
      "description": "Python 异步编程",
      "tags": ["Python", "async", "并发"]
    }
  ]
}
```

## 同步机制

- **write**：写入文件后调 `add_or_update` 同步索引
- **edit**：替换后重新解析文件，调 `add_or_update` 更新索引
- **delete**：删除文件后调 `remove` 移除索引
- **rebuild**：全量扫描重建索引，修复不一致

## 一致性保障

- `vega check` 检查索引一致性：对比 index.json 和实际文件，报告缺失或多余的条目
- `vega rebuild` 全量重建，修复任何不一致
- 如果人类直接编辑了文件，运行 rebuild 即可同步

## 性能

个人知识库通常几十到几百个条目，索引 JSON 读取几乎零成本。即使即时扫描也在毫秒级（200 条目 0.015s），索引的优势主要在架构清晰而非性能。
