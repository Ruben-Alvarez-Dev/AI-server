#!/usr/bin/env bash
# tools/git/setup-hooks.sh
# Point Git to use repo-managed hooks under .githooks/

set -euo pipefail

git config core.hooksPath .githooks
echo "✅ Git hooks path configurado a .githooks"

