#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_DIR="$SCRIPT_DIR/../ui"

cd "$UI_DIR"

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "Copying .env.example to .env"
  cp .env.example .env
fi

echo "Installing UI dependencies..."
npm install

echo "Starting UI at http://localhost:5173 ..."
npm run dev
