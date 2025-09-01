#!/usr/bin/env bash
# tools/messaging/nats_setup_mac.sh
# NATS Server setup with JetStream on macOS (config file based)

set -euo pipefail

CONF_PATH=${NATS_CONF:-"$(cd -P -- "$(dirname -- "$0")" && pwd -P)/../../config/environment/nats.conf"}

echo "NATS setup helper"
echo "Config file: $CONF_PATH"

cat <<EOF > "$CONF_PATH"
port: 4222
http: 8222
jetstream: {
  store_dir: "~/nats/jetstream"
  max_mem_store: 536870912 # 500MB
  max_file_store: 10737418240 # 10GB
}
EOF

echo "Generated NATS config with JetStream."
echo "Run: nats-server -c $CONF_PATH"

