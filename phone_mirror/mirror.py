"""Screen mirroring: scrcpy in a window, restarted when it has to be.

The mirror restarts on its own when a cable is plugged in during a Wi-Fi session
(USB is smoother), when settings are saved, and after a connection drop.
"""
from __future__ import annotations

import subprocess
import time

from PySide6 import QtWidgets

from . import adb, config, desktop
from .i18n import _
from .ui import APP_NAME, ensure_connection, notify, run_busy, show_start_error


def mirror_title(cfg: dict, link: adb.Link) -> str:
    name = config.device_name(cfg, link.device_id, link.name)
    return f"{name} ({'USB' if link.usb else 'Wi-Fi'})"


def mirror_args(cfg: dict, link: adb.Link) -> list[str]:
    a = ["-s", link.serial, f"--window-title={mirror_title(cfg, link)}",
         f"--video-codec={cfg['codec']}", f"--video-bit-rate={cfg['bit_rate']}M"]
    if cfg["max_size"]:
        a.append(f"--max-size={cfg['max_size']}")
    if cfg["max_fps"]:
        a.append(f"--max-fps={cfg['max_fps']}")
    if cfg["video_buffer"]:
        a.append(f"--video-buffer={cfg['video_buffer']}")
    if cfg["turn_screen_off"]:
        a.append("--turn-screen-off")
    if cfg["stay_awake"]:
        # --stay-awake only works while the phone is charging; --keep-active simulates
        # user activity and works on battery too.
        a.append("--keep-active")
    if cfg["fullscreen"]:
        a.append("--fullscreen")
    if cfg["always_on_top"]:
        a.append("--always-on-top")
    if not cfg["audio"]:
        a.append("--no-audio")
    return a


def _stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def run_scrcpy(cfg: dict, link: adb.Link) -> int | str:
    """Run the mirror until it ends.

    Returns scrcpy's exit code, "usb" if a cable was plugged in during a Wi-Fi
    mirror, or "reload" if settings were saved meanwhile (cfg is then updated).
    In both latter cases the caller starts the mirror again.
    """
    args = mirror_args(cfg, link)
    mtime = config.config_mtime()
    on_top = cfg["always_on_top"]
    if on_top:
        desktop.keep_above(mirror_title(cfg, link), link.device_id)
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(config.LOG_FILE, "w") as log:
            proc = subprocess.Popen(["scrcpy", *args], stdout=log, stderr=subprocess.STDOUT)
            while True:
                try:
                    return proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                if not link.usb and adb.usb_ready(link.device_id):
                    _stop(proc)
                    return "usb"
                if config.config_mtime() != mtime:
                    mtime = config.config_mtime()
                    cfg.update({k: v for k, v in config.load_config().items() if k != "device"})
                    if mirror_args(cfg, link) != args:
                        _stop(proc)
                        return "reload"
    finally:
        if on_top:
            desktop.keep_above_stop(link.device_id)


def mode_mirror(cfg: dict) -> int:
    quick_drops = 0
    running_for = None
    try:
        while True:
            link = ensure_connection(cfg)
            if not link:
                return 0
            if running_for != link.device_id:
                if running_for:
                    config.clear_running("mirror", running_for)
                running_for = link.device_id
                config.mark_running("mirror", running_for)
            # Stick to this phone for the rest of the session, even in "first found" mode.
            cfg["device"] = link.device_id

            started = time.monotonic()
            code = run_scrcpy(cfg, link)
            if code == "usb":
                notify(_("USB cable detected — switching to USB…"))
                continue
            if code == "reload":
                notify(_("New settings — restarting the mirror…"))
                continue
            if code == 0:  # window closed
                return 0
            if code != 2:  # failed to start
                show_start_error(_("The mirror could not start."))
                return 1

            # Exit code 2: the phone disconnected while mirroring.
            quick_drops = quick_drops + 1 if time.monotonic() - started < 10 else 0
            if quick_drops >= 3:  # drops right after starting, again and again: give up
                show_start_error(_("The mirror could not start."))
                return 1
            if cfg["auto_reconnect"]:
                notify(_("Connection lost — reconnecting…"))
                run_busy(_("Connection lost — reconnecting to the phone…"),
                         adb.wait_reconnect, link)
            else:
                answer = QtWidgets.QMessageBox.question(
                    None, APP_NAME, _("The connection to the phone was lost. Reconnect?"))
                if answer != QtWidgets.QMessageBox.Yes:
                    return 0
    finally:
        if running_for:
            config.clear_running("mirror", running_for)
