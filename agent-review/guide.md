# Agent Review

Vega 的自我迭代流程。你的职责：

1. 运行测试脚本，让外部 AI（通过 opencode run）自由探索 Vega
2. 分析它的操作记录和反馈，区分真实问题和误判
3. 汇报分析结果，由用户决定是否修复以及修复哪些

迭代不是自动的——每轮分析结果都需要用户审核后才能行动。

## 目录结构

```
agent-review/
  prompts/        # 提示词，可以有多份
  results/        # 测试产物（gitignore）
  agent-review-test.sh  # 执行脚本
  guide.md        # 本文件
```

## 运行

```bash
bash agent-review/agent-review-test.sh
```

默认使用 `prompts/prompt.md`，脚本里 `PROMPT_FILE` 可指向其他提示词。

不要自己去手动调用 Vega 命令做测试，统一通过脚本让另一个 AI 来测。

## 分析

在进行分析之前，确保已充分了解项目各设计原则、为什么要这样设计等。先读 `docs/agent.md` 及其中引用的设计文档，再开始分析。

跑完后读 `results/` 下最新文件夹的内容。必须同时读 trace 和 report，不能只读 report：

- `*-report.txt` — AI 的文字总结，可能不准
- `*-trace.jsonl` — 完整的操作记录，用于验证 AI 的判断

验证每条反馈：
- 对照 trace 中的实际输入输出，确认 AI 报告的问题是否真实存在
- 结合项目的设计文档和源码理解，判断 AI 的建议是否与设计理念一致
- 区分：哪些是确认的问题，哪些是 AI 误判

## 输出

向用户汇报分析结果，包含：

- 确认的问题：附上 trace 中的证据（命令、输出、时间戳等）
- 不成立的反馈：说明为什么不成立
- 改进建议（如有）：按优先级排列

不要主动修复任何问题，等用户决定。
