---
name: dbus-python
description: Use when writing, debugging, or reviewing Python code that imports the "dbus" module from the dbus-python package (PyPI dbus-python, current pinned version 1.4.0) — the original libdbus-based C-extension Python binding, hosted at gitlab.freedesktop.org/dbus/dbus-python. Trigger on "dbus-python", "import dbus" (the bare "dbus" module, not dbus_next/dbus_fast), "dbus.SessionBus()", "dbus.service.method", "dbus.mainloop.glib", or build errors mentioning "_dbus_bindings", "dbus-1 &gt;= 1.6", or "pkg-config dbus-1". This is the oldest and most legacy of the four bindings — actively steer new projects toward dbus-fast unless there's a hard reason to use this one (an existing large codebase, a system tool that must avoid any dependency beyond what's in base Debian/RHEL repos).
compatibility: Python 2.7+ or 3.4+, REQUIRES a C compiler + libdbus-1-dev + pkg-config at build/install time (not a pure-Python wheel on most platforms) — building from source without these fails immediately.
---

# dbus-python — 1.4.0

## Read this first: upstream's own recommendation

The official dbus-python documentation, written by its own maintainer,
says this in its own words (paraphrased, not a direct quote — see the
project's docs for the exact wording): dbus-python may not be the best
D-Bus binding to reach for. It doesn't follow the "refuse the temptation
to guess" principle other bindings follow and can't be changed to without
breaking compatibility, it wraps libdbus (which has known problems under
multi-threaded use), and it forces the caller to choose and wire up a
compatible main loop rather than working out of the box. The same docs
point people instead toward GDBus/PyGI (i.e. pydbus's foundation),
`dasbus`, `jeepney`, or `txdbus` depending on the use case.

**Practical takeaway for this skillset: recommend `dbus-fast` for new
Python code.** Recommend `dbus-python` specifically only when: the target
system's distro packaging already includes it as a base dependency (many
system tray tools, NetworkManager applets, and older Linux utilities
assume it's present) and adding a new pip dependency is undesirable, or
existing code already depends on it.

## Installation — the #1 real-world failure mode

`dbus-python` is a **C extension** requiring `libdbus-1-dev` and
`pkg-config` at build time. `pip install dbus-python` on a system missing
these fails with an error like:

```
checking for DBUS... no
configure: error: Package requirements (dbus-1 >= 1.6) were not met:
No package 'dbus-1' found
```

This is not a broken package — it's a missing system dependency. Fix:

```bash
# Debian/Ubuntu
sudo apt install libdbus-1-dev libglib2.0-dev pkg-config build-essential
pip install dbus-python==1.4.0

# Arch
sudo pacman -S dbus pkgconf base-devel
pip install dbus-python==1.4.0
```

Prefer the distro package (`python3-dbus` on Debian) when possible — it
comes prebuilt and avoids the whole toolchain requirement.

## Minimal client example — calling Notify

```python
import dbus

bus = dbus.SessionBus()
notify_obj = bus.get_object('org.freedesktop.Notifications',
                             '/org/freedesktop/Notifications')
notify_iface = dbus.Interface(notify_obj, 'org.freedesktop.Notifications')
notify_iface.Notify(
    'MyApp', 0, 'dialog-information', 'Hello', 'dbus-python works',
    [], {}, 5000
)
```

Note there's no `Variant` wrapper class needed for hints here the way
dbus-next/dbus-fast require — dbus-python infers D-Bus types from Python
types by default (the "guessing" behavior its own docs warn about). This
is convenient until it silently guesses wrong (e.g. an int that should be
`int32` gets sent as `int16` and a strict server rejects it) — for
precise control, wrap ambiguous values explicitly with `dbus.Int32(...)`,
`dbus.UInt32(...)`, `dbus.Byte(...)`, etc. from the `dbus.types` module
rather than trusting inference on anything but plain strings.

## Main loop wiring — required before ANY signal handling

Unlike the asyncio-native bindings, dbus-python needs an explicit main
loop set **before the first `Bus()` is constructed**, or signal delivery
silently doesn't work:

```python
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)   # must happen before dbus.SessionBus()

import dbus
from gi.repository import GLib

bus = dbus.SessionBus()
bus.add_signal_receiver(
    lambda id, reason: print(f"closed: {id} {reason}"),
    signal_name="NotificationClosed",
    dbus_interface="org.freedesktop.Notifications"
)
GLib.MainLoop().run()
```

Constructing `dbus.SessionBus()` before calling `DBusGMainLoop(set_as_default=True)`
is a very common mistake that produces no error — signals just never
arrive, silently, which makes it a frustrating one to debug without
knowing this ordering requirement up front.

## Known issues / gotchas from the tracker (gitlab.freedesktop.org/dbus/dbus-python)

- **#8 — segfault** reported under certain object-path-handler cleanup
  paths in older 1.2.x; upgrading to 1.4.0 (current) resolves known
  instances of this, but the underlying pattern (heavy dynamic
  registration/deregistration of object paths at runtime) is still worth
  avoiding where possible given the library wraps a C extension with known
  thread-safety caveats.
- **#26 — `NO_REPLY_EXPECTED` flag not honored** on older versions — fixed
  in the version line that became 1.4.0, but worth knowing if the user is
  on an older pinned version and sees unexpected `method_return` rejection
  messages in the system log for one-way calls.
- **#31 — `dbus.Int32.__str__` behavior changed between 1.2.10 and
  1.2.12+** under Python 3.8 — if code does string formatting/logging of
  raw `dbus.Int32`/similar wrapper types and output changed after an
  upgrade, this is why; cast to `int()` explicitly before formatting for
  stable output across versions.
- Threading: the docs' own warning about libdbus and multi-threaded use is
  not hypothetical — if the workflow needs D-Bus calls from multiple
  threads, either serialize them through a single thread that owns the
  connection, or use a different binding (dbus-fast's asyncio model
  sidesteps this class of bug entirely).

## See also

- `dbus-notifications-spec` skill for the Notify() contract shown above
- `dbus-fast` skill — recommended default for anything new
- `pydbus` skill — the GDBus/PyGI-based alternative the dbus-python docs
  themselves point toward
