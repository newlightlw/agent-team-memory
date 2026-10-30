#!/usr/bin/env bash
# Member bootstrap for macOS/Linux. No sudo or global Python installation.
set -euo pipefail
TEAM_MEMORY_PYTHON=''
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3,11))' >/dev/null 2>&1; then
    TEAM_MEMORY_PYTHON=$(command -v "$candidate")
    break
  fi
done
if [[ -z "$TEAM_MEMORY_PYTHON" ]] && command -v uv >/dev/null 2>&1; then
  TEAM_MEMORY_PYTHON=$(uv python find 3.11 2>/dev/null || true)
fi
if [[ -z "$TEAM_MEMORY_PYTHON" ]] || ! "$TEAM_MEMORY_PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3,11))' >/dev/null 2>&1; then
  echo 'Python 3.11+ is required. Install it first, or use an existing uv-managed Python.' >&2
  exit 1
fi
command -v git >/dev/null 2>&1 || { echo 'Git is required.' >&2; exit 1; }
TEAM_MEMORY_INSTALLER=$(mktemp "${TMPDIR:-/tmp}/team-memory-install.XXXXXXXX")
trap 'rm -f "$TEAM_MEMORY_INSTALLER"' EXIT
curl --fail --silent --show-error --location --proto '=https' \
  https://raw.githubusercontent.com/newlightlw/agent-team-memory/v0.3.0/scripts/install.py \
  --output "$TEAM_MEMORY_INSTALLER"
"$TEAM_MEMORY_PYTHON" "$TEAM_MEMORY_INSTALLER" "$@"
