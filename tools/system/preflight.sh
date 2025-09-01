#!/usr/bin/env bash
# tools/system/preflight.sh
# System preflight checks for AI-Server (macOS + Apple Silicon)

set -euo pipefail

pass() { echo "✅ $1"; }
fail() { echo "❌ $1"; exit 1; }
warn() { echo "⚠️  $1"; }

# 2.1.1 macOS version
if command -v sw_vers >/dev/null 2>&1; then
  MACOS_VER=$(sw_vers -productVersion)
  MIN_VER=14
  MAJOR=${MACOS_VER%%.*}
  if [ "$MAJOR" -ge "$MIN_VER" ]; then pass "macOS $MACOS_VER (>= 14)"; else fail "macOS $MACOS_VER (< 14)"; fi
else warn "sw_vers not found (cannot verify macOS version)"; fi

# 2.1.2 RAM >= 128GB
if sysctl hw.memsize >/dev/null 2>&1; then
  MEM_BYTES=$(sysctl -n hw.memsize)
  REQ=$((128 * 1024 * 1024 * 1024))
  if [ "$MEM_BYTES" -ge "$REQ" ]; then pass "RAM >= 128GB"; else warn "RAM < 128GB (detected $(printf '%.1f' "$(echo "$MEM_BYTES/1073741824" | bc -l)") GB)"; fi
else warn "sysctl hw.memsize not available"; fi

# 2.1.3 Apple Silicon
ARCH=$(uname -m || echo "unknown")
if [ "$ARCH" = "arm64" ]; then pass "Apple Silicon arm64"; else warn "Non-arm64 architecture: $ARCH"; fi

# 2.1.4 Disk free >= 500GB
AVAIL_KB=$(df -k . | awk 'NR==2{print $4}')
REQ_KB=$((500*1024*1024))
if [ "$AVAIL_KB" -ge "$REQ_KB" ]; then pass "Disk free >= 500GB"; else warn "Disk free < 500GB"; fi

# 2.1.5 Metal access (compile or run a basic Swift check if available)
if command -v xcrun >/dev/null 2>&1; then
  if [ -f "tools/test_metal.swift" ]; then
    if xcrun swiftc tools/test_metal.swift -o /tmp/test_metal 2>/dev/null; then
      /tmp/test_metal && pass "Metal test passed" || warn "Metal test program returned non-zero"
    else
      warn "Failed to compile Metal test (Swift). Ensure Xcode CLT and SDKs."
    fi
  else
    warn "tools/test_metal.swift not found; skipping Metal test"
  fi
else
  warn "xcrun not found; cannot compile Metal test"
fi

# 2.1.6 Xcode CLT
if xcode-select -p >/dev/null 2>&1; then pass "Xcode Command Line Tools present"; else warn "Xcode CLT missing"; fi

# 2.5 Build tools
command -v cmake >/dev/null 2>&1 && pass "cmake found" || warn "cmake not found"
command -v make  >/dev/null 2>&1 && pass "make found"  || warn "make not found"
command -v pkg-config >/dev/null 2>&1 && pass "pkg-config found" || warn "pkg-config not found"

# 2.2 Python
command -v python3.11 >/dev/null 2>&1 && pass "python3.11 found" || warn "python3.11 not found"
[ -d venv ] && pass "venv directory exists" || warn "venv directory missing"

# 2.3 Node.js
command -v node >/dev/null 2>&1 && pass "Node.js found" || warn "Node.js not found"
command -v pnpm >/dev/null 2>&1 && pass "pnpm found" || warn "pnpm not found (optional)"

# 2.4 Rust
command -v rustc >/dev/null 2>&1 && pass "Rust toolchain found" || warn "Rust not found"
command -v cargo >/dev/null 2>&1 && pass "cargo found" || warn "cargo not found"

echo "--- Preflight check completed ---"
exit 0

