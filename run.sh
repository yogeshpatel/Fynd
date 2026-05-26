#!/usr/bin/env bash
# Local RAG Workbench — single entry point
# Works on Linux and macOS
#
# Usage:
#   ./run.sh                  start backend + UI together (default)
#   ./run.sh all              start backend + UI together
#   ./run.sh backend          backend only
#   ./run.sh ui               UI only
#   ./run.sh install-llama    clone and build llama.cpp from source
#   ./run.sh install-ollama   install Ollama
#   ./run.sh help             show this help

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
UI_DIR="$SCRIPT_DIR/ui"
LLAMA_DIR="$SCRIPT_DIR/llama.cpp"

# Detect OS
OS="$(uname -s)"
case "$OS" in
  Linux)  PLATFORM="linux" ;;
  Darwin) PLATFORM="macos" ;;
  *)
    echo "Unsupported platform: $OS"
    exit 1
    ;;
esac

# CPU thread count
if [ "$PLATFORM" = "macos" ]; then
  NPROC="$(sysctl -n hw.logicalcpu)"
else
  NPROC="$(nproc)"
fi

# ─────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────

check_python() {
  if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ and try again."
    exit 1
  fi
  PY_VER="$(python3 -c 'import sys; print(sys.version_info.minor)')"
  if [ "$PY_VER" -lt 10 ]; then
    echo "ERROR: Python 3.10+ required. Found 3.$PY_VER."
    exit 1
  fi
}

check_node() {
  if ! command -v node &>/dev/null; then
    echo "ERROR: node not found. Install Node.js 18+ and try again."
    exit 1
  fi
  if ! command -v npm &>/dev/null; then
    echo "ERROR: npm not found."
    exit 1
  fi
}

setup_backend_venv() {
  cd "$BACKEND_DIR"
  if [ ! -d ".venv" ]; then
    echo "[backend] Creating virtual environment..."
    python3 -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "[backend] Installing dependencies..."
  pip install -r requirements.txt -q
  if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[backend] Copying .env.example → .env"
    cp .env.example .env
  fi
}

run_backend() {
  check_python
  setup_backend_venv
  echo "[backend] Starting at http://127.0.0.1:8000 ..."
  cd "$BACKEND_DIR"
  source .venv/bin/activate
  exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
}

run_ui() {
  check_node
  cd "$UI_DIR"
  if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[ui] Copying .env.example → .env"
    cp .env.example .env
  fi
  echo "[ui] Installing npm dependencies..."
  npm install --silent
  echo "[ui] Starting at http://localhost:5173 ..."
  exec npm run dev
}

run_all() {
  check_python
  check_node

  # Set up backend venv first (blocking, before we fork)
  setup_backend_venv

  # Set up UI deps
  cd "$UI_DIR"
  if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
  fi
  npm install --silent

  echo ""
  echo "  Backend → http://127.0.0.1:8000"
  echo "  UI      → http://localhost:5173"
  echo "  Press Ctrl+C to stop both."
  echo ""

  # Start backend in background
  (
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload 2>&1 | sed 's/^/[backend] /'
  ) &
  BACKEND_PID=$!

  # Start UI in background
  (
    cd "$UI_DIR"
    npm run dev 2>&1 | sed 's/^/[ui] /'
  ) &
  UI_PID=$!

  # Kill both on Ctrl+C
  trap 'echo ""; echo "Stopping..."; kill "$BACKEND_PID" "$UI_PID" 2>/dev/null; wait' INT TERM

  wait "$BACKEND_PID" "$UI_PID"
}

install_llama() {
  if ! command -v git &>/dev/null; then
    echo "ERROR: git not found."
    exit 1
  fi
  if ! command -v cmake &>/dev/null; then
    echo "ERROR: cmake not found. Install cmake and try again."
    if [ "$PLATFORM" = "macos" ]; then
      echo "  brew install cmake"
    else
      echo "  sudo apt install cmake   # Debian/Ubuntu"
      echo "  sudo dnf install cmake   # Fedora/RHEL"
    fi
    exit 1
  fi

  if [ -d "$LLAMA_DIR" ]; then
    echo "llama.cpp already cloned at $LLAMA_DIR"
    echo "To rebuild, delete the directory and run again."
    exit 0
  fi

  echo "Cloning llama.cpp..."
  git clone https://github.com/ggerganov/llama.cpp "$LLAMA_DIR"

  echo "Building llama.cpp with $NPROC threads..."
  cd "$LLAMA_DIR"
  cmake -B build
  cmake --build build --config Release -j"$NPROC"

  BINARY="$LLAMA_DIR/build/bin/llama-server"
  echo ""
  echo "Build complete."
  echo "Binary: $BINARY"
  echo ""
  echo "Add to backend/.env:"
  echo "  ENABLE_LLM=true"
  echo "  LLM_BACKEND=llama_cpp"
  echo "  MODEL_PATH=/path/to/your-model.gguf"
  echo "  LLAMA_SERVER_BIN=$BINARY"
}

install_ollama() {
  if command -v ollama &>/dev/null; then
    echo "Ollama is already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
    echo ""
    echo "Start it with:  ollama serve"
    echo "Pull a model:   ollama pull llama3"
    exit 0
  fi

  echo "Installing Ollama on $PLATFORM..."

  if [ "$PLATFORM" = "macos" ]; then
    if command -v brew &>/dev/null; then
      echo "Using Homebrew..."
      brew install ollama
    else
      echo "Homebrew not found — using curl installer..."
      curl -fsSL https://ollama.com/install.sh | sh
    fi
  else
    # Linux
    curl -fsSL https://ollama.com/install.sh | sh
  fi

  echo ""
  echo "Ollama installed."
  echo ""
  echo "Next steps:"
  echo "  1. Start Ollama:         ollama serve"
  echo "  2. Pull a model:         ollama pull llama3"
  echo "  3. Edit backend/.env:"
  echo "       ENABLE_LLM=true"
  echo "       LLM_BACKEND=ollama"
  echo "       OLLAMA_MODEL=llama3"
  echo "  4. Restart the backend:  ./run.sh backend"
}

show_help() {
  cat <<EOF
Local RAG Workbench — run.sh ($PLATFORM)

Usage:
  ./run.sh [command]

Commands:
  (none) / all      Start backend + UI together
  backend           Start backend only  (http://127.0.0.1:8000)
  ui                Start UI only       (http://localhost:5173)
  install-llama     Clone and build llama.cpp from source
  install-ollama    Install Ollama
  help              Show this help

LLM backend options (set in backend/.env):
  ENABLE_LLM=false          Retrieval-only, no LLM needed (default)
  ENABLE_LLM=true
  LLM_BACKEND=llama_cpp     Use llama-server with a GGUF model
  LLM_BACKEND=ollama        Use Ollama (run: ollama serve + ollama pull <model>)
EOF
}

# ─────────────────────────────────────────────
# dispatch
# ─────────────────────────────────────────────

case "${1:-all}" in
  all)             run_all ;;
  backend)         run_backend ;;
  ui)              run_ui ;;
  install-llama)   install_llama ;;
  install-ollama)  install_ollama ;;
  help | --help)   show_help ;;
  *)
    echo "Unknown command: $1"
    echo ""
    show_help
    exit 1
    ;;
esac
