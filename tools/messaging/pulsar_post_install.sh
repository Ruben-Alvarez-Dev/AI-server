#!/usr/bin/env bash
# tools/messaging/pulsar_post_install.sh
# Post-install: create namespaces and run smoke tests

set -euo pipefail

PULSAR_ADMIN=${PULSAR_ADMIN:-pulsar-admin}

create_ns() {
  local ns=$1
  $PULSAR_ADMIN namespaces create "$ns" 2>/dev/null || true
  $PULSAR_ADMIN namespaces set-retention "$ns" --time 1d --size 10G || true
}

echo "Creating namespaces..."
create_ns memory-server/rag
create_ns llm-server/orchestration

echo "Smoke test: listing tenants and namespaces"
$PULSAR_ADMIN tenants list || true
$PULSAR_ADMIN namespaces list public || true

echo "Done."

