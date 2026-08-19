from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading
import json
import urllib.request
import urllib.error

from . import dbus_notify

logger = logging.getLogger(__name__)

_PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUNDLED_SOUND = os.path.join(_PKG_DIR, "sounds", "keyclick.wav")

_DEFAULTS = {
    "sound_enabled": True,
    "sound_path": "",
    "sound_volume": 100,
    "icon_path": "",
}

_BUNDLED_ICON = os.path.join(_PKG_DIR, "assets", "icon-128.png")


def _load_config() -> dict:
    cfg_path = os.path.join(_PKG_DIR, "plugin.yaml")
    data = dict(_DEFAULTS)
    try:
        import yaml

        with open(cfg_path, encoding="utf-8") as fh:
            parsed = yaml.safe_load(fh) or {}
        data.update(parsed.get("config", {}))
    except Exception:
        logger.debug("config load failed, using defaults", exc_info=True)
    return data


_CONFIG = _load_config()


def _sound_path() -> str:
    path = _CONFIG.get("sound_path") or _BUNDLED_SOUND
    return os.path.expanduser(path)


def _play_keyclick() -> None:
    if not _CONFIG.get("sound_enabled", True):
        return
    path = _sound_path()
    if not os.path.exists(path):
        return
    player = shutil.which("paplay") or shutil.which("aplay")
    if not player:
        # fallback: terminal bell if no audio player is available
        print("\a", end="", file=sys.stderr, flush=True)
        return
    cmd = [player, path]
    if player.endswith("paplay"):
        vol = max(0, min(100, int(_CONFIG.get("sound_volume", 100))))
        cmd = [player, "--volume", str(int(vol / 100 * 65536)), path]
    try:
        subprocess.run(cmd, capture_output=True, timeout=5)
    except Exception:
        logger.debug("keyclick play failed", exc_info=True)


def _icon_path() -> str | None:
    path = _CONFIG.get("icon_path") or _BUNDLED_ICON
    path = os.path.expanduser(path)
    if os.path.exists(path):
        return path
    return None


def _run_notifier(
    binary: str,
    title: str,
    message: str,
    icon: str | None = None,
    app_name: str = "Hermes",
    urgency: str = "normal",
    expire: int = 0,
) -> bool:
    if not shutil.which(binary):
        return False
    cmd = [binary, "-a", app_name]
    if icon:
        cmd += ["-i", icon]
    cmd += ["-u", urgency, "-t", str(expire), title, message]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


_MIRROR_URL = os.environ.get("HERMES_NOTIFY_MIRROR", "").strip()


def _mirror_notification(
    *,
    title: str,
    message: str,
    icon: str | None,
    app_name: str,
    urgency: str,
    expire: int,
    source: str,
) -> None:
    """Best-effort mirror of the notification to a local dashboard for visual testing.

    Gated by the HERMES_NOTIFY_MIRROR env var. Runs off the hot path in a daemon
    thread; any failure is swallowed so production notifications are unaffected.
    """
    if not _MIRROR_URL:
        return

    payload = {
        "title": title,
        "message": message,
        "icon": icon,
        "app_name": app_name,
        "urgency": urgency,
        "expire": expire,
        "source": source,
    }
    try:
        data = json.dumps(payload).encode("utf-8")
    except Exception:
        logger.debug("notify mirror encode failed", exc_info=True)
        return

    def _post() -> None:
        try:
            req = urllib.request.Request(
                _MIRROR_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            logger.debug("notify mirror post failed", exc_info=True)

    threading.Thread(target=_post, daemon=True).start()


def _echo_to_stderr(title: str, message: str) -> None:
    print(f"[hermes-linux-notify] {title}: {message}", file=sys.stderr)


def send_notification(
    title: str,
    message: str,
    icon: str | None = None,
    app_name: str = "Hermes",
    urgency: str = "normal",
    expire: int = 0,
    source: str = "",
) -> int | None:
    """Send a desktop notification. Returns the D-Bus notification id when the
    D-Bus path is used (so callers can auto-close it), else None."""
    threading.Thread(target=_play_keyclick, daemon=True).start()

    if icon is None:
        icon = _icon_path()

    _mirror_notification(
        title=title,
        message=message,
        icon=icon,
        app_name=app_name,
        urgency=urgency,
        expire=expire,
        source=source,
    )

    notif_id = dbus_notify.notify(
        app_name=app_name,
        icon=icon or "",
        summary=title,
        body=message,
        urgency=urgency,
        expire=expire,
    )
    if notif_id is not None:
        return notif_id

    if _run_notifier("notify-send", title, message, icon=icon, app_name=app_name, urgency=urgency, expire=expire):
        return None

    _echo_to_stderr(title, message)
    return None


def close_notification(notif_id: int) -> None:
    """Auto-close a previously sent notification by its D-Bus id."""
    dbus_notify.close(notif_id)
