---
name: dbus-notifications-spec
description: Reference for the org.freedesktop.Notifications D-Bus specification (v1.2) — the interface every Linux desktop notification daemon (dunst, mako, notification-thing, KDE, GNOME) implements. Use this skill whenever the user asks about the Notify() method signature, hints (urgency, category, image-data, resident, transient, sound-*), capabilities negotiation, ActionInvoked/NotificationClosed signals, notification IDs and replaces_id, markup support, or is writing/debugging ANY client or server (daemon) that talks to org.freedesktop.Notifications over D-Bus — regardless of which language or D-Bus binding is used. Also use this as the contract reference before writing code with dbus-next, pydbus, dbus-python, or dbus-fast against this interface. Trigger on "notification spec", "org.freedesktop.Notifications", "notify-send", "dunst", "libnotify", "desktop notification", "D-Bus Notify method".
compatibility: language-agnostic — this is a protocol reference, not a library. Pairs with dbus-next, dbus-fast, pydbus, or dbus-python skills for implementation.
---

# org.freedesktop.Notifications — Desktop Notifications Specification v1.2

This is the **contract**, not a library. Read this before writing client or server
code against `org.freedesktop.Notifications` in any language. Version 1.2 is what's
actually deployed everywhere (dunst, mako, GNOME Shell, KDE Plasma, xfce4-notifyd).
A "v2" draft (`org.freedesktop.Notification` on portals, singular) exists for the
XDG Desktop Portal path — see `references/portal-vs-classic.md` if the user's
environment is a Flatpak/sandboxed app instead of a plain session-bus daemon.

## Core facts an agent must get right

- **Bus name:** `org.freedesktop.Notifications`
- **Object path:** `/org/freedesktop/Notifications` (fixed, singular — do not invent
  per-notification paths)
- **Interface:** `org.freedesktop.Notifications`
- **Bus:** session bus, always. Never the system bus. This is the single most common
  mistake — a service on the system bus will simply never be found by clients calling
  `Notify` on the session bus, and vice versa.

## Notify method — exact signature

```
UINT32 Notify (
    STRING    app_name,        // can be "" — do not assume non-empty
    UINT32    replaces_id,     // 0 = new notification; non-zero = replace that ID
    STRING    app_icon,        // themed icon name OR file:// URI OR "" 
    STRING    summary,         // required, short
    STRING    body,            // may be "" ; markup subset allowed (see below)
    ARRAY     actions,         // as[] of (action_key, localized_label) pairs, flat
    DICT      hints,           // a{sv} — see hints table below
    INT32     expire_timeout   // ms; -1 = server default; 0 = never expire
)  →  returns UINT32 (the notification id, use for replaces_id / CloseNotification)
```

`actions` is a **flat** array: `["default", "Open", "cancel", "Dismiss"]`, i.e.
pairs concatenated, not an array of 2-tuples. This trips up almost every
first-time implementer — check this first when a client's action buttons
don't appear or the server rejects the call with a marshalling error.

## GetCapabilities → STRING ARRAY

Always call this before relying on optional behavior (actions, markup, sound,
persistence). A server that doesn't advertise `"actions"` in its capability
list will silently ignore the `actions` array — no error, buttons just won't
render. Never assume a capability; query it.

Standard capability tokens: `action-icons`, `actions`, `body`, `body-hyperlinks`,
`body-images`, `body-markup`, `icon-multi`, `icon-static`, `persistence`, `sound`.

## Key hints (the `a{sv}` dict) — most commonly needed

| Hint             | Type  | Notes |
|------------------|-------|-------|
| `urgency`        | byte  | 0=low, 1=normal, 2=critical. **Critical notifications should not auto-expire** — well-behaved servers ignore `expire_timeout` for urgency 2, but not all do; don't rely on it for anything safety-critical. |
| `category`       | string| dot-separated (`device.added`, `im.received`); servers may filter/route on this |
| `image-data`     | (iiibiiay) | raw pixel data struct — width, height, rowstride, has_alpha, bits_per_sample, channels, pixel data. Painful to build by hand; prefer `image-path` |
| `image-path`     | string| `file://` URI or icon-theme name — simplest way to show an icon, prefer this over `image-data` |
| `resident`       | bool  | ask server to keep the notification after an action is invoked, instead of closing it |
| `transient`      | bool  | bypass persistence and always be removed on close, even in servers with a history feature |
| `sound-file` / `sound-name` | string | explicit sound path or themed sound name, mutually exclusive with each other and with `suppress-sound` |
| `suppress-sound` | bool  | ask server not to play any sound for this one |
| `x` / `y`        | int32 | pixel position hint, both required together — rarely honored by modern compositors, don't design UX around it |

Hint values **must** be wrapped as D-Bus Variants (`sv` in the dict). Every
binding covered by the sibling skills (dbus-next, pydbus, dbus-python,
dbus-fast) has a different idiom for this — see each skill's reference for
the exact call shape.

## Signals a client should listen for

- `ActionInvoked(UINT32 id, STRING action_key)` — user clicked a named action button
- `NotificationClosed(UINT32 id, UINT32 reason)` — reason: 1=expired, 2=user
  dismissed, 3=closed via `CloseNotification()` call, 4=undefined/reserved
- (v1.2 draft-only, not universally implemented) `ActivationToken` — used by some
  servers for XDG activation tokens alongside `ActionInvoked`

A client that calls `Notify` and never listens for `NotificationClosed` will
leak notification IDs it can never clean up with `CloseNotification`, and
will never know if the user actually saw / dismissed / acted on it. If the
user's use case involves waiting on a user response (a confirm/cancel
dialog-style notification), the signal is not optional — spell that out
explicitly, since it's easy to write "fire and forget" `Notify` code that
silently drops the response path entirely.

## Markup

Only `<b>`, `<i>`, `<u>`, `<a href="">`, `<img src="" alt="">` are spec-legal,
and only when the server advertises the `body-markup` capability. Most
servers strip or escape anything else. Do not assume HTML.

## Known cross-implementation gotchas (from real bug trackers, not the spec text)

- **dunst / mako** ignore `x`/`y` positioning hints entirely — positioning is
  compositor-config-only in Wayland environments.
- Several servers (older `notification-daemon` forks) **log a traceback** if a
  client requests `GetCapabilities` before the service has finished
  registering on the bus at startup — a client racing a freshly (re)started
  daemon should retry with backoff rather than treat the first failure as fatal.
- `replaces_id` semantics differ subtly: some servers replace in place
  (same position), others re-insert at the top of the stack. Don't build UX
  that depends on visual position being preserved across a replace.
- Icon resolution (`app_icon` as a bare name like `"dialog-information"` vs a
  `file://` URI) depends on the icon theme installed on the *server's*
  machine, not the client's — this matters for remote/SSH scenarios.

## When the user's environment is Mori's (Sandy Bridge / Debian Trixie, Hyprland/Wayland)

No GPU-side implications here — Notify is a plain D-Bus method call, zero
graphics driver interaction. If a notification server crashes or hangs on
this machine, the cause is almost always the compositor's own notification
daemon (if using a minimal WM/Hyprland setup, confirm one is actually
running — `busctl --user list | grep -i notif` — since Hyprland ships no
daemon of its own and a bare Notify call from a client will simply time out
with no daemon owning the bus name).

## See also

- `references/full-signature-and-enums.md` — every method (`CloseNotification`,
  `GetServerInformation`), the full hints table, and the closed-reason enum
- Sibling skills for implementation: `dbus-next`, `dbus-fast`, `pydbus`, `dbus-python`
