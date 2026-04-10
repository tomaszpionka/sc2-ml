#!/usr/bin/env bash
set -euo pipefail

FILE_PATH=$(jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null || echo "")
[ -z "$FILE_PATH" ] && exit 0

if echo "$FILE_PATH" | grep -q '\.py$'; then
  cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
  source .venv/bin/activate && poetry run ruff check "$FILE_PATH" --no-fix 2>&1 | tail -10 || true
fi
