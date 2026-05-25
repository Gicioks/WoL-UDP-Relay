# WoL-UDP-Relay

This service listens for Wake-on-LAN (WoL) magic packets on UDP port 9 and rebroadcasts them to the correct subnet broadcast address based on the target device's MAC address.

## Install

Run:

```bash
cd wol-relay
chmod +x install.sh
./install.sh
```

The installer will:

- Create `~/wol-relay`
- Install `wol-relay.py`
- Copy example config `wol-relay.json`
- Create the `wol-relay.service` systemd service
- Enable automatic startup
- Start the service

Verify operation:

```bash
systemctl status wol-relay.service
```

View logs:

```bash
journalctl -u wol-relay.service -f
```

## Uninstall

Run:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

This will:

- Stop the `wol-udp-relay` service
- Disable automatic startup
- Remove the systemd service file
- Remove the `~/wol-relay` installation directory
- Reload systemd

## Configuration Options

### `default_broadcast`

The broadcast address used when a device MAC address is not explicitly listed in `mac_to_broadcast`.

Example:

```json
{
  "default_broadcast": "192.168.1.255"
}
```

If omitted and a MAC address is not mapped, the WoL packet will be dropped.

### `mac_to_broadcast`

Maps a target device MAC address to a specific subnet broadcast address.

Example:

```json
{
  "mac_to_broadcast": {
    "aa:bb:cc:dd:ee:ff": "192.168.10.255",
    "11:22:33:44:55:66": "192.168.20.255"
  }
}
```

When a WoL packet targeting `aa:bb:cc:dd:ee:ff` is received, the relay forwards the packet to `192.168.10.255:9`.

Likewise, a packet targeting `11:22:33:44:55:66` is forwarded to `192.168.20.255:9`.

## Example VLAN Setup

| VLAN | Network | Broadcast |
|--------|--------|--------|
| Main LAN | 192.168.1.0/24 | 192.168.1.255 |
| Servers | 192.168.10.0/24 | 192.168.10.255 |
| IoT | 192.168.20.0/24 | 192.168.20.255 |

Example configuration:

```json
{
  "default_broadcast": "192.168.1.255",
  "mac_to_broadcast": {
    "70:85:c2:11:22:33": "192.168.10.255",
    "00:11:22:33:44:55": "192.168.20.255"
  }
}
```

## MAC Address Format

MAC addresses may be entered in any of the following forms:

```text
aa:bb:cc:dd:ee:ff
AA:BB:CC:DD:EE:FF
aa-bb-cc-dd-ee-ff
```

The relay automatically normalizes them to lowercase colon-separated format.

## Service Verification

Check service status:

```bash
systemctl status wol-udp-relay.service
```

View live logs:

```bash
journalctl -u wol-udp-relay.service -f
```

Verify the relay is listening on UDP port 9:

```bash
sudo ss -ulpn | grep ':9'
```

## Typical Log Messages

Successful relay:

```text
Relayed WoL for aa:bb:cc:dd:ee:ff from ('192.168.1.100', 45678) -> 192.168.10.255:9
```

No mapping found:

```text
Dropped WoL for aa:bb:cc:dd:ee:ff from ('192.168.1.100', 45678) (no mapping)
```

Relay error:

```text
Failed relaying WoL for aa:bb:cc:dd:ee:ff -> 192.168.10.255: [error]
```

## Notes

- The service listens on UDP port 9 on all network interfaces.
- Only valid Wake-on-LAN magic packets are processed.
- Duplicate WoL packets for the same MAC are suppressed for 2 seconds.
- The relay ignores packets originating from the local host to prevent forwarding loops.
- A Raspberry Pi with access to multiple VLANs/subnets is an ideal deployment target.