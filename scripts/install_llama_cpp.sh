#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$SCRIPT_DIR/../llama.cpp"

if [ -d "$INSTALL_DIR" ]; then
  echo "llama.cpp already cloned at $INSTALL_DIR"
  echo "To rebuild, delete the directory and run this script again."
  exit 0
fi

echo "Cloning llama.cpp..."
git clone https://github.com/ggerganov/llama.cpp "$INSTALL_DIR"

cd "$INSTALL_DIR"

echo "Building llama.cpp (this may take a few minutes)..."
cmake -B build
cmake --build build --config Release -j"$(nproc)"

echo ""
echo "Build complete."
echo "llama-server binary: $INSTALL_DIR/build/bin/llama-server"
echo ""
echo "Add to backend/.env:"
echo "  LLAMA_SERVER_BIN=$INSTALL_DIR/build/bin/llama-server"
