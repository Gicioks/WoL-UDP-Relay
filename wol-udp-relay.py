#!/usr/bin/env python3
import json
import re
import socket
import sys
import time
from pathlib import Path

CONF_PATH = Path(__file__).resolve().parent / "wol-relay.json"

MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", re.I)

def norm_mac(mac: str) -> str:
    mac = mac.strip().lower().replace("-", ":")
    if not MAC_RE.match(mac):
        raise ValueError(f"Invalid MAC: {mac}")
    return mac

def extract_mac_from_magic(pkt: bytes) -> str | None:
    # Standard WoL: 6 bytes of 0xFF followed by 16 repetitions of target MAC (6 bytes)
    if len(pkt) < 6 + 16 * 6:
        return None
    if pkt[0:6] != b"\xff" * 6:
        return None
    mac_bytes = pkt[6:12]
    # Verify repeats
    for i in range(1, 16):
        if pkt[6 + i * 6 : 12 + i * 6] != mac_bytes:
            return None
    return ":".join(f"{b:02x}" for b in mac_bytes)

def load_conf():
    data = json.loads(CONF_PATH.read_text(encoding="utf-8"))
    m = {norm_mac(k): v for k, v in data.get("mac_to_broadcast", {}).items()}
    default_b = data.get("default_broadcast")
    return m, default_b

def get_local_ipv4s() -> set[str]:
    """
    Best-effort list of local IPv4 addresses for loop prevention.
    (Not perfect in every exotic setup, but good for typical Pi configs.)
    """
    ips = {"127.0.0.1"}

    # Add address of default route interface (works well on Raspberry Pi)
    try:
        tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmp.connect(("8.8.8.8", 80))
        ips.add(tmp.getsockname()[0])
        tmp.close()
    except Exception:
        pass

    # Add hostname-resolved addresses
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except Exception:
        pass

    return ips

def main():
    mac_map, default_bcast = load_conf()

    listen_ip = "0.0.0.0"
    listen_port = 9

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_ip, listen_port))

    # Sender socket (enable broadcast)
    out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    out.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    local_ips = get_local_ipv4s()

    # Dedupe window: many WoL clients send bursts; also helps reduce noise.
    last_sent: dict[str, float] = {}
    DEDUPE_SECONDS = 2.0

    print(f"Listening UDP/{listen_port} for WoL packets... Local IPs: {sorted(local_ips)}", flush=True)

    while True:
        pkt, src = sock.recvfrom(4096)

        # Prevent infinite loop: ignore our own relayed broadcasts
        if src[0] in local_ips:
            continue

        mac = extract_mac_from_magic(pkt)
        if not mac:
            # Ignore non-WoL packets silently
            continue

        now = time.time()
        if now - last_sent.get(mac, 0.0) < DEDUPE_SECONDS:
            continue
        last_sent[mac] = now

        bcast = mac_map.get(mac, default_bcast)
        if not bcast:
            print(f"Dropped WoL for {mac} from {src} (no mapping)", flush=True)
            continue

        try:
            out.sendto(pkt, (bcast, 9))
            print(f"Relayed WoL for {mac} from {src} -> {bcast}:9", flush=True)
        except Exception as e:
            print(f"Failed relaying WoL for {mac} -> {bcast}: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()