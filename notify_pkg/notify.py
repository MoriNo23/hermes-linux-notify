from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading

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
    expire: int = 5000,
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


def _echo_to_stderr(title: str, message: str) -> None:
    print(f"[hermes-linux-notify] {title}: {message}", file=sys.stderr)


def send_notification(
    title: str,
    message: str,
    icon: str | None = None,
    app_name: str = "Hermes",
    urgency: str = "normal",
    expire: int = 5000,
) -> None:
    threading.Thread(target=_play_keyclick, daemon=True).start()

    if icon is None:
        icon = _icon_path()

    if _run_notifier("notify-send", title, message, icon=icon, app_name=app_name, urgency=urgency, expire=expire):
        return

    _echo_to_stderr(title, message)
