#!/usr/bin/env bash
# Build the Table Order Android APK via Buildozer
# Output: apps/release/TableOrder.apk
# Run from the apps/ directory on a Linux/macOS machine (or WSL)
# Requires: buildozer, python3-dev, and Android SDK/NDK (auto-downloaded by buildozer)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TABLE_ORDER_DIR="$SCRIPT_DIR/table_order"
SHARED_DIR="$SCRIPT_DIR/shared"
RELEASE_DIR="$SCRIPT_DIR/release"

mkdir -p "$RELEASE_DIR"

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
echo " Copying APK to release/"
echo "============================================================"
APK=$(ls "$TABLE_ORDER_DIR/bin/"*.apk 2>/dev/null | head -1)
if [ -n "$APK" ]; then
    cp "$APK" "$RELEASE_DIR/TableOrder.apk"
    echo "TableOrder.apk  ->  $RELEASE_DIR/TableOrder.apk"
else
    echo "WARNING: APK not found in bin/. Check buildozer output."
fi

echo "============================================================"
echo " Cleaning up copied shared/ directory"
echo "============================================================"
rm -rf "$TABLE_ORDER_DIR/shared"

echo ""
echo "Build complete.  Files in: $RELEASE_DIR"
