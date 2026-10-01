"""Entry point.

    phone-mirror                     mirror the phone screen (saved settings)
    phone-mirror --webcam            expose the phone camera as a webcam (v4l2loopback)
    phone-mirror --settings          settings window
    phone-mirror --device SERIAL     pick a phone for this run (see the settings)
    phone-mirror --install-desktop   (re)write the application-menu entry

Everything happens in small windows: it is meant to be started from the app menu.
"""
from __future__ import annotations

import argparse
import sys

from . import __version__, config, desktop


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="phone-mirror",
        description="Mirror an Android phone or use its camera as a webcam (scrcpy).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--webcam", action="store_true", help="phone camera as a webcam")
    mode.add_argument("--settings", action="store_true", help="settings window")
    mode.add_argument("--install-desktop", action="store_true",
                      help="(re)write the application-menu entry and exit")
    parser.add_argument("--device", metavar="SERIAL", help="phone to use for this run")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    opts = parser.parse_args()

    cfg = config.load_config()
    if opts.install_desktop:
        print(desktop.write_entry(cfg["click_action"]))
        return 0
    if not desktop.entry_installed():  # e.g. installed with pip/pipx: no menu entry yet
        desktop.write_entry(cfg["click_action"])

    from PySide6 import QtCore, QtGui, QtWidgets

    from .i18n import LANG
    from .ui import APP_NAME

    app = QtWidgets.QApplication(sys.argv)
    # Standard buttons (Save, Close, Yes/No…) in the user's language.
    translator = QtCore.QTranslator(app)
    if translator.load(QtCore.QLocale(LANG), "qtbase", "_",
                       QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
    app.setApplicationName(APP_NAME)
    app.setDesktopFileName("phone-mirror")
    app.setWindowIcon(QtGui.QIcon.fromTheme("smartphone"))

    if opts.device:
        cfg["device"] = opts.device  # this run only

    if opts.settings:
        from .settings import SettingsDialog
        SettingsDialog(cfg).exec()
        return 0
    if opts.webcam:
        from .webcam import mode_webcam
        return mode_webcam(cfg)
    from .mirror import mode_mirror
    return mode_mirror(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
