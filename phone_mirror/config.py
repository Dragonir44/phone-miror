"""Settings (JSON in ~/.config/phone-mirror) and the run-state of mirror/webcam processes.

Several processes share the config file: the settings window, a running mirror and a
running webcam. Each one saves through `update_config()`, which re-reads the file first,
so nobody overwrites settings another process saved in the meantime.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

APP_ID = "phone-mirror"
CONFIG_DIR = Path.home() / ".config" / APP_ID
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = Path.home() / ".cache" / APP_ID
LOG_FILE = CACHE_DIR / "scrcpy.log"
PORT = 5555  # adb over Wi-Fi

DEFAULTS = {
    # Phones: adb serial -> {"name": str, "ip": str | None}
    "devices": {},
    "device": "",           # selected phone (serial); "" = first phone found
    "ip": "",               # IP to try when no phone is known yet
    # Mirror
    "max_size": 1920,       # 0 = native resolution
    "max_fps": 60,          # 0 = unlimited
    "bit_rate": 8,          # Mbit/s
    "codec": "h265",
    "video_buffer": 0,      # ms
    "turn_screen_off": True,
    "stay_awake": True,
    "fullscreen": False,
    "always_on_top": False,
    "audio": True,
    "auto_reconnect": True,
    "click_action": "settings",  # menu icon click: "settings" or "mirror"
    # Webcam
    "cam_facing": "front",
    "cam_max_size": 1920,   # 16:9 → 1920x1080, 1280x720, 640x360
    "cam_fps": 30,
    "cam_preview": False,
}

# Mirror presets: only these keys are touched.
PRESETS = {
    "smooth": dict(max_size=1280, max_fps=60, bit_rate=4, codec="h265", video_buffer=50),
    "balanced": dict(max_size=1920, max_fps=60, bit_rate=8, codec="h265", video_buffer=0),
    "quality": dict(max_size=0, max_fps=0, bit_rate=16, codec="h265", video_buffer=0),
}


def load_config() -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    try:
        stored = json.loads(CONFIG_FILE.read_text())
    except (OSError, ValueError):
        stored = {}
    # The original single-file script stored the camera size as "1920x1080".
    size = stored.pop("cam_size", None)
    if isinstance(size, str) and "x" in size and "cam_max_size" not in stored:
        stored["cam_max_size"] = max(int(v) for v in size.split("x"))
    cfg.update(stored)
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, CONFIG_FILE)


def update_config(**changes) -> dict:
    """Apply `changes` on top of the config currently on disk, save, return it."""
    cfg = load_config()
    cfg.update(changes)
    save_config(cfg)
    return cfg


def config_mtime() -> int:
    try:
        return CONFIG_FILE.stat().st_mtime_ns
    except OSError:
        return 0


def device_name(cfg: dict, device_id: str, fallback: str = "") -> str:
    return cfg["devices"].get(device_id, {}).get("name") or fallback or device_id


# ── Run state: one mirror and one webcam per phone at most ───────────────────

def _pid_file(mode: str, device_id: str) -> Path:
    return CACHE_DIR / f"{mode}-{device_id}.pid"


def mark_running(mode: str, device_id: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _pid_file(mode, device_id).write_text(str(os.getpid()))


def clear_running(mode: str, device_id: str) -> None:
    try:
        _pid_file(mode, device_id).unlink()
    except OSError:
        pass


def is_running(mode: str, device_id: str = "") -> bool:
    """Is a `mode` ("mirror"/"webcam") process alive — for this phone, or any if ""."""
    files = [_pid_file(mode, device_id)] if device_id else CACHE_DIR.glob(f"{mode}-*.pid")
    for f in files:
        try:
            cmdline = Path(f"/proc/{int(f.read_text())}/cmdline").read_text()
        except (OSError, ValueError):
            continue
        if APP_ID in cmdline or "phone_mirror" in cmdline:  # guards against PID reuse
            return True
    return False
