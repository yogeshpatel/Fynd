#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing backend dependencies..."
pip install -r requirements.txt -q

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "Copying .env.example to .env"
  cp .env.example .env
fi

echo "Starting backend at http://127.0.0.1:8000 ..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
