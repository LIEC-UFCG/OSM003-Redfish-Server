# Instala dependências do sistema (offline)
sudo dpkg -i deps/*.deb

ARCH=$(uname -m)

case "$ARCH" in
    armv7l|armv6l|aarch64)
        echo "Detected ARM architecture."
        ./bin/server_arm
        ;;
    x86_64)
        echo "Detected x86_64 architecture."
        ./bin/server_x86_64
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac
