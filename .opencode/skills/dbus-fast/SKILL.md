---
name: dbus-fast
description: Use when writing, debugging, or reviewing Python code that imports dbus_fast (PyPI package dbus-fast, current pinned version 5.0.22, maintained by the Bluetooth-Devices org / used by bleak and Home Assistant) — the actively-maintained, performance-focused fork of dbus_next, with an optional Cython acceleration extension. This is the DEFAULT recommendation for any new Python D-Bus work (asyncio or GLib), including org.freedesktop.Notifications clients/servers, BlueZ/bleak-style BLE work, MPRIS media players, or systemd interaction. Trigger on "dbus_fast", "dbus-fast", "python dbus asyncio", or whenever a user asks "which D-Bus library should I use" for new Python code — steer them here over dbus-next, pydbus, and dbus-python unless they have a specific reason to use one of those instead.
compatibility: Python 3.8+, zero required dependencies (optional Cython extension for speed, falls back to pure Python automatically if unavailable), asyncio or GLib main loop. API is near-drop-in compatible with dbus_next for basic usage.
---

# dbus-fast — 5.0.22

## Why this is the default recommendation

dbus_fast (Bluetooth-Devices/dbus-fast) is a maintained fork of the now
largely inactive `dbus_next` (see the `dbus-next` skill for that project's
"Dead repository?" status). It's the D-Bus library behind `bleak` (the
cross-platform BLE library) and is used by Home Assistant — meaning it
gets real production traffic and active maintenance, unlike the other
three bindings in this set. Releases land roughly monthly. For any new
Python D-Bus code with no legacy constraint, recommend this one by default.

## Installation

```bash
pip install dbus-fast==5.0.22
```

Zero required dependencies. An optional Cython-compiled extension speeds
up (un)marshalling — it's built automatically from source if a C toolchain
is present, or pip pulls a prebuilt wheel for common platforms. Falls back
to pure Python transparently if neither is available — this is not a hard
requirement, unlike dbus-python's mandatory build toolchain.

On Mori's machine (older Sandy Bridge CPU, Debian Trixie): if `pip install`
tries to compile the Cython extension from source and it's slow or flaky
on that hardware, `pip install dbus-fast --no-binary=:all:` is unnecessary
— just let pip pull the prebuilt manylinux wheel (default behavior) rather
than forcing a source build; there's no reason to compile locally unless
specifically debugging the extension itself.

## Minimal client example — calling Notify

```python
from dbus_fast.aio import MessageBus
from dbus_fast import Variant
import asyncio

async def main():
    bus = await MessageBus().connect()
    introspection = await bus.introspect(
        "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
    )
    proxy = bus.get_proxy_object(
        "org.freedesktop.Notifications", "/org/freedesktop/Notifications", introspection
    )
    notifications = proxy.get_interface("org.freedesktop.Notifications")

    notif_id = await notifications.call_notify(
        "MyApp", 0, "dialog-information", "Hello", "Body text",
        [], {"urgency": Variant("y", 1)}, 5000
    )
    print(notif_id)

asyncio.run(main())
```

This is intentionally near-identical to the `dbus_next` example — swapping
`dbus_next` for `dbus_fast` in imports is often the entire migration for
basic client code. Same `call_<snake_case_method>` proxy convention, same
`Variant(signature, value)` wrapping requirement for hints.

## Where the API diverges from dbus_next (check when porting)

- Newer releases added typed helper annotations (`DBusStr`, `DBusDict`,
  etc. from `dbus_fast.annotations`) as an alternative to raw D-Bus
  signature strings in `@method()` decorators — optional, not required,
  but worth using in new code for better editor/type-checker support.
- Property/variant marshalling internals were rewritten for performance;
  if porting code that pokes at `dbus_next` internals (not just the public
  API), expect breakage — public high-level API usage ports cleanly.

## Minimal service example — exporting an interface

```python
from dbus_fast.service import ServiceInterface, method, signal
from dbus_fast.aio import MessageBus
import asyncio

class ExampleInterface(ServiceInterface):
    def __init__(self):
        super().__init__("com.example.Interface")

    @method()
    def Echo(self, what: "s") -> "s":
        return what

    @signal()
    def SomethingHappened(self) -> "s":
        return "details"

async def main():
    bus = await MessageBus().connect()
    bus.export("/com/example/Path", ExampleInterface())
    await bus.request_name("com.example.Name")
    await asyncio.Event().wait()

asyncio.run(main())
```

## Known issues / gotchas worth knowing before debugging from scratch

- **Binary-incompatibility errors after upgrading dbus-fast across a major
  version bump while other installed packages (notably `bleak`) pin an
  older range** — symptom looks like `dbus_fast.signature.Variant size
  changed, may indicate binary incompatibility. Expected N from C header,
  got M from PyObject`. This is a Cython ABI mismatch from having two
  incompatible dbus_fast versions' compiled artifacts on the path
  simultaneously (usually via a stale cached wheel or a venv that wasn't
  fully rebuilt). Fix: `pip install --force-reinstall --no-cache-dir
  dbus-fast==5.0.22` inside a clean virtualenv, and check with `pip show
  dbus-fast` that only one version is resolvable.
- **`bleak` pins a version range, not an exact pin** (historically
  `dbus-fast<3,>=1.83.0` style ranges, tightening over time) — if
  `dbus_fast` is a transitive dependency via `bleak` in the same project,
  confirm the direct pin (5.0.22) is actually compatible with whatever
  `bleak` version is installed rather than assuming; a version conflict
  here silently resolves to whichever pip picks, not necessarily 5.0.22.
- **PyPI project maintains an unusually large release cadence and package
  size** (Cython wheels across many platforms/Python versions) — if
  install is slow on a constrained connection or storage, that's expected
  packaging overhead, not a broken install.
- On Windows, `dbus_fast` has no meaningful functionality (same as every
  binding in this set — D-Bus doesn't exist there) — `bleak` conditionally
  imports it only on `platform_system == "Linux"`; if debugging a
  cross-platform tool, confirm the import is actually guarded the same way.

## See also

- `dbus-notifications-spec` skill for the Notify() contract shown above
- `dbus-next` skill — the unmaintained ancestor this forked from; only
  relevant for legacy-codebase context, not for new code
- `references/glib-mainloop.md` — GLib main loop variant (same shape as dbus_next's)
