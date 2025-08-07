#!/bin/bash
# Test script to debug desktop file issues

echo "=== Desktop File Debug Test ==="
echo "Current working directory: $(pwd)"
echo "This script location: $(dirname "$(readlink -f "$0")")"

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"; 
echo "SCRIPT_DIR: $SCRIPT_DIR"

cd "$SCRIPT_DIR"
echo "Changed to: $(pwd)"

if [ -f installer.py ]; then
    echo "✅ installer.py found"
    echo "Attempting to run installer..."
    python3 installer.py --status
else
    echo "❌ installer.py not found"
    echo "Files in directory:"
    ls -la
fi