# Phone Mirror

A small Qt front-end for [scrcpy](https://github.com/Genymobile/scrcpy): mirror an
Android phone on your Linux desktop, or use its camera as a webcam — over Wi-Fi or USB,
from your application menu, without touching a terminal.

- **Mirror** the phone screen, with sound. Presets (smooth / balanced / best quality),
  H.265, an anti-stutter buffer, fullscreen, always on top.
- **Webcam**: the front or back camera becomes a regular webcam (v4l2loopback) that
  Discord, browsers and OBS can use.
- **USB or Wi-Fi, automatically**: USB is used when the phone is plugged in (smoother,
  works without Wi-Fi); plug the cable in during a Wi-Fi session and it switches over;
  unplug it and Wi-Fi takes over. After a phone restart, plugging it in once sets
  wireless adb up again.
- **Several phones**: detected over USB, recognised by serial number, their last IP is
  remembered.
- **Live settings**: saving the settings restarts a running mirror or webcam with them.
- **Stays awake on battery** (`--keep-active`; scrcpy's `--stay-awake` only works while
  charging).
- **KDE Plasma integration**: menu entry with right-click actions (mirror now, webcam,
  settings); *always on top* works under Wayland through KWin.
- English and French.

## Requirements

- `scrcpy` (tested with 4.1) and `adb` (`android-tools`)
- Python ≥ 3.10 and PySide6
- Optional: `v4l2loopback` (webcam), `qdbus6` from `qt6-tools` (always on top under
  KDE Wayland), `notify-send` (notifications)

On the phone: enable **USB debugging** (Developer options), plug it in once and accept
the prompt.

## Install

Arch Linux (AUR):

```bash
yay -S phone-mirror
```

Anywhere else (the menu entry is created on first run, or with `phone-mirror --install-desktop`):

```bash
pipx install phone-mirror
```

## Usage

Start **Phone Mirror** from the application menu: the settings window opens, with
*Start mirror* and *Start webcam* buttons. Right-click the icon for *Mirror now*,
*Webcam* and *Settings* — or make a click start mirroring right away (Phones tab).

```
phone-mirror                     mirror the phone screen
phone-mirror --webcam            phone camera as a webcam
phone-mirror --settings          settings window
phone-mirror --device SERIAL     pick a phone for this run
phone-mirror --install-desktop   (re)write the application-menu entry
```

Drop a file on the mirror window to send it to the phone's Downloads, or an APK to
install it (scrcpy feature).

### Webcam setup (once)

The webcam needs a v4l2loopback device. Install it (`v4l2loopback-dkms` on Arch; some
kernels such as CachyOS's already ship it), then:

```bash
printf 'v4l2loopback\n' | sudo tee /etc/modules-load.d/v4l2loopback.conf
printf 'options v4l2loopback devices=2 video_nr=10,11 card_label="Phone Camera,OBS Virtual Camera" exclusive_caps=1,1\n' | sudo tee /etc/modprobe.d/v4l2loopback.conf
sudo modprobe v4l2loopback
```

The settings window shows these commands too. In **OBS**, add a *Video Capture Device
(V4L2)* source while the webcam is running — not a *PipeWire Camera* source: with
`exclusive_caps=1` the device only advertises itself as a camera while streaming, and
PipeWire doesn't re-check it.

### Troubleshooting

- **The webcam fails with `CAMERA_IN_USE`**: the phone is locked and face unlock holds
  the front camera. Unlock the phone (Phone Mirror retries for a few seconds).
- **Stutters over Wi-Fi**: try the *Smooth* preset, a 30–50 ms buffer, or the cable.
- scrcpy's output of the last run is in `~/.cache/phone-mirror/scrcpy.log`; the error
  dialogs show its tail.

Settings live in `~/.config/phone-mirror/config.json`.

## License

MIT
