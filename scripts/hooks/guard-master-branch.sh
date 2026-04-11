#!/usr/bin/env bash
set -euo pipefail

CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || echo "")"

if [[ "$CURRENT_BRANCH" == "master" || "$CURRENT_BRANCH" == "main" ]]; then
  echo "BLOCKED: Write/Edit is not allowed on the '${CURRENT_BRANCH}' branch. Create a feature branch first." >&2
  exit 2
fi

exit 0
