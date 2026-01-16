#!/bin/bash
# Start Vite dev server with proper WSL path handling
cd "$(dirname "$0")"
export NODE_OPTIONS="--no-warnings"
npm run dev -- --host 0.0.0.0 --port 5173
