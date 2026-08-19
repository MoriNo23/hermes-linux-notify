# Using the GLib main loop instead of asyncio in dbus_fast

Same shape as dbus_next's GLib variant (see the `dbus-next` skill's
equivalent reference if migrating):

```python
from dbus_fast.glib import MessageBus

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

Requires `PyGObject` (`gi`) installed separately — same caveat as dbus_next:
this is not pulled in as a dependency automatically. Use this mode only
when integrating with an existing GTK/GLib event loop; for anything new,
prefer the asyncio (`dbus_fast.aio`) mode shown in SKILL.md, since it needs
no extra system package and composes naturally with the rest of a modern
async Python codebase.
