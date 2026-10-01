"""Desktop integration: the menu entry, and KWin (KDE Plasma) helpers."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .config import CACHE_DIR

TEMPLATE = Path(__file__).with_name("data") / "phone-mirror.desktop"
USER_ENTRY = Path.home() / ".local/share/applications/phone-mirror.desktop"


def app_command() -> str:
    """How a menu entry should start us: the installed script, else `python -m`."""
    exe = shutil.which("phone-mirror")
    return exe or f"{sys.executable} -m phone_mirror"


def entry_installed() -> bool:
    data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    return USER_ENTRY.exists() or any(
        (Path(d) / "applications/phone-mirror.desktop").exists() for d in data_dirs)


def write_entry(click_action: str) -> Path:
    """Write the user menu entry (it overrides a system-wide one).

    A click on the icon opens the settings or starts mirroring; the right-click
    actions always offer mirror, webcam and settings.
    """
    cmd = app_command()
    lines, section = [], ""
    for line in TEMPLATE.read_text().splitlines():
        if line.startswith("["):
            section = line
        if line.startswith("Exec=phone-mirror"):
            if section == "[Desktop Entry]":
                line = f"Exec={cmd}" + (" --settings" if click_action == "settings" else "")
            else:
                line = line.replace("Exec=phone-mirror", f"Exec={cmd}", 1)
        lines.append(line)
    USER_ENTRY.parent.mkdir(parents=True, exist_ok=True)
    USER_ENTRY.write_text("\n".join(lines) + "\n")
    try:
        subprocess.run(["kbuildsycoca6"], capture_output=True, timeout=30)  # refresh KDE menu
    except (OSError, subprocess.TimeoutExpired):
        pass
    return USER_ENTRY


# ── KWin ─────────────────────────────────────────────────────────────────────
# Under Wayland an app can't put itself on top: scrcpy --always-on-top is ignored.
# KWin can, through a tiny script loaded over D-Bus (needs qdbus6, from qt6-tools).

_KEEP_ABOVE = "phone-mirror-keep-above"


def _kwin(method: str, *args: str) -> None:
    try:
        subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting",
                        f"org.kde.kwin.Scripting.{method}", *args],
                       capture_output=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        pass  # not on KDE: scrcpy --always-on-top does what it can (X11)


def keep_above(title: str, key: str) -> None:
    """Keep the window titled `title` on top, including when it appears later.
    `key` names the script, so each phone's mirror has its own."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    script = CACHE_DIR / f"keep-above-{key}.js"
    script.write_text(f"""var TITLE = {json.dumps(title)};
function apply(w) {{ if (w.caption === TITLE) w.keepAbove = true; }}
workspace.windowList().forEach(apply);
workspace.windowAdded.connect(function (w) {{
    apply(w);
    w.captionChanged.connect(function () {{ apply(w); }});
}});
""")
    _kwin("unloadScript", f"{_KEEP_ABOVE}-{key}")
    _kwin("loadScript", str(script), f"{_KEEP_ABOVE}-{key}")
    _kwin("start")


def keep_above_stop(key: str) -> None:
    _kwin("unloadScript", f"{_KEEP_ABOVE}-{key}")
