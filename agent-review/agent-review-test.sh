#!/usr/bin/env bash
# Vega Agent Review — 让 AI 自由探索 Vega 并给出体验反馈
# 用法: bash agent-review/agent-review-test.sh [-n 次数]

set -euo pipefail

ROUNDS=1
while getopts "n:" opt; do
    case $opt in
        n) ROUNDS="$OPTARG" ;;
        *) ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
PROMPTS_DIR="$SCRIPT_DIR/prompts"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

mkdir -p "$RESULTS_DIR"

log()  { echo -e "${CYAN}[Agent-Review]${NC} $*"; }
ok()   { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; }

# ============================================================
# 对单个 prompt 执行测试
# ============================================================

run_one() {
    local prompt_file="$1"
    local output_dir="$2"
    local prompt_name
    prompt_name=$(basename "$prompt_file" .md)

    local stream_file="$output_dir/${prompt_name}-trace.jsonl"
    local report_file="$output_dir/${prompt_name}-report.txt"

    log "测试: $prompt_name"

    # 拼接 prompt + _ 开头的共享片段
    local combined
    combined=$(mktemp)
    cat "$prompt_file" > "$combined"
    for snippet in "$PROMPTS_DIR"/_*.md; do
        [[ -f "$snippet" ]] || continue
        echo -e "\n---\n" >> "$combined"
        cat "$snippet" >> "$combined"
    done

    # 调用 opencode run
    exit_code=0
    cat "$combined" | opencode run \
        --format json \
        2>"$output_dir/${prompt_name}-stderr.log" \
        > "$stream_file" || exit_code=$?

    rm -f "$combined"

    if [[ $exit_code -ne 0 ]]; then
        fail "$prompt_name: opencode run 退出码 $exit_code"
        return 1
    fi

    # 提取 AI 文本回复
    cat "$stream_file" | python -c "
import json, sys
decoder = json.JSONDecoder()

def parse_objects(text):
    pos = 0
    while pos < len(text):
        try:
            obj, end = decoder.raw_decode(text, pos)
            yield obj
            pos = end
            while pos < len(text) and text[pos] in ' \t\n\r,':
                pos += 1
        except json.JSONDecodeError:
            break

texts = []
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    for d in parse_objects(line):
        if d.get('type') == 'text':
            t = d.get('part', {}).get('text', '')
            if t:
                texts.append(t)

sys.stdout.write('\n'.join(texts))
" > "$report_file" 2>/dev/null

    ok "$prompt_name 完成"
}

# ============================================================
# 主流程
# ============================================================

# 按时间戳建文件夹
run_id=$(date +%Y%m%d-%H%M%S)
run_dir="$RESULTS_DIR/$run_id"
mkdir -p "$run_dir"

total_prompt_count=0
total_fail_count=0

for ((round=1; round<=ROUNDS; round++)); do
    if [[ $ROUNDS -gt 1 ]]; then
        log "=== 第 ${round}/${ROUNDS} 轮 ==="
        round_dir="$run_dir/round-${round}"
        mkdir -p "$round_dir"
    else
        round_dir="$run_dir"
    fi

    prompt_count=0
    fail_count=0
    for prompt_file in "$PROMPTS_DIR"/*.md; do
        [[ -f "$prompt_file" ]] || continue
        # _ 开头的是共享片段，不是独立 prompt
        [[ "$(basename "$prompt_file")" == _* ]] && continue
        run_one "$prompt_file" "$round_dir" || fail_count=$((fail_count + 1))
        prompt_count=$((prompt_count + 1))
    done

    if [[ $prompt_count -eq 0 ]]; then
        fail "prompts/ 下没有找到 .md 文件"
        exit 1
    fi

    total_prompt_count=$((total_prompt_count + prompt_count))
    total_fail_count=$((total_fail_count + fail_count))
done

echo ""
echo "=== 测试完成 ==="
echo "  轮次: $ROUNDS"
echo "  总运行: $total_prompt_count 个提示词"
echo "  总失败: $total_fail_count"
echo "  输出: $run_dir"
