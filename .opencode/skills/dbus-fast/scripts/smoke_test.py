#!/usr/bin/env python3
"""
Smoke test for dbus_fast (5.0.22): confirms the library imports, a session
bus connection can be made, and a live Notify() round-trip works.

Usage: python3 smoke_test.py
Exit code 0 = all good. Non-zero = see printed diagnosis.
"""
import asyncio
import sys


def fail(msg: str, code: int = 1):
    print(f"[FAIL] {msg}")
    sys.exit(code)


async def main():
    try:
        from dbus_fast.aio import MessageBus
        from dbus_fast import Variant
    except ImportError as e:
        fail(
            f"dbus_fast not importable ({e}). Install with: "
            "pip install dbus-fast==5.0.22"
        )

    try:
        bus = await MessageBus().connect()
    except Exception as e:
        fail(
            f"Could not connect to session bus ({e}). Check that "
            "$DBUS_SESSION_BUS_ADDRESS is set and a session bus is running "
            "(dbus-launch / systemd --user)."
        )

    try:
        introspection = await bus.introspect(
            "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
        )
        proxy = bus.get_proxy_object(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
            introspection,
        )
        notifications = proxy.get_interface("org.freedesktop.Notifications")
    except Exception as e:
        fail(
            f"No notification daemon owns org.freedesktop.Notifications ({e}). "
            "Check `busctl --user list | grep -i notif` — on Hyprland/minimal "
            "WM setups no daemon runs by default (dunst, mako, etc. must be "
            "started separately)."
        )

    try:
        notif_id = await notifications.call_notify(
            "dbus-fast-smoke-test",
            0,
            "dialog-information",
            "dbus_fast smoke test",
            "If you see this, dbus_fast + your notification daemon both work.",
            [],
            {"urgency": Variant("y", 1)},
            4000,
        )
        print(f"[OK] Notify() succeeded, id={notif_id}")
    except Exception as e:
        fail(f"Notify() call failed ({e}).")

    print("[OK] dbus_fast environment looks healthy.")


if __name__ == "__main__":
    asyncio.run(main())
