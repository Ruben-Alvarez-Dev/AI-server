#!/usr/bin/env bash
# tools/messaging/pulsar_setup_mac.sh
# Apache Pulsar 3.2.x setup for macOS (standalone)

set -euo pipefail

PULSAR_VERSION=${PULSAR_VERSION:-3.2.0}
PREFIX=${PULSAR_PREFIX:-/opt}
INSTALL_DIR="$PREFIX/pulsar"
ARCHIVE="apache-pulsar-$PULSAR_VERSION-bin.tar.gz"
URL=${PULSAR_URL:-"https://archive.apache.org/dist/pulsar/pulsar-$PULSAR_VERSION/$ARCHIVE"}

echo "== Pulsar setup =="
echo "Version: $PULSAR_VERSION"
echo "Prefix:  $PREFIX"

mkdir -p "$PREFIX"
cd "$PREFIX"

if [ ! -d "$INSTALL_DIR" ]; then
  echo "Downloading $URL ..."
  curl -L "$URL" -o "$ARCHIVE"
  echo "Extracting..."
  tar xzf "$ARCHIVE"
  mv "apache-pulsar-$PULSAR_VERSION" pulsar
fi

cd "$INSTALL_DIR"
echo "Configuring standalone mode and memory limits..."
sed -i '' 's/^pulsar.*/pulsar/;' conf/standalone.conf >/dev/null 2>&1 || true

# JVM heap limits in pulsar_env.sh
if grep -q "PULSAR_MEM" conf/pulsar_env.sh; then
  sed -i '' 's/^export PULSAR_MEM=.*/export PULSAR_MEM="-Xms1g -Xmx2g -XX:+UseG1GC"/' conf/pulsar_env.sh
else
  echo 'export PULSAR_MEM="-Xms1g -Xmx2g -XX:+UseG1GC"' >> conf/pulsar_env.sh
fi

echo "Creating launchd plist (not loaded automatically)..."
PLIST_SOURCE="$(cd -P -- "$(dirname -- "$0")" && pwd -P)/../../config/launchd/com.ai.pulsar.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.ai.pulsar.plist"
if [ -f "$PLIST_SOURCE" ]; then
  mkdir -p "$(dirname "$PLIST_TARGET")"
  cp "$PLIST_SOURCE" "$PLIST_TARGET"
  echo "Copied launchd plist to $PLIST_TARGET"
  echo "Load with: launchctl load -w $PLIST_TARGET"
fi

echo "Done. Use bin/pulsar-daemon start standalone to run manually."

