#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/wol-relay"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

echo "Copying application files..."
cp "$SCRIPT_DIR/wol-udp-relay.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/wol-relay.json" "$INSTALL_DIR/"

chmod +x "$INSTALL_DIR/wol-relay.py"

echo "Installing systemd service..."

sed "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    "$SCRIPT_DIR/wol-udp-relay.service" | \
    sudo tee /etc/systemd/system/wol-udp-relay.service >/dev/null

sudo systemctl daemon-reload
sudo systemctl enable wol-udp-relay.service
sudo systemctl restart wol-udp-relay.service

echo
echo "Installation complete."
echo

systemctl status wol-udp-relay.service --no-pager