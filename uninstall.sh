#!/usr/bin/env bash
set -e

SERVICE_NAME="wol-udp-relay"
INSTALL_DIR="$HOME/wol-relay"

echo "Stopping service..."
sudo systemctl stop ${SERVICE_NAME}.service 2>/dev/null || true

echo "Disabling service..."
sudo systemctl disable ${SERVICE_NAME}.service 2>/dev/null || true

echo "Removing systemd service..."
sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service

echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl reset-failed

echo
read -p "Remove configuration file (wol-relay.json)? [y/N] " REMOVE_CONFIG

if [[ "$REMOVE_CONFIG" =~ ^[Yy]$ ]]; then
    echo "Removing installation directory..."
    rm -rf "$INSTALL_DIR"
else
    echo "Preserving configuration..."

    rm -f "$INSTALL_DIR/wol-relay.py"

    # Remove directory only if empty
    rmdir "$INSTALL_DIR" 2>/dev/null || true

    if [[ -f "$INSTALL_DIR/wol-relay.json" ]]; then
        echo
        echo "Configuration preserved at:"
        echo "  $INSTALL_DIR/wol-relay.json"
    fi
fi

echo
echo "WoL Relay successfully removed."