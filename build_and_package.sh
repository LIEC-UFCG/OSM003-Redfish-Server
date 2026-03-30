#!/bin/bash

# Main script name
SCRIPT_NAME="main.py"

# Checks if the script exists
if [[ ! -f "$SCRIPT_NAME" ]]; then
    echo "File $SCRIPT_NAME not found!"
    exit 1
fi

# Detects machine architecture
ARCH=$(uname -m)
BIN_NAME=""
case "$ARCH" in
    armv7l|armv6l|aarch64)
        BIN_NAME="server_arm"
        ;;
    x86_64)
        BIN_NAME="server_x86_64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

echo "[*] Detected architecture: $ARCH"
echo "[*] Generating binary with PyInstaller..."

# Generates binary
pyinstaller --onefile "$SCRIPT_NAME"

# Checks if the executable was created
if [[ ! -f "dist/main" ]]; then
    echo "Error: binary was not generated correctly."
    exit 1
fi

# Creates bin folder if necessary
mkdir -p bin

# Moves binary with appropriate name
cp dist/main "./bin/$BIN_NAME"
chmod +x "./bin/$BIN_NAME"

echo "[✓] Binary moved to ./bin/$BIN_NAME"

# Creates final packaging directory
PACKAGE_DIR="redfish_server_package"
mkdir -p "$PACKAGE_DIR/bin"
mkdir -p "$PACKAGE_DIR/deps"

# Copies binary and start.sh
cp "./bin/$BIN_NAME" "$PACKAGE_DIR/bin/"
cp start.sh "$PACKAGE_DIR/"
cp accounts.json "$PACKAGE_DIR/"
cp privilege_registry.json "$PACKAGE_DIR/"
cp sessions.json "$PACKAGE_DIR/"
cp ~/redfishpi_logs/audit_log.json "$PACKAGE_DIR/" 2>/dev/null || true
cp ~/redfishpi_logs/auth_log.json "$PACKAGE_DIR/" 2>/dev/null || true
cp ~/redfishpi_logs/event_log.json "$PACKAGE_DIR/" 2>/dev/null || true
cp ~/redfishpi_logs/error_log.json "$PACKAGE_DIR/" 2>/dev/null || true
cp deps/*.deb "$PACKAGE_DIR/deps/" 2>/dev/null || true

# Cria pacote tar.gz
TAR_NAME="${PACKAGE_DIR}.tar.gz"
tar -czf "$TAR_NAME" -C "$PACKAGE_DIR" .

echo "[✓] Pacote final criado: $TAR_NAME"

# Limpeza (opcional)
rm -rf build dist __pycache__ "$SCRIPT_NAME.spec" "$PACKAGE_DIR"

echo "[✓] Build completo com sucesso."
