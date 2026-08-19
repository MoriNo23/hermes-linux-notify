---
name: pydbus
description: Use when writing, debugging, or reviewing Python code that imports pydbus (PyPI package pydbus, current pinned version 0.6.0, by LEW21) — a GLib/GObject-Introspection-based "Pythonic" D-Bus library built on PyGI. Trigger on "pydbus", "SessionBus()/SystemBus() from pydbus", ".get('.Notifications')" bus-alias syntax, or when the user wants the terse pydbus calling convention specifically. Also trigger to warn the user away from pydbus toward dbus-next/dbus-fast when they're starting a new asyncio project, since pydbus requires GLib's main loop and has had no releases since 2019.
compatibility: Python 2.7+ or 3.4+, REQUIRES PyGObject (gi) and GLib/girepository >= 2.46 installed at the OS level — not pip-installable on its own, must come from distro packages (python3-gi / python-gobject on Debian/Arch).
---

# pydbus — 0.6.0

## Read this first: project status

pydbus (LEW21/pydbus) has had **no release since 0.6.0 (2017)** and no
commits addressing open issues in years — issues from 2018-2021 (#82
through #99) remain open and unanswered. It is not formally deprecated by
its author, but it is not actively maintained either. Recommend it only
when the user specifically wants its terse calling syntax for a quick
script, or is maintaining existing code already built on it. For anything
new and asyncio-based, point to `dbus-fast` instead.

## Hard dependency: PyGObject, not pip-installable alone

```bash
# Debian/Ubuntu
sudo apt install python3-gi
pip install pydbus==0.6.0

# Arch
sudo pacman -S python-gobject
pip install pydbus==0.6.0
```

`pip install pydbus` alone will succeed but importing it will fail with
`ModuleNotFoundError: No module named 'gi'` unless PyGObject is separately
present — this is the #1 first-run failure and is NOT a pydbus bug, it's
documented upstream behavior (PyGI intentionally isn't on PyPI). Always
check for `python3 -c "import gi"` succeeding before debugging anything
else in a pydbus failure.

## Minimal example — the whole appeal of pydbus is this brevity

```python
from pydbus import SessionBus

bus = SessionBus()
notifications = bus.get('.Notifications')  # short alias, resolves to
                                            # org.freedesktop.Notifications
notifications.Notify(
    'MyApp', 0, 'dialog-information', 'Hello', 'pydbus works :)',
    [], {}, 5000
)
```

The `.Notifications` shorthand only works because pydbus special-cases the
`org.freedesktop` prefix for bus names starting with `.` — `bus.get('.systemd1')`
similarly resolves to `org.freedesktop.systemd1`. For anything outside that
namespace, pass the full bus name string.

## Publishing a service

```python
from pydbus import SessionBus
from gi.repository import GLib

class Demo:
    """
    <node>
      <interface name='com.example.Demo'>
        <method name='Echo'>
          <arg type='s' name='what' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
      </interface>
    </node>
    """
    def Echo(self, what):
        return what

bus = SessionBus()
bus.publish("com.example.Demo", Demo())
GLib.MainLoop().run()
```

Note the **XML introspection docstring** — this is pydbus's mechanism for
declaring the D-Bus interface, unlike dbus-next/dbus-fast's Python
decorators. It's easy to get the XML subtly wrong (mismatched arg count,
wrong direction) with no helpful error at import time — errors typically
only surface when a client actually calls the mismatched method. Validate
the docstring XML carefully against the actual method signature when
debugging a "method not found" or marshalling error from a client.

## GLib main loop is mandatory for signals/services

pydbus is built entirely on `Gio.DBusConnection` via PyGI, so any service,
or any client that needs to receive signals (not just make blocking calls),
requires a running `GLib.MainLoop`. A script that only calls methods
synchronously (like the Notify example above) doesn't need one — but the
moment signal subscriptions (`.SomeSignal.connect(...)`) are added, a
`GLib.MainLoop().run()` (or equivalent, e.g. inside a GTK app already
running one) becomes mandatory or the callback will simply never fire.

## Known open issues to watch for

- **#42 — UNIX file descriptors not returned correctly.** `Inhibit()`-style
  calls (systemd-logind power management, etc.) that should return a raw FD
  come back as `0` instead of a usable descriptor. `dbus-python` handles
  this correctly per the same issue thread — if a workflow specifically
  needs FD-passing (inhibitor locks, memfd handoff), steer away from pydbus
  entirely rather than trying to work around this.
- **#76 — `GLib.Error: g-spawn-exit-error-quark` on `SessionBus()`** when no
  session bus is already running and `dbus-launch` can't autospawn one
  (common on headless boxes, containers, or minimal window manager setups
  without a full desktop session). Fix is ensuring `dbus-launch` /
  `dbus-run-session` actually starts a session bus before the script runs —
  not a pydbus-side fix.
- **#65 — no built-in guidance for catching D-Bus method errors** cleanly;
  they surface as `GLib.Error` with a `g-io-error-quark` domain and the
  original D-Bus error name embedded in the message string, not as a typed
  Python exception per D-Bus error name. When writing error handling,
  catch `GLib.Error` broadly and parse/match against `e.message` rather
  than expecting per-error-type exception classes.

None of these are specific to a low-RAM/older-CPU machine — they're
upstream library gaps, not performance issues.

## See also

- `dbus-notifications-spec` skill for the Notify() contract shown above
- `dbus-fast` skill — recommended default for new asyncio work
- `references/introspection-xml-gotchas.md` — deeper dive on the XML docstring format
