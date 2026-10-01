"""Settings window: phones, mirror quality, webcam, menu entry.

Saving applies right away: a running mirror or webcam notices the new config and
restarts with it, so this window can stay open to adjust things live.
"""
from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from . import adb, config, desktop
from .i18n import _
from .ui import APP_NAME, combo, launch_detached, remember, run_busy
from .webcam import LoopbackSetupDialog, RESOLUTIONS, find_loopback


def preset_labels() -> dict[str, str]:
    return {"smooth": _("Smooth (busy Wi-Fi)"), "balanced": _("Balanced"),
            "quality": _("Best quality")}


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(_("{app} — Settings").format(app=APP_NAME))
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.general_tab(), _("Phones"))
        tabs.addTab(self.mirror_tab(), _("Mirror"))
        tabs.addTab(self.webcam_tab(), _("Webcam"))

        buttons = QtWidgets.QDialogButtonBox()
        mirror = buttons.addButton(_("Start mirror"), QtWidgets.QDialogButtonBox.ActionRole)
        mirror.clicked.connect(lambda: self.launch("mirror"))
        webcam = buttons.addButton(_("Start webcam"), QtWidgets.QDialogButtonBox.ActionRole)
        webcam.clicked.connect(lambda: self.launch("webcam"))
        save = buttons.addButton(QtWidgets.QDialogButtonBox.Save)
        save.clicked.connect(self.save)
        save.setToolTip(_("A running mirror or webcam restarts with the new settings."))
        buttons.addButton(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.reject)

        self.status = QtWidgets.QLabel()
        self.status.setWordWrap(True)
        self.status_timer = QtCore.QTimer(self, singleShot=True, interval=6000,
                                          timeout=self.status.clear)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(tabs)
        lay.addWidget(self.status)
        lay.addWidget(buttons)
        self.update_preset_label()

    # ── Phones tab ───────────────────────────────────────────────────────────
    def general_tab(self):
        c = self.cfg
        self.device = QtWidgets.QComboBox()
        detect = QtWidgets.QPushButton(_("Detect phones"))
        detect.setToolTip(_("Finds the phones plugged in over USB (or already connected over "
                            "Wi-Fi) and prepares their Wi-Fi connection."))
        detect.clicked.connect(self.detect_devices)
        add = QtWidgets.QPushButton(_("Add by IP…"))
        add.clicked.connect(self.add_by_ip)
        self.rename_btn = QtWidgets.QPushButton(_("Rename…"))
        self.rename_btn.clicked.connect(self.rename_device)
        self.forget_btn = QtWidgets.QPushButton(_("Forget"))
        self.forget_btn.clicked.connect(self.forget_device)
        self.device.currentIndexChanged.connect(self.update_device_buttons)
        self.fill_devices(c["device"])
        row = QtWidgets.QHBoxLayout()
        for b in (detect, add, self.rename_btn, self.forget_btn):
            row.addWidget(b)

        test = QtWidgets.QPushButton(_("Test the connection"))
        test.clicked.connect(self.test_connection)
        self.test_result = QtWidgets.QLabel()
        self.test_result.setWordWrap(True)
        info = QtWidgets.QLabel("<small>" + _(
            "A new phone: enable USB debugging (Developer options), plug it in and click "
            "“Detect phones”. After a phone restart, plug it in once: Wi-Fi is set up again "
            "automatically.") + "</small>")
        info.setWordWrap(True)

        self.auto_reconnect = QtWidgets.QCheckBox(_("Reconnect automatically if Wi-Fi drops"),
                                                  checked=c["auto_reconnect"])
        self.click_action = combo([("settings", _("Open these settings")),
                                   ("mirror", _("Start mirroring right away"))],
                                  c["click_action"])
        click_info = QtWidgets.QLabel("<small>" + _(
            "Right-clicking the icon always offers: Mirror now, Webcam and Settings.")
            + "</small>")
        click_info.setWordWrap(True)

        w = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(w)
        form.addRow(_("Phone"), self.device)
        form.addRow(row)
        form.addRow(test, self.test_result)
        form.addRow(info)
        form.addRow(self.auto_reconnect)
        form.addRow(QtWidgets.QLabel("<b>" + _("Application menu") + "</b>"))
        form.addRow(_("Clicking the icon"), self.click_action)
        form.addRow(click_info)
        return w

    def fill_devices(self, selected: str):
        self.device.blockSignals(True)
        self.device.clear()
        self.device.addItem(_("Automatic (first phone found)"), "")
        for device_id, d in self.cfg["devices"].items():
            where = d.get("ip") or _("no Wi-Fi yet")
            self.device.addItem(f"{d.get('name') or device_id} — {where}", device_id)
        i = self.device.findData(selected)
        self.device.setCurrentIndex(i if i >= 0 else 0)
        self.device.blockSignals(False)
        self.update_device_buttons()

    def update_device_buttons(self):
        known = bool(self.device.currentData())
        self.rename_btn.setEnabled(known)
        self.forget_btn.setEnabled(known)

    def save_devices(self):
        config.update_config(devices=self.cfg["devices"])

    def detect_devices(self):
        links, unauthorized = run_busy(_("Looking for phones…"), adb.scan)
        for link in links:
            entry = self.cfg["devices"].setdefault(link.device_id, {})
            entry["name"] = entry.get("name") or link.name
            entry["ip"] = link.ip or entry.get("ip")
        messages = []
        if links:
            self.save_devices()
            self.fill_devices(self.device.currentData() or "")
            messages.append(_("✔ Found: {names}").format(
                names=", ".join(self.cfg["devices"][l.device_id]["name"] for l in links)))
        if unauthorized:
            messages.append(_(
                "⚠ A plugged-in phone hasn't authorized this computer yet: unlock it and accept "
                "“Allow USB debugging?” on its screen, then click “Detect phones” again. No "
                "prompt? Unplug and plug it back in, or use “Revoke USB debugging "
                "authorizations” in its Developer options."))
        if not messages:
            messages.append(_("✘ No phone found. Plug one in over USB, with USB debugging "
                              "enabled, and accept the prompt on it."))
        self.test_result.setText("\n".join(messages))

    def add_by_ip(self):
        ip, ok = QtWidgets.QInputDialog.getText(
            self, APP_NAME, _("Phone IP address (Settings → Wi-Fi on the phone):"))
        ip = ip.strip()
        if not ok or not ip:
            return
        found = run_busy(_("Connecting to the phone…"),
                         lambda: adb.wifi_ready(ip) and adb.describe(f"{ip}:{config.PORT}"))
        if not found:
            self.test_result.setText(_("✘ No answer from {ip}:{port}. Wireless adb must be on: "
                                       "plug the phone in once and click “Detect phones”.")
                                     .format(ip=ip, port=config.PORT))
            return
        device_id, name = found
        entry = self.cfg["devices"].setdefault(device_id, {})
        entry.update(name=entry.get("name") or name, ip=ip)
        self.save_devices()
        self.fill_devices(device_id)
        self.test_result.setText(_("✔ Added: {name}").format(name=entry["name"]))

    def rename_device(self):
        device_id = self.device.currentData()
        entry = self.cfg["devices"][device_id]
        name, ok = QtWidgets.QInputDialog.getText(self, APP_NAME, _("Name of this phone:"),
                                                  text=entry.get("name") or "")
        if ok and name.strip():
            entry["name"] = name.strip()
            self.save_devices()
            self.fill_devices(device_id)

    def forget_device(self):
        device_id = self.device.currentData()
        del self.cfg["devices"][device_id]
        self.save_devices()
        self.fill_devices("")

    def test_connection(self):
        probe = dict(self.cfg, device=self.device.currentData() or "")
        link, reason = run_busy(_("Connecting to the phone…"), adb.try_connect, probe)
        if link:
            remember(self.cfg, link)
            self.fill_devices(self.device.currentData() or "")
            name = config.device_name(self.cfg, link.device_id, link.name)
            if not link.usb:
                self.test_result.setText(_("✔ {name}: connected over Wi-Fi ({ip})")
                                         .format(name=name, ip=link.ip))
            elif link.ip:
                self.test_result.setText(_("✔ {name}: connected over USB — Wi-Fi ready for "
                                           "later ({ip})").format(name=name, ip=link.ip))
            else:
                self.test_result.setText(_("✔ {name}: connected over USB — the phone's Wi-Fi "
                                           "is off").format(name=name))
        elif reason == "unauthorized":
            self.test_result.setText(_("✘ Plugged in over USB but not authorized: accept the "
                                       "prompt on the phone."))
        else:
            self.test_result.setText(_("✘ Unreachable. Plug the phone in over USB."))

    # ── Mirror tab ───────────────────────────────────────────────────────────
    def mirror_tab(self):
        c = self.cfg
        self.preset = QtWidgets.QComboBox()
        self.preset.addItem(_("Custom"), "")
        for key, label in preset_labels().items():
            self.preset.addItem(label, key)
        self.preset.activated.connect(self.apply_preset)

        self.max_size = combo([(0, _("Native")), (2400, "2400 px"), (1920, "1920 px"),
                               (1600, "1600 px"), (1280, "1280 px"), (1024, "1024 px"),
                               (800, "800 px")], c["max_size"])
        self.max_fps = combo([(0, _("Unlimited")), (120, "120"), (90, "90"), (60, "60"),
                              (30, "30")], c["max_fps"])
        self.bit_rate = QtWidgets.QSpinBox(minimum=1, maximum=40, suffix=" Mb/s",
                                           value=c["bit_rate"])
        self.codec = combo([("h265", _("H.265 — better picture at the same bitrate")),
                            ("h264", _("H.264 — most compatible"))], c["codec"])
        self.video_buffer = QtWidgets.QSpinBox(minimum=0, maximum=500, singleStep=10,
                                               suffix=" ms", value=c["video_buffer"])
        self.video_buffer.setSpecialValueText(_("None (lowest latency)"))
        self.video_buffer.setToolTip(_("Delays the picture slightly to absorb Wi-Fi hiccups."))
        for w in (self.max_size, self.max_fps, self.codec):
            w.currentIndexChanged.connect(self.update_preset_label)
        for w in (self.bit_rate, self.video_buffer):
            w.valueChanged.connect(self.update_preset_label)

        self.turn_screen_off = QtWidgets.QCheckBox(_("Turn the phone screen off"),
                                                   checked=c["turn_screen_off"])
        self.stay_awake = QtWidgets.QCheckBox(_("Keep the phone awake (even on battery)"),
                                              checked=c["stay_awake"])
        self.audio = QtWidgets.QCheckBox(_("Forward the sound"), checked=c["audio"])
        self.fullscreen = QtWidgets.QCheckBox(_("Fullscreen"), checked=c["fullscreen"])
        self.always_on_top = QtWidgets.QCheckBox(_("Always on top"), checked=c["always_on_top"])

        tip = QtWidgets.QLabel("<small>" + _(
            "Stutters? Over Wi-Fi it's nearly always the bitrate: try “Smooth”, or add a "
            "30–50 ms buffer — or plug the cable in. Tip: drop a file on the window to send "
            "it to Downloads, or an APK to install it.") + "</small>")
        tip.setWordWrap(True)

        w = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(w)
        form.addRow(_("Preset"), self.preset)
        form.addRow(_("Max resolution"), self.max_size)
        form.addRow(_("Max frame rate"), self.max_fps)
        form.addRow(_("Video bitrate"), self.bit_rate)
        form.addRow(_("Codec"), self.codec)
        form.addRow(_("Anti-stutter buffer"), self.video_buffer)
        for box in (self.turn_screen_off, self.stay_awake, self.audio, self.fullscreen,
                    self.always_on_top):
            form.addRow(box)
        form.addRow(tip)
        return w

    def preset_values(self) -> dict:
        return dict(max_size=self.max_size.currentData(), max_fps=self.max_fps.currentData(),
                    bit_rate=self.bit_rate.value(), codec=self.codec.currentData(),
                    video_buffer=self.video_buffer.value())

    def apply_preset(self, index: int):
        values = config.PRESETS.get(self.preset.itemData(index))
        if not values:
            return
        self.max_size.setCurrentIndex(self.max_size.findData(values["max_size"]))
        self.max_fps.setCurrentIndex(self.max_fps.findData(values["max_fps"]))
        self.bit_rate.setValue(values["bit_rate"])
        self.codec.setCurrentIndex(self.codec.findData(values["codec"]))
        self.video_buffer.setValue(values["video_buffer"])

    def update_preset_label(self):
        current = self.preset_values()
        key = next((k for k, v in config.PRESETS.items() if v == current), "")
        self.preset.setCurrentIndex(self.preset.findData(key))

    # ── Webcam tab ───────────────────────────────────────────────────────────
    def webcam_tab(self):
        c = self.cfg
        self.cam_facing = combo([("front", _("Front (selfie)")), ("back", _("Back"))],
                                c["cam_facing"])
        self.cam_max_size = combo(list(RESOLUTIONS.items()), c["cam_max_size"])
        self.cam_fps = combo([(30, "30"), (24, "24"), (15, "15")], c["cam_fps"])
        self.cam_preview = QtWidgets.QCheckBox(_("Show a preview on the computer"),
                                               checked=c["cam_preview"])

        device = find_loopback()
        status = QtWidgets.QLabel(
            _("Virtual webcam ready: “{name}” ({dev})").format(name=device[1], dev=device[0])
            if device else _("No virtual webcam yet — a one-time setup is needed."))
        status.setWordWrap(True)

        w = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(w)
        form.addRow(_("Camera"), self.cam_facing)
        form.addRow(_("Resolution"), self.cam_max_size)
        form.addRow(_("Frame rate"), self.cam_fps)
        form.addRow(self.cam_preview)
        form.addRow(status)
        if not device:
            setup = QtWidgets.QPushButton(_("How to set it up…"))
            setup.clicked.connect(lambda: LoopbackSetupDialog(self).exec())
            form.addRow(setup)
        return w

    # ── Save / launch ────────────────────────────────────────────────────────
    def collect(self):
        old_click = config.load_config()["click_action"]
        self.cfg.update(self.preset_values())
        self.cfg.update(
            device=self.device.currentData() or "",
            turn_screen_off=self.turn_screen_off.isChecked(),
            stay_awake=self.stay_awake.isChecked(), audio=self.audio.isChecked(),
            fullscreen=self.fullscreen.isChecked(), always_on_top=self.always_on_top.isChecked(),
            cam_facing=self.cam_facing.currentData(), cam_max_size=self.cam_max_size.currentData(),
            cam_fps=self.cam_fps.currentData(), cam_preview=self.cam_preview.isChecked(),
            auto_reconnect=self.auto_reconnect.isChecked(),
            click_action=self.click_action.currentData(),
        )
        # A running mirror may have recorded a newer IP meanwhile: keep it.
        for device_id, entry in config.load_config()["devices"].items():
            if device_id in self.cfg["devices"] and entry.get("ip"):
                self.cfg["devices"][device_id]["ip"] = entry["ip"]
        config.save_config(self.cfg)
        if self.cfg["click_action"] != old_click:
            desktop.write_entry(self.cfg["click_action"])

    def show_status(self, text: str):
        self.status.setText(text)
        self.status_timer.start()

    def save(self):
        self.collect()
        running = [label for mode, label in (("mirror", _("to the running mirror")),
                                              ("webcam", _("to the running webcam")))
                   if config.is_running(mode)]
        if running:
            self.show_status(_("✔ Saved — applied {where} (restarting in a few seconds).")
                             .format(where=_(" and ").join(running)))
        else:
            self.show_status(_("✔ Saved."))

    def launch(self, mode: str):
        self.collect()
        device_id = self.cfg["device"]
        if config.is_running(mode, device_id):
            self.show_status(_("Already running: settings applied (restarting in a few "
                               "seconds)."))
            return
        args = (["--webcam"] if mode == "webcam" else []) + \
               (["--device", device_id] if device_id else [])
        launch_detached(*args)
        self.show_status((_("✔ Mirror started.") if mode == "mirror" else _("✔ Webcam started."))
                         + " " + _("Keep this window open to adjust: each save applies right "
                                   "away (short restart)."))
