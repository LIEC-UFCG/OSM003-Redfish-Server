#!/usr/bin/env bash

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/LIEC-UFCG/OSM003-Redfish-Server.git}"
REPO_DIR="${REPO_DIR:-$HOME/OSM003-Redfish-Server}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
ENABLE_DOCKER_GROUP="${ENABLE_DOCKER_GROUP:-0}"
RUN_SERVER="${RUN_SERVER:-0}"

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
sudo apt install -y git python3 python3-venv python3-pip

require_command git
require_command "$PYTHON_BIN"

if [ ! -d "$REPO_DIR/.git" ]; then
    log "Cloning repository into $REPO_DIR"
    git clone "$REPO_URL" "$REPO_DIR"
else
    log "Repository already exists in $REPO_DIR; updating"
    git -C "$REPO_DIR" pull --ff-only
fi

cd "$REPO_DIR"

if [ "$ENABLE_DOCKER_GROUP" = "1" ]; then
    if ! groups "$USER" | grep -qw docker; then
        log "Adding user to the docker group"
        sudo usermod -aG docker "$USER"
        log "Restart the session to apply the docker group change"
    fi
    sudo systemctl enable --now docker
fi

if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment in $REPO_DIR/$VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
else
    log "Virtual environment already exists in $REPO_DIR/$VENV_DIR"
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
echo "[OK] Environment prepared in $REPO_DIR"
echo "Next steps:"
echo "  cd $REPO_DIR"
echo "  source $VENV_DIR/bin/activate"
echo "  python main.py"
echo
echo "Tips:"
echo "  ENABLE_DOCKER_GROUP=1 ./setup_source.sh"
echo "  RUN_SERVER=1 ./setup_source.sh"