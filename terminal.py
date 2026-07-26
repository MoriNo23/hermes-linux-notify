from __future__ import annotations

import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)

TERMINAL_NAMES: dict[str, str] = {
    "ghostty":        "Ghostty",
    "gnome-terminal": "GNOME Terminal",
    "konsole":        "Konsole",
    "kitty":          "kitty",
    "alacritty":      "Alacritty",
    "wezterm":        "WezTerm",
    "warp":           "Warp",
    "hyper":          "Hyper",
    "tabby":          "Tabby",
    "tilix":          "Tilix",
    "terminator":     "Terminator",
    "xfce4-terminal": "XFCE Terminal",
    "lxterminal":     "LXTerminal",
    "urxvt":          "urxvt",
    "st":             "st",
    "foot":           "foot",
    "deepin-terminal":"Deepin Terminal",
}

_CACHED_NAME: str | None = None


def detect_terminal_name() -> str | None:
    global _CACHED_NAME
    if _CACHED_NAME is not None:
        return _CACHED_NAME

    try:
        ppid = os.getppid()
        for _ in range(15):
            try:
                r = subprocess.run(
                    ["ps", "-p", str(ppid), "-o", "ucomm=", "-o", "ppid="],
                    capture_output=True, text=True, timeout=2,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                break

            line = r.stdout.strip()
            if not line:
                break
            parts = line.rsplit(maxsplit=1)
            if len(parts) != 2:
                break
            comm, next_ppid = parts
            name = comm.strip().lower()
            app = TERMINAL_NAMES.get(name)
            if app:
                _CACHED_NAME = app
                return app
            try:
                ppid = int(next_ppid)
            except ValueError:
                break
    except Exception:
        logger.debug("linux-notify: terminal detection failed", exc_info=True)

    return None


def focus_terminal_window(term_name: str | None) -> None:
    if term_name is None:
        return
    wmctrl = shutil.which("wmctrl")
    if wmctrl:
        try:
            subprocess.run(
                [wmctrl, "-a", term_name],
                capture_output=True, timeout=3,
            )
        except Exception:
            pass
    xdotool = shutil.which("xdotool")
    if xdotool:
        try:
            result = subprocess.run(
                [xdotool, "search", "--name", term_name],
                capture_output=True, text=True, timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                for wid in result.stdout.strip().split():
                    subprocess.run(
                        [xdotool, "windowactivate", wid],
                        capture_output=True, timeout=3,
                    )
        except Exception:
            pass
