#!/bin/bash
# Test Vite build with explicit path handling
cd "$(dirname "$0")"
export NODE_OPTIONS="--no-warnings --max-old-space-size=4096"
export PATH="$PWD/node_modules/.bin:$PATH"

# Convert WSL path to Windows path if needed (WSL2)
if [[ "$PWD" == /mnt/* ]] || [[ "$PWD" == /home/* ]]; then
    echo "Running in WSL, using explicit node path..."
    node node_modules/vite/bin/vite.js build
else
    npm run build
fi
