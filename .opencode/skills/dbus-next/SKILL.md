---
name: dbus-next
description: Use when writing, debugging, or reviewing Python code that imports dbus_next (package name dbus-next, PyPI/altdesktop, current pinned version 0.2.3) — asyncio-native D-Bus client/service library. Trigger on "dbus_next", "python-dbus-next", "MessageBus().connect()", asyncio + D-Bus, or when the user is building a service/client against org.freedesktop.Notifications, BlueZ, MPRIS, systemd, or any session/system bus interface in Python with asyncio. Also trigger if dbus-fast comes up as an alternative — dbus-next is the unmaintained ancestor dbus-fast forked from, and the user should usually be steered to dbus-fast unless they have a specific reason (existing codebase, pinned dependency) to stay on dbus-next.
compatibility: Python 3.7+, zero external dependencies, asyncio or GLib main loop. Pairs with dbus-notifications-spec for the Notify() contract.
---

# python-dbus-next (dbus_next) — 0.2.3

## Read this first: maintenance status

As of this writing, altdesktop/python-dbus-next has an **open, unanswered
issue literally titled "Dead repository?"** (#168, Feb 2025) and no tagged
release since **v0.2.3 (Jul 2021)**. 0.2.3 is also the last version — there
is nothing newer to upgrade to on this project. It still works and is
Debian/Arch packaged, but:

- **Recommend `dbus-fast` instead for any new project.** It's a maintained
  fork with the same API surface (mostly drop-in: `import dbus_fast` instead
  of `import dbus_next`, few signature changes) plus an optional Cython
  speedup. See the sibling `dbus-fast` skill.
- Only stay on `dbus_next` if the user has an existing codebase already
  depending on it and no compelling reason to migrate, or a transitive
  dependency pins it.

## Installation

```bash
pip install dbus-next==0.2.3
# or via distro package: python3-dbus-next (Debian/Ubuntu), python-dbus-next (Arch)
```

Zero native/C dependencies — pure Python, so no build toolchain issues like
`dbus-python` has. This is dbus-next's main practical advantage over
`dbus-python` even setting aside asyncio.

## Two API layers

1. **High-level client** — proxy objects via introspection (`get_proxy_object`)
2. **High-level service** — `ServiceInterface` + decorators to export methods
3. **Low-level** — raw `Message` construction, for talking directly to the
   bus daemon or building your own abstraction (rarely needed)

## Minimal client example — calling Notify

```python
from dbus_next.aio import MessageBus
from dbus_next import Variant
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

Two things that trip people up every time:

- **Method names on the proxy are `call_<method_name_snake_case>`.**
  `Notify` becomes `call_notify`, `GetCapabilities` becomes
  `call_get_capabilities`. Forgetting the `call_` prefix or not
  snake_casing is the single most common first-run error.
- **Every hint value must be wrapped in `Variant(signature, value)`.**
  Passing a bare Python value into the hints dict raises a marshalling
  error, not a silent failure — read the traceback, it usually names the
  exact key that's unwrapped.

## Minimal service example — exporting an interface

```python
from dbus_next.service import ServiceInterface, method, signal
from dbus_next.aio import MessageBus
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
    await asyncio.Event().wait()  # run forever

asyncio.run(main())
```

Type annotations use raw D-Bus signature strings (`"s"`, `"u"`, `"a{sv}"`),
not Python types — this is a common point of confusion coming from normal
Python type hints.

## Known open issues to watch for (from the tracker, still unresolved)

- **#167 — "properties must have a single complete type."** Hits people
  exporting a `ServiceInterface` property whose D-Bus signature is
  ambiguous/compound; if this exact error appears, simplify the property's
  signature or check the container types being passed rather than assuming
  it's a bug in the caller's business logic.
- **#165 — logs an error + full traceback to stderr when another program
  queries an unknown property** on an exported service, even though this is
  normal/expected D-Bus behavior. Don't mistake this log spam for an actual
  crash — the process keeps running. If it's polluting a systemd journal
  meaningfully, wrap property access to fail cleanly instead.
- **#162 — UNIX FD leaks** when passing file descriptors over D-Bus (e.g.
  logind `Inhibit()` calls). If the workflow passes FDs, monitor
  `/proc/<pid>/fd` count over time.
- **#153 — asyncio write callback terminates the connection on EAGAIN**
  instead of retrying, under backpressure. Can surface as unexplained
  disconnects on a busy bus. If connections drop under load with no other
  explanation, this is a likely cause — no upstream fix exists.
- **#157 — does not work on Windows** (by design; D-Bus is a Linux/Unix
  IPC mechanism). If the user is targeting Windows, this whole family of
  libraries (dbus-next, dbus-fast, pydbus, dbus-python) is the wrong tool
  entirely — say so plainly rather than debugging around it.

None of these are Mori's-machine-specific (Sandy Bridge/i5-2430M has no
bearing on D-Bus behavior) — they're upstream library bugs, listed here so
they're recognized immediately instead of re-diagnosed from scratch.

## See also

- `dbus-notifications-spec` skill for the Notify() contract this example targets
- `dbus-fast` skill — the maintained fork, prefer it for new code
- `references/glib-mainloop.md` — using the GLib main loop instead of asyncio
