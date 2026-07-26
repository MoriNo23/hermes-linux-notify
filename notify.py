from __future__ import annotations

import logging
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


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
    if _run_notifier("notify-send", title, message):
        return

    if _run_notifier("dunstify", title, message):
        return

    _echo_to_stderr(title, message)
