from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading

logger = logging.getLogger(__name__)

_BUNDLED_SOUND = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "sounds", "keyclick.wav"
)

_DEFAULTS = {"sound_enabled": True, "sound_path": "", "sound_volume": 100}


def _load_config() -> dict:
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin.yaml")
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


def _run_notifier(
    binary: str,
    title: str,
    message: str,
    urgency: str = "normal",
    expire: int = 5000,
) -> bool:
    if not shutil.which(binary):
        return False
    try:
        r = subprocess.run(
            [binary, "-u", urgency, "-t", str(expire), title, message],
            capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def _echo_to_stderr(title: str, message: str) -> None:
    print(f"[hermes-linux-notify] {title}: {message}", file=sys.stderr)


def send_notification(title: str, message: str) -> None:
    threading.Thread(target=_play_keyclick, daemon=True).start()

    if _run_notifier("notify-send", title, message):
        return

    if _run_notifier("dunstify", title, message):
        return

    _echo_to_stderr(title, message)
