#!/bin/bash
# Pulsar Environment Configuration
# Source this file to set up Pulsar CLI tools

export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
export PATH="/opt/pulsar/bin:$PATH"

# Verify Pulsar CLI is available
if command -v pulsar-admin &> /dev/null; then
    echo "Pulsar CLI tools configured successfully"
    pulsar-admin clusters list 2>/dev/null || echo "Pulsar service may not be running"
else
    echo "Warning: Pulsar CLI tools not found in PATH"
fi