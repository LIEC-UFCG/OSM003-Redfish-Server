#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
CONFIG_FILE="${REDFISH_SERVER_CONFIG_FILE:-server_config.json}"
ENABLE_DOCKER_GROUP="${ENABLE_DOCKER_GROUP:-}"
RUN_SERVER="${RUN_SERVER:-}"

log() {
    echo "[*] $*"
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[ERROR] Required command not found: $1" >&2
        exit 1
    fi
}

log "Updating system packages"
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

require_command "$PYTHON_BIN"

if [ -f "$CONFIG_FILE" ]; then
    # Read setup defaults from config file unless explicit env vars were provided.
    eval "$($PYTHON_BIN - "$CONFIG_FILE" <<'PY'
import json
import sys

config_path = sys.argv[1]

try:
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = {}

def to_shell_bool(name, default):
    value = data.get(name, default)
    if isinstance(value, str):
        value = value.strip().lower() in ("1", "true", "yes", "on")
    else:
        value = bool(value)
    return "1" if value else "0"

print(f"CFG_ENABLE_DOCKER_GROUP={to_shell_bool('ENABLE_DOCKER_GROUP', False)}")
print(f"CFG_RUN_SERVER={to_shell_bool('RUN_SERVER_AFTER_SETUP', False)}")
PY
)"
fi

ENABLE_DOCKER_GROUP="${ENABLE_DOCKER_GROUP:-${CFG_ENABLE_DOCKER_GROUP:-0}}"
RUN_SERVER="${RUN_SERVER:-${CFG_RUN_SERVER:-0}}"

if [ ! -f "requirements.txt" ] || [ ! -f "main.py" ]; then
    echo "[ERROR] Execute this script from the repository root directory." >&2
    echo "[ERROR] Missing requirements.txt and/or main.py in: $PROJECT_DIR" >&2
    exit 1
fi

if [ "$ENABLE_DOCKER_GROUP" = "1" ]; then
    if ! groups "$USER" | grep -qw docker; then
        log "Adding user to the docker group"
        sudo usermod -aG docker "$USER"
        log "Restart the session to apply the docker group change"
    fi
    sudo systemctl enable --now docker
fi

if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment in $PROJECT_DIR/$VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
else
    log "Virtual environment already exists in $PROJECT_DIR/$VENV_DIR"
fi

log "Installing Python dependencies"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ "$RUN_SERVER" = "1" ]; then
    log "Starting the server"
    exec python main.py
fi

echo
echo "[OK] Environment prepared in $PROJECT_DIR"
echo "Next steps:"
echo "  source $VENV_DIR/bin/activate"
echo "  python main.py"
echo
echo "Tips:"
echo "  Edit server_config.json to define setup/runtime defaults"
echo "  ENABLE_DOCKER_GROUP=1 ./setup_source.sh"
echo "  RUN_SERVER=1 ./setup_source.sh"