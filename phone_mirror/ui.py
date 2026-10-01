"""Qt helpers shared by the mirror, the webcam and the settings window."""
from __future__ import annotations

import concurrent.futures
import subprocess
import sys
import time

from PySide6 import QtCore, QtWidgets

from . import adb, config
from .i18n import _

APP_NAME = _("Phone Mirror")


def notify(message: str) -> None:
    try:
        subprocess.Popen(["notify-send", "-a", APP_NAME, "-i", "smartphone", APP_NAME, message])
    except OSError:
        pass


def run_busy(label: str, fn, *args):
    """Run fn in a thread; show a small "please wait" window if it takes a while."""
    dlg = QtWidgets.QProgressDialog(label, None, 0, 0)
    dlg.setWindowTitle(APP_NAME)
    dlg.setCancelButton(None)
    dlg.setMinimumDuration(0)
    dlg.reset()  # otherwise QProgressDialog pops up on its own
    start = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(1) as ex:
        fut = ex.submit(fn, *args)
        while not fut.done():
            if not dlg.isVisible() and time.monotonic() - start > 0.7:
                dlg.show()
            QtWidgets.QApplication.processEvents()
            concurrent.futures.wait([fut], timeout=0.03)
    dlg.close()
    return fut.result()


def log_tail(n: int = 12) -> str:
    try:
        lines = config.LOG_FILE.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-n:])


def launch_detached(*args: str) -> None:
    QtCore.QProcess.startDetached(sys.executable, ["-m", "phone_mirror", *args])


def remember(cfg: dict, link: adb.Link) -> None:
    """Record the phone we reached (name, current IP) in the saved device list."""
    entry = cfg["devices"].get(link.device_id, {})
    new = {"name": entry.get("name") or link.name, "ip": link.ip or entry.get("ip")}
    if new != entry:
        fresh = config.load_config()
        fresh["devices"][link.device_id] = new
        config.save_config(fresh)
        cfg["devices"] = fresh["devices"]


def ensure_connection(cfg: dict) -> adb.Link | None:
    """Reach the phone, asking the user what to do if it can't be. None = gave up."""
    while True:
        link, reason = run_busy(_("Connecting to the phone…"), adb.try_connect, cfg)
        if link:
            remember(cfg, link)
            return link

        target = cfg["device"]
        name = config.device_name(cfg, target) if target else _("The phone")
        if reason == "unauthorized":
            text = _("A phone is plugged in over USB but hasn't authorized this computer.\n\n"
                     "Accept “Allow USB debugging” on the phone's screen, then click Retry.")
        else:
            text = _("{name} can't be reached.\n\n"
                     "Plug it in over USB and click Retry: mirroring will go through the "
                     "cable, and Wi-Fi will be set up again for next time (useful after the "
                     "phone restarted).\n\n"
                     "Otherwise, check that it is on the same Wi-Fi network.").format(name=name)
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, APP_NAME, text)
        retry = box.addButton(_("Retry"), QtWidgets.QMessageBox.AcceptRole)
        change = box.addButton(_("Phone IP…"), QtWidgets.QMessageBox.ActionRole)
        box.addButton(_("Cancel"), QtWidgets.QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is change:
            current = cfg["devices"].get(target, {}).get("ip") if target else cfg["ip"]
            ip, ok = QtWidgets.QInputDialog.getText(
                None, APP_NAME, _("Phone IP address (Settings → Wi-Fi on the phone):"),
                text=current or "")
            if ok and ip.strip():
                if target in cfg["devices"]:
                    cfg["devices"][target]["ip"] = ip.strip()
                    config.update_config(devices=cfg["devices"])
                else:
                    cfg["ip"] = ip.strip()
                    config.update_config(ip=cfg["ip"])
        elif box.clickedButton() is not retry:
            return None


def show_start_error(message: str) -> None:
    box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, APP_NAME, message)
    box.setInformativeText(_("If the error mentions an encoder or a codec, try H.264 or a "
                             "lower resolution in the settings."))
    box.setDetailedText(log_tail(25))
    settings = box.addButton(_("Open settings"), QtWidgets.QMessageBox.ActionRole)
    box.addButton(QtWidgets.QMessageBox.Close)
    box.exec()
    if box.clickedButton() is settings:
        launch_detached("--settings")


def combo(items, current) -> QtWidgets.QComboBox:
    """QComboBox from [(value, label)], with `current` selected."""
    c = QtWidgets.QComboBox()
    for value, label in items:
        c.addItem(label, value)
    i = c.findData(current)
    c.setCurrentIndex(i if i >= 0 else 0)
    return c
