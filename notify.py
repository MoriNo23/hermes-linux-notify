from __future__ import annotations

import logging
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


def _notify_send(
    title: str,
    message: str,
    urgency: str = "normal",
    expire: int = 5000,
) -> bool:
    if not shutil.which("notify-send"):
        return False
    try:
        r = subprocess.run(
            ["notify-send", "-u", urgency, "-t", str(expire), title, message],
            capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def _dunstify(
    title: str,
    message: str,
    urgency: str = "normal",
    expire: int = 5000,
) -> bool:
    if not shutil.which("dunstify"):
        return False
    try:
        r = subprocess.run(
            ["dunstify", "-u", urgency, "-t", str(expire), title, message],
            capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def _echo_to_stderr(title: str, message: str) -> None:
    print(f"[hermes-linux-notify] {title}: {message}", file=sys.stderr)


def send_notification(title: str, message: str) -> None:
    if _notify_send(title, message):
        return

    if _dunstify(title, message):
        return

    _echo_to_stderr(title, message)
