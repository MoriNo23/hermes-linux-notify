# Using the GLib main loop instead of asyncio in dbus_next

`dbus_next` supports a GLib-backed main loop as an alternative to asyncio —
useful when integrating with an existing GTK app that already runs
`Gtk.main()` / a `GLib.MainLoop`.

```python
from dbus_next.glib import MessageBus

bus = MessageBus().connect_sync()
introspection = bus.introspect_sync(
    "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
)
proxy = bus.get_proxy_object(
    "org.freedesktop.Notifications", "/org/freedesktop/Notifications", introspection
)
notifications = proxy.get_interface("org.freedesktop.Notifications")
notifications.call_notify_sync(
    "MyApp", 0, "", "Hello", "Body", [], {}, 5000
)
```

Note the `_sync` suffix on every call in this mode — the GLib variant is
blocking-style by design, not callback-based, even though it integrates
with GLib's event loop under the hood. Requires `PyGObject` installed
separately (`python3-gi` on Debian) — `dbus_next` does not pull it in as a
dependency, so a `glib` import failing with `ModuleNotFoundError: gi` means
that package is missing, not a dbus_next bug.

Mixing this with asyncio in the same process is not supported — pick one
main loop per process.
