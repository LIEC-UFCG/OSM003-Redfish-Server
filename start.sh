#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Installs system dependencies (offline), if any package is available.
if compgen -G "$SCRIPT_DIR/deps/*.deb" > /dev/null; then
    sudo dpkg -i "$SCRIPT_DIR"/deps/*.deb
fi

ARCH=$(uname -m)

case "$ARCH" in
    armv7l|armv6l|aarch64)
        echo "Detected ARM architecture."
        BIN_PATH="$SCRIPT_DIR/bin/server_arm"
        ;;
    x86_64)
        echo "Detected x86_64 architecture."
        BIN_PATH="$SCRIPT_DIR/bin/server_x86_64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

if [ -x "$BIN_PATH" ]; then
    exec "$BIN_PATH"
fi

echo "Binary not found: $BIN_PATH"
echo "Falling back to Python startup (main.py)."

if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/main.py"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/main.py"
elif command -v python >/dev/null 2>&1; then
    exec python "$SCRIPT_DIR/main.py"
else
    echo "Python interpreter not found to run fallback startup."
    exit 1
fi
