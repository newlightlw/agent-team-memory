#!/usr/bin/env bash
# liwei / 新组员在 Linux 服务器上一键修复「不是记忆仓库根」类错误。
# 用法: bash scripts/fix-wrong-memory-path.sh <英文短名> [记忆仓库路径]
set -euo pipefail

AUTHOR="${1:?用法: $0 <英文短名> [记忆仓库路径]}"
MEM_DIR="${2:-${TEAM_MEMORY_ROOT:-$HOME/team-memory}}"
GITEA="${GITEA_URL:-http://192.168.1.66:3000/ai-team/team-memory.git}"
TOOL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"

echo "=== 记忆数据仓库: $MEM_DIR ==="
echo "=== 工具仓库: $TOOL_DIR ==="

if [[ ! -f "$MEM_DIR/.team-memory.yml" ]]; then
  echo "记忆仓库未初始化, 运行 onboard..."
  MEM_DIR="$MEM_DIR" "$PY" "$TOOL_DIR/scripts/onboard.py" "$GITEA" "$AUTHOR"
else
  echo "记忆仓库已存在, 更新工具并刷新 skill..."
  "$PY" -m pip install -e "$TOOL_DIR[mcp]"
  "$PY" -m team_memory load --global --tools claude -p "$MEM_DIR"
  "$PY" -m team_memory check-bridges -p "$MEM_DIR" --tools claude
fi

echo ""
echo "✓ 完成。以后所有命令必须带: -p $MEM_DIR"
echo "  示例: $PY -m team_memory save \"标题\" -t skill --via claude -a $AUTHOR -p $MEM_DIR --note \"...\""
echo "  错误示例(勿用): -p $TOOL_DIR/team_memory"
echo ""
echo "Claude Code: 退出并新开一个会话, 再说「提交一下」"
