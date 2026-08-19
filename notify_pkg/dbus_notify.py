from __future__ import annotations

import asyncio
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from dbus_fast.aio import MessageBus
    from dbus_fast import Variant

    HAVE_DBUS_FAST = True
except Exception:  # pragma: no cover - optional dependency
    HAVE_DBUS_FAST = False

_NOTIF_BUS = "org.freedesktop.Notifications"
_NOTIF_PATH = "/org/freedesktop/Notifications"

_URGENCY = {"low": 0, "normal": 1, "critical": 2}


def notify(
    *,
    app_name: str = "Hermes",
    icon: str = "",
    summary: str,
    body: str,
    urgency: str = "normal",
    expire: int = 0,
) -> Optional[int]:
    """Send a desktop notification over D-Bus and return its id (or None).

    Runs on a daemon thread with its own asyncio loop so it can be called from
    the synchronous plugin hooks. Returns None when dbus-fast is missing or the
    bus/daemon is unavailable — callers fall back to notify-send.
    """
    if not HAVE_DBUS_FAST:
        return None

    box: dict[str, object] = {}

    def _worker() -> None:
        try:
            box["id"] = asyncio.run(
                _send(app_name, icon, summary, body, urgency, expire)
            )
        except Exception:
            logger.debug("dbus notify failed", exc_info=True)
            box["id"] = None

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=5)
    result = box.get("id")
    return int(result) if isinstance(result, int) else None


async def _send(
    app_name: str, icon: str, summary: str, body: str, urgency: str, expire: int
) -> Optional[int]:
    bus = await MessageBus().connect()
    try:
        introspection = await bus.introspect(_NOTIF_BUS, _NOTIF_PATH)
        proxy = bus.get_proxy_object(_NOTIF_BUS, _NOTIF_PATH, introspection)
        iface = proxy.get_interface(_NOTIF_BUS)
        hints = {"urgency": Variant("y", _URGENCY.get(urgency, 1))}
        nid = await iface.call_notify(
            app_name, 0, icon or "", summary, body, [], hints, expire
        )
        return int(nid)
    finally:
        try:
            bus.disconnect()
        except Exception:
            pass


def close(notif_id: int) -> None:
    """Best-effort programmatic close of a notification by id."""
    if not HAVE_DBUS_FAST or not isinstance(notif_id, int):
        return

    def _worker() -> None:
        try:
            asyncio.run(_close(notif_id))
        except Exception:
            logger.debug("dbus close failed", exc_info=True)

    threading.Thread(target=_worker, daemon=True).start()


async def _close(notif_id: int) -> None:
    bus = await MessageBus().connect()
    try:
        introspection = await bus.introspect(_NOTIF_BUS, _NOTIF_PATH)
        proxy = bus.get_proxy_object(_NOTIF_BUS, _NOTIF_PATH, introspection)
        iface = proxy.get_interface(_NOTIF_BUS)
        await iface.call_close_notification(notif_id)
    finally:
        try:
            bus.disconnect()
        except Exception:
            pass
