#!/bin/bash

# Nome do script principal
SCRIPT_NAME="main.py"

# Verifica se o script existe
if [[ ! -f "$SCRIPT_NAME" ]]; then
    echo "Arquivo $SCRIPT_NAME não encontrado!"
    exit 1
fi

# Detecta arquitetura da máquina
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
        echo "Arquitetura não suportada: $ARCH"
        exit 1
        ;;
esac

echo "[*] Arquitetura detectada: $ARCH"
echo "[*] Gerando binário com PyInstaller..."

# Gera binário
pyinstaller --onefile "$SCRIPT_NAME"

# Verifica se o executável foi criado
if [[ ! -f "dist/main" ]]; then
    echo "Erro: binário não foi gerado corretamente."
    exit 1
fi

# Cria pasta bin se necessário
mkdir -p bin

# Move binário com nome apropriado
cp dist/main "./bin/$BIN_NAME"
chmod +x "./bin/$BIN_NAME"

echo "[✓] Binário movido para ./bin/$BIN_NAME"

# Cria diretório de empacotamento final
PACKAGE_DIR="redfish_server_package"
mkdir -p "$PACKAGE_DIR/bin"
mkdir -p "$PACKAGE_DIR/deps"

# Copia binário e start.sh
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
