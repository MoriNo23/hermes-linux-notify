#!/usr/bin/env python3
"""
Smoke test for pydbus (0.6.0): confirms PyGObject + pydbus import cleanly
and a live Notify() call works.

Usage: python3 smoke_test.py
Exit code 0 = all good. Non-zero = see printed diagnosis.
"""
import sys


def fail(msg: str, code: int = 1):
    print(f"[FAIL] {msg}")
    sys.exit(code)


def main():
    try:
        import gi  # noqa: F401
    except ImportError:
        fail(
            "PyGObject (gi) is not installed. This is required by pydbus and "
            "is NOT pulled in by `pip install pydbus`. Install via distro "
            "package: `sudo apt install python3-gi` (Debian) or "
            "`sudo pacman -S python-gobject` (Arch)."
        )

    try:
        from pydbus import SessionBus
    except ImportError as e:
        fail(f"pydbus not importable ({e}). Install with: pip install pydbus==0.6.0")

    try:
        bus = SessionBus()
    except Exception as e:
        fail(
            f"Could not connect to session bus ({e}). If this is "
            "'g-spawn-exit-error-quark', no session bus could be autospawned "
            "— check `dbus-run-session` or that you're in a full desktop "
            "session, not a bare headless shell."
        )

    try:
        notifications = bus.get(".Notifications")
    except Exception as e:
        fail(
            f"No notification daemon owns org.freedesktop.Notifications ({e}). "
            "Check `busctl --user list | grep -i notif` — on Hyprland/minimal "
            "WM setups no daemon runs by default."
        )

    try:
        notif_id = notifications.Notify(
            "pydbus-smoke-test",
            0,
            "dialog-information",
            "pydbus smoke test",
            "If you see this, pydbus + your notification daemon both work.",
            [],
            {},
            4000,
        )
        print(f"[OK] Notify() succeeded, id={notif_id}")
    except Exception as e:
        fail(f"Notify() call failed ({e}).")

    print("[OK] pydbus environment looks healthy.")


if __name__ == "__main__":
    main()
