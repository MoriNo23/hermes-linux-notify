#!/usr/bin/env python3
"""
Smoke test for dbus-python (1.4.0, the `dbus` module): confirms the C
extension imports and a live Notify() call works.

Usage: python3 smoke_test.py
Exit code 0 = all good. Non-zero = see printed diagnosis.
"""
import sys


def fail(msg: str, code: int = 1):
    print(f"[FAIL] {msg}")
    sys.exit(code)


def main():
    try:
        import dbus
    except ImportError as e:
        fail(
            f"dbus module not importable ({e}). This is a C extension — "
            "`pip install dbus-python` requires libdbus-1-dev + pkg-config + "
            "a C compiler at build time. On Debian: "
            "`sudo apt install libdbus-1-dev libglib2.0-dev pkg-config "
            "build-essential && pip install dbus-python==1.4.0`. Prefer the "
            "distro package `python3-dbus` when possible to skip the build."
        )

    try:
        bus = dbus.SessionBus()
    except Exception as e:
        fail(
            f"Could not connect to session bus ({e}). Check that "
            "$DBUS_SESSION_BUS_ADDRESS is set and a session bus is running."
        )

    try:
        notify_obj = bus.get_object(
            "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
        )
        notify_iface = dbus.Interface(notify_obj, "org.freedesktop.Notifications")
    except Exception as e:
        fail(
            f"No notification daemon owns org.freedesktop.Notifications ({e}). "
            "Check `busctl --user list | grep -i notif` — on Hyprland/minimal "
            "WM setups no daemon runs by default."
        )

    try:
        notif_id = notify_iface.Notify(
            "dbus-python-smoke-test",
            0,
            "dialog-information",
            "dbus-python smoke test",
            "If you see this, dbus-python + your notification daemon both work.",
            [],
            {},
            4000,
        )
        print(f"[OK] Notify() succeeded, id={notif_id}")
    except Exception as e:
        fail(f"Notify() call failed ({e}).")

    print("[OK] dbus-python environment looks healthy.")


if __name__ == "__main__":
    main()
