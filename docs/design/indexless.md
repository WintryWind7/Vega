# 无索引方案

## 决策

Vega 不使用 index.json 索引文件，search 命令直接扫描 .md 文件、解析 frontmatter 进行匹配。

## 背景

原始方案维护 index.json 存储条目元数据，write/edit/delete 时同步更新索引。这带来了几个问题：

- AI 直接编辑文件时（用自身工具），索引会过时，需要额外同步机制
- 增加了 edit 命令的必要性（否则无法同步索引）
- 索引一致性需要 check 命令专门检查

去掉索引后：
- write 只写文件，edit 可由 AI 自身工具替代
- 无一致性问题
- 架构大幅简化

## 性能

基准测试结果（Windows，直接扫描所有 .md 文件解析 frontmatter）：

| 文件数 | 搜索耗时 |
|--------|----------|
| 50 | 0.004s |
| 200 | 0.015s |
| 2,000 | 0.13s |
| 20,000 | 1.7s |
| 200,000 | 15.2s |

个人知识库通常几十到几百个条目，搜索耗时在毫秒级，完全无感知。

## 影响

- **去掉**：index.json、index 模块、rebuild 命令、list 命令、check 中的索引一致性检查
- **简化**：write（只写文件）、delete（只删文件）、search（直接扫描）
- **init**：不再创建 index.json
- **edit**：AI 可直接用自身工具编辑文件，无需 vega edit 同步索引
- **check**：只检查 frontmatter 格式和必填字段
