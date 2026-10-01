"""adb helpers: find the phone over USB first, then over Wi-Fi.

A phone is identified by its adb USB serial, which is also its `ro.serialno`, so the
same phone is recognised whichever way it is reached.
"""
from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass

from .config import PORT


@dataclass
class Link:
    serial: str          # what to pass to `adb -s` / `scrcpy -s`
    device_id: str       # stable identity (ro.serialno)
    name: str            # name reported by the phone
    ip: str | None       # Wi-Fi IP, None if the phone's Wi-Fi is off

    @property
    def usb(self) -> bool:
        return ":" not in self.serial


def adb(*args: str, timeout: float = 15) -> str:
    try:
        r = subprocess.run(["adb", *args], capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return ""


def responds(serial: str) -> bool:
    """A real round-trip: right after Wi-Fi drops, `adb get-state` still says "device"."""
    return adb("-s", serial, "shell", "echo", "ok", timeout=5).strip() == "ok"


def wifi_ready(ip: str) -> bool:
    serial = f"{ip}:{PORT}"
    if responds(serial):
        return True
    adb("disconnect", serial, timeout=5)  # drop a dead or "offline" entry
    adb("connect", serial, timeout=10)
    return responds(serial)


def adb_devices() -> list[tuple[str, str]]:
    """[(serial, state)] for every phone adb knows (USB and Wi-Fi)."""
    devs = []
    for line in adb("devices").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and "._adb" not in parts[0] and not parts[0].startswith("emulator"):
            devs.append((parts[0], parts[1]))
    return devs


def usb_devices() -> list[tuple[str, str]]:
    return [(s, state) for s, state in adb_devices() if ":" not in s]


def usb_ready(device_id: str = "") -> str | None:
    """Serial of a plugged-in, authorized phone (this one if `device_id` is given)."""
    return next((s for s, state in usb_devices()
                 if state == "device" and (not device_id or s == device_id)), None)


def describe(serial: str) -> tuple[str, str]:
    """(ro.serialno, human name) of a reachable phone."""
    out = adb("-s", serial, "shell",
              "getprop ro.serialno; settings get global device_name; "
              "getprop ro.product.marketname; getprop ro.product.manufacturer; "
              "getprop ro.product.model", timeout=10).splitlines()
    serialno, user_name, market, maker, model = (out + [""] * 5)[:5]
    user_name = "" if user_name.strip() == "null" else user_name.strip()
    model = model.strip()
    if maker.strip() and not model.lower().startswith(maker.strip().lower()):
        model = f"{maker.strip()} {model}"
    return serialno.strip() or serial, user_name or market.strip() or model or serial


def wifi_ip(serial: str) -> str | None:
    out = adb("-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0")
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out)
    return m.group(1) if m else None


def prepare_usb(serial: str) -> str | None:
    """Phone on USB: get wireless adb ready for when the cable is unplugged.

    Returns its Wi-Fi IP, or None if its Wi-Fi is off.
    """
    ip = wifi_ip(serial)
    if ip and adb("-s", serial, "shell", "getprop", "service.adb.tcp.port").strip() != str(PORT):
        adb("-s", serial, "tcpip", str(PORT))               # adbd restarts on the phone…
        adb("-s", serial, "wait-for-usb-device", timeout=15)  # …wait until it is back
    return ip


def try_connect(cfg: dict) -> tuple[Link | None, str]:
    """Reach the selected phone (or the first one found): USB first — smoother, and it
    works without Wi-Fi — then Wi-Fi. Returns (link, "") or (None, reason)."""
    target = cfg["device"]
    reason = "unreachable"
    for serial, state in usb_devices():
        if target and serial != target:
            continue
        if state == "unauthorized":
            reason = "unauthorized"
        elif state == "device":
            device_id, name = describe(serial)
            return Link(serial, device_id, name, prepare_usb(serial)), ""

    if target:
        ips = [cfg["devices"].get(target, {}).get("ip")]
    else:
        ips = [d.get("ip") for d in cfg["devices"].values()] + [cfg["ip"]]
    for ip in dict.fromkeys(ip for ip in ips if ip):  # dedupe, keep order
        if wifi_ready(ip):
            device_id, name = describe(f"{ip}:{PORT}")
            if target and device_id != target:
                continue  # that IP now belongs to another phone
            return Link(f"{ip}:{PORT}", device_id, name, ip), ""
    return None, reason


def wait_reconnect(link: Link, attempts: int = 10, delay: float = 3) -> bool:
    """After a drop: watch for Wi-Fi or a cable for ~30 s (bounded)."""
    for _ in range(attempts):
        if usb_ready(link.device_id) or (link.ip and wifi_ready(link.ip)):
            return True
        time.sleep(delay)
    return False


def scan() -> tuple[list[Link], int]:
    """Every phone currently reachable through adb (USB or already-connected Wi-Fi),
    and how many more are plugged in but still waiting for the user to authorize
    this computer on their screen."""
    found: dict[str, Link] = {}
    unauthorized = 0
    for serial, state in adb_devices():
        if state == "unauthorized":
            unauthorized += 1
        if state != "device":
            continue
        device_id, name = describe(serial)
        if ":" in serial:  # USB wins when a phone is reachable both ways
            found.setdefault(device_id, Link(serial, device_id, name, serial.split(":")[0]))
        else:
            found[device_id] = Link(serial, device_id, name, prepare_usb(serial))
    return list(found.values()), unauthorized
