"""The phone camera as a webcam, through a v4l2loopback virtual device."""
from __future__ import annotations

import time
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from . import adb, config
from .i18n import _
from .ui import APP_NAME, ensure_connection, log_tail, show_start_error

CAM_LABEL = "Phone Camera"
LOOPBACK_SETUP = """\
printf 'v4l2loopback\\n' | sudo tee /etc/modules-load.d/v4l2loopback.conf
printf 'options v4l2loopback devices=2 video_nr=10,11 card_label="Phone Camera,OBS Virtual Camera" exclusive_caps=1,1\\n' | sudo tee /etc/modprobe.d/v4l2loopback.conf
sudo modprobe v4l2loopback"""
RESOLUTIONS = {1920: "1080p", 1280: "720p", 640: "360p"}


def find_loopback() -> tuple[str, str] | None:
    """Virtual webcam to write to: (/dev/videoN, name), or None."""
    devs = []
    for d in sorted(Path("/sys/class/video4linux").glob("video*")):
        if "/devices/virtual/" in str(d.resolve()):  # v4l2loopback devices are virtual
            try:
                name = (d / "name").read_text().strip()
            except OSError:
                name = d.name
            devs.append((f"/dev/{d.name}", name))
    devs.sort(key=lambda dev: "OBS" in dev[1])  # leave OBS's own virtual camera alone
    return devs[0] if devs else None


def webcam_args(cfg: dict, link: adb.Link, device: str) -> list[str]:
    a = ["-s", link.serial, "--video-source=camera", "--no-audio",
         f"--camera-facing={cfg['cam_facing']}", "--camera-ar=16:9",
         f"--max-size={cfg['cam_max_size']}", f"--camera-fps={cfg['cam_fps']}",
         f"--video-codec={cfg['codec']}", f"--video-bit-rate={max(cfg['bit_rate'], 8)}M",
         f"--v4l2-sink={device}", f"--window-title={_('Phone camera')}"]
    if not cfg["cam_preview"]:
        # --no-video-playback alone still opens an (empty) control window.
        a.append("--no-window")
    return a


class LoopbackSetupDialog(QtWidgets.QDialog):
    """Explains the one-time v4l2loopback setup (needs root)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        lay = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(_(
            "No virtual webcam is available.\n\n"
            "One-time setup: install v4l2loopback (on Arch: v4l2loopback-dkms — some "
            "kernels, such as CachyOS's, already include it), then paste these commands in "
            "a terminal (your password will be asked). They create the “Phone Camera” "
            "webcam at every boot, plus a second one for OBS's virtual camera."))
        intro.setWordWrap(True)
        lay.addWidget(intro)
        cmds = QtWidgets.QPlainTextEdit(LOOPBACK_SETUP)
        cmds.setReadOnly(True)
        cmds.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        cmds.setMinimumWidth(720)
        cmds.setFixedHeight(90)
        lay.addWidget(cmds)
        buttons = QtWidgets.QDialogButtonBox()
        copy = buttons.addButton(_("Copy the commands"), QtWidgets.QDialogButtonBox.ActionRole)
        copy.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(LOOPBACK_SETUP))
        buttons.addButton(QtWidgets.QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)


class WebcamWindow(QtWidgets.QWidget):
    """Small control window, open as long as the camera is exposed as a webcam."""

    def __init__(self, cfg: dict, link: adb.Link, device: tuple[str, str]):
        super().__init__()
        self.cfg, self.link, self.device = cfg, link, device
        self.quick_drops = 0
        self.busy_retries = 0
        self.stopping = False
        self.setWindowTitle(_("{app} — Webcam").format(app=APP_NAME))

        self.status = QtWidgets.QLabel()
        self.status.setWordWrap(True)
        hint = QtWidgets.QLabel(_(
            "Pick “{name}” as the camera in Discord or your browser.\n"
            "In OBS, use a “Video Capture Device (V4L2)” source, not “PipeWire Camera”: "
            "PipeWire doesn't see this virtual webcam.").format(name=device[1]))
        hint.setWordWrap(True)
        self.switch_btn = QtWidgets.QPushButton()
        self.switch_btn.clicked.connect(self.switch_camera)
        stop_btn = QtWidgets.QPushButton(_("Stop"))
        stop_btn.clicked.connect(self.close)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.status)
        lay.addWidget(hint)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.switch_btn)
        row.addStretch()
        row.addWidget(stop_btn)
        lay.addLayout(row)
        self.setMinimumWidth(440)

        self.proc = QtCore.QProcess(self)
        self.proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self.proc.finished.connect(self.on_finished)
        self.config_mtime = config.config_mtime()
        self.watch = QtCore.QTimer(self, interval=2000, timeout=self.check_changes)
        self.watch.start()
        self.start()

    def start(self):
        if self.stopping:  # window closed while a delayed retry was pending
            return
        front = self.cfg["cam_facing"] == "front"
        self.switch_btn.setText(_("Switch to the back camera") if front
                                else _("Switch to the front camera"))
        self.status.setText(_("● Webcam on: {camera}, {res} at {fps} fps → {dev}").format(
            camera=_("front camera") if front else _("back camera"),
            res=RESOLUTIONS.get(self.cfg["cam_max_size"], f"{self.cfg['cam_max_size']}px"),
            fps=self.cfg["cam_fps"], dev=self.device[0]))
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.proc.setStandardOutputFile(str(config.LOG_FILE))
        self.started = time.monotonic()
        self.running_args = webcam_args(self.cfg, self.link, self.device[0])
        self.proc.start("scrcpy", self.running_args)

    def _stop_process(self):
        self.stopping = True
        self.proc.terminate()
        if not self.proc.waitForFinished(5000):
            self.proc.kill()
            self.proc.waitForFinished(2000)
        self.stopping = False

    def restart(self):
        self._stop_process()
        self.start()

    def check_changes(self):
        """Restart when settings were saved, or through the cable when one gets plugged
        in during a Wi-Fi session."""
        if self.proc.state() == QtCore.QProcess.NotRunning:
            return
        if config.config_mtime() != self.config_mtime:
            self.config_mtime = config.config_mtime()
            self.cfg.update({k: v for k, v in config.load_config().items() if k != "device"})
            if webcam_args(self.cfg, self.link, self.device[0]) != self.running_args:
                self.restart()
                return
        if self.link.usb or not adb.usb_ready(self.link.device_id):
            return
        self._stop_process()
        link = ensure_connection(self.cfg)
        if link:
            self.link = link
            self.start()
        else:
            self.close()

    def switch_camera(self):
        self.cfg["cam_facing"] = "back" if self.cfg["cam_facing"] == "front" else "front"
        self.busy_retries = 0
        config.update_config(cam_facing=self.cfg["cam_facing"])
        self.restart()

    def on_finished(self, code, _status):
        if self.stopping:
            return
        if code == 0 or (self.cfg["cam_preview"] and "v4l2 sink started" in log_tail(200)
                         and adb.responds(self.link.serial)):
            # Preview window closed with its ✕. scrcpy usually exits with 0, sometimes with
            # 2 like a real disconnection (same log): then the clue is that streaming had
            # started and the phone still answers.
            if self.ask_after_preview_closed():
                self.start()
                return
        elif code == 2:
            self.quick_drops = self.quick_drops + 1 if time.monotonic() - self.started < 10 else 0
            if self.quick_drops < 3:
                self.status.setText(_("Connection lost — reconnecting…"))
                link = ensure_connection(self.cfg)
                if link:
                    self.link = link
                    self.start()
                    return
        elif "CAMERA_IN_USE" in log_tail(200) and self.busy_retries < 5:
            # Locked phone: face unlock keeps the front camera to itself.
            self.busy_retries += 1
            self.status.setText(_("The phone is using its camera (face unlock?) — unlock it… "
                                  "retry {n}/5").format(n=self.busy_retries))
            QtCore.QTimer.singleShot(3000, self.start)
            return
        else:
            show_start_error(_("The webcam could not start."))
        self.stopping = True
        self.close()

    def ask_after_preview_closed(self) -> bool:
        """True if the user wants the webcam back (with or without the preview)."""
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning, APP_NAME,
            _("The preview window was closed: the webcam is off."), parent=self)
        box.setInformativeText(_("The preview and the webcam are one and the same. To stop "
                                 "the webcam, use the “Stop” button of this window instead."))
        again = box.addButton(_("Restart"), QtWidgets.QMessageBox.AcceptRole)
        no_preview = box.addButton(_("Restart without preview"), QtWidgets.QMessageBox.AcceptRole)
        box.addButton(_("Stop the webcam"), QtWidgets.QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is no_preview:
            self.cfg["cam_preview"] = False  # for this session only
        return box.clickedButton() in (again, no_preview)

    def closeEvent(self, event):
        self.stopping = True
        if self.proc.state() != QtCore.QProcess.NotRunning:
            self.proc.terminate()
            if not self.proc.waitForFinished(5000):
                self.proc.kill()
        super().closeEvent(event)


def mode_webcam(cfg: dict) -> int:
    device = find_loopback()
    if not device:
        LoopbackSetupDialog().exec()
        return 1
    link = ensure_connection(cfg)
    if not link:
        return 0
    cfg["device"] = link.device_id
    config.mark_running("webcam", link.device_id)
    try:
        win = WebcamWindow(cfg, link, device)
        win.show()
        return QtWidgets.QApplication.exec()
    finally:
        config.clear_running("webcam", link.device_id)
