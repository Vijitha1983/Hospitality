#!/usr/bin/env bash
# Build the Table Order Android APK via Buildozer
# Run from the apps/ directory on a Linux/macOS machine (or WSL)
# Requires: buildozer, python3-dev, and Android SDK/NDK (auto-downloaded by buildozer)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TABLE_ORDER_DIR="$SCRIPT_DIR/table_order"
SHARED_DIR="$SCRIPT_DIR/shared"

echo "============================================================"
echo " Copying shared/ into table_order/ for bundling"
echo "============================================================"
cp -r "$SHARED_DIR" "$TABLE_ORDER_DIR/shared"

echo "============================================================"
echo " Building APK with Buildozer"
echo "============================================================"
cd "$TABLE_ORDER_DIR"
buildozer android debug

echo "============================================================"
echo " Cleaning up copied shared/ directory"
echo "============================================================"
rm -rf "$TABLE_ORDER_DIR/shared"

echo ""
echo "APK output: $TABLE_ORDER_DIR/bin/*.apk"
echo "Build complete."
