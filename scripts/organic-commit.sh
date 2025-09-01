#!/usr/bin/env bash
# scripts/organic-commit.sh
# Full validation and organic commit to main with smart message

set -euo pipefail

echo "🔍 Validando reglas críticas..."

# 0. Ensure inside a Git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ No es un repositorio Git"
  exit 1
fi

# 0.1 Ensure current branch is main
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "❌ Solo se permite commitear en 'main' (rama actual: $CURRENT_BRANCH)"
  exit 1
fi

# 0.2 Author identity enforcement
AUTHOR_NAME=$(git config user.name || echo "")
AUTHOR_EMAIL=$(git config user.email || echo "")
if [ "$AUTHOR_NAME" != "Ruben-Alvarez-Dev" ] || [ "$AUTHOR_EMAIL" != "ruben.alvarez.dev@gmail.com" ]; then
  echo "❌ FATAL: Autor inválido. Debe ser Ruben-Alvarez-Dev <ruben.alvarez.dev@gmail.com>"
  echo "   Configura Git: git config --global user.name 'Ruben-Alvarez-Dev' && git config --global user.email 'ruben.alvarez.dev@gmail.com'"
  exit 1
fi

# 1. Directory rules validation
if grep -q "^/logs\|^logs/" .gitignore; then
  echo "❌ FATAL: /logs/ encontrado en .gitignore - DEBE commitearse"
  exit 1
fi

if grep -q "^/plan\|^plan/" .gitignore; then
  echo "❌ FATAL: /plan/ encontrado en .gitignore - DEBE commitearse"
  exit 1
fi

if ! grep -q "OLD_VERSION" .gitignore; then
  echo "❌ FATAL: OLD_VERSION no encontrado en .gitignore - DEBE ignorarse"
  exit 1
fi

# 2. Ensure OLD_VERSION is not staged
if git diff --cached --name-only | grep -q "OLD_VERSION"; then
  echo "❌ FATAL: Detectados archivos en OLD_VERSION - NUNCA commitear OLD_VERSION"
  exit 1
fi

# 3. Ensure there are staged changes
if git diff --cached --quiet; then
  echo "❌ No hay cambios staged para committear"
  exit 0
fi

# 4. Significance check
CHANGED_LINES=$(git diff --cached --numstat | awk '{s+=$1+$2} END {print s+0}')
if [ "$CHANGED_LINES" -lt 3 ]; then
  echo "❌ Cambios muy pequeños (<3 líneas), no se hace commit"
  git reset HEAD .
  exit 0
fi

# 5. ATLAS black-box compliance (prevent internal exposure)
if git diff --cached --name-only | grep -q "atlas"; then
  if git diff --cached | grep -qE "(ATLAS INTERNAL|atlas.*internal|atlas.*algorithm)"; then
    echo "❌ ATLAS internal documentation detected - black box violation"
    exit 1
  fi
fi

# 6. Require checkpoint log when committing code changes
STAGED_FILES=$(git diff --cached --name-only)
CODE_CHANGED=$(echo "$STAGED_FILES" | grep -E '\.(py|js|ts|tsx|css|scss|yaml|yml)$' | grep -Ev '^(logs/)' || true)
if [ -n "$CODE_CHANGED" ]; then
  NEW_LOG=$(git diff --cached --name-only --diff-filter=A | grep -E '^logs/[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{6}_.+\.md$' || true)
  if [ -z "$NEW_LOG" ]; then
    echo "❌ Falta log de checkpoint en logs/YYYY-MM-DD_HHMMSS_X.Y.Z_keyword.md (añade uno nuevo)"
    exit 1
  fi
fi

# 7. Smart commit type detection
COMMIT_TYPE="feat"
if git diff --cached --name-only | grep -q "test"; then
  COMMIT_TYPE="test"
elif git diff --cached --name-only | grep -Eq "README|docs" && ! git diff --cached --name-only | grep -Eq "^logs/.*\.md$|plan/"; then
  COMMIT_TYPE="docs"
elif git diff --cached --name-only | grep -Eq "fix|bug"; then
  COMMIT_TYPE="fix"
elif git diff --cached --name-only | grep -Eq "atlas.*\.py|atlas.*\.js|atlas.*\.yaml"; then
  COMMIT_TYPE="feat(atlas)"
elif git diff --cached --name-only | grep -Eq "^logs/.*\.md$"; then
  COMMIT_TYPE="docs(log)"
elif git diff --cached --name-only | grep -q "plan/"; then
  COMMIT_TYPE="docs(plan)"
fi

# 8. Compose commit message
CHANGED_FILES=$(git diff --cached --numstat | wc -l | tr -d ' ')
INSERTIONS=$(git diff --cached --numstat | awk '{s+=$1} END {print s+0}')
DELETIONS=$(git diff --cached --numstat | awk '{s+=$2} END {print s+0}')
COMMIT_MESSAGE="$COMMIT_TYPE: $CHANGED_FILES files, $INSERTIONS insertions(+), $DELETIONS deletions(-)"

# 9. Commit to main
git commit -m "$COMMIT_MESSAGE"
echo "✅ Commit orgánico a MAIN: $COMMIT_MESSAGE"

