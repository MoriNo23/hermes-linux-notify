# Full method list — org.freedesktop.Notifications (v1.2)

## Methods

### Notify
See SKILL.md — the main entry point.

### CloseNotification
```
void CloseNotification(UINT32 id)
```
Ask the server to close a notification programmatically (not user-initiated).
Triggers a `NotificationClosed` signal with reason=3. No-op / silently
ignored by some servers if `id` is unknown or already closed — don't treat
the absence of an error as confirmation the notification was actually open.

### GetCapabilities
```
ARRAY GetCapabilities(void) → as
```
See SKILL.md.

### GetServerInformation
```
GetServerInformation(out STRING name,
                      out STRING vendor,
                      out STRING version,
                      out STRING spec_version)
```
`spec_version` should be `"1.2"` for a compliant server, but older or
partial implementations sometimes report `"1.1"` or omit it — treat a
missing/blank spec_version as "assume the conservative subset of the spec,
don't assume optional hints work."

## NotificationClosed reason enum

| Value | Meaning |
|-------|---------|
| 1 | Notification expired (timeout reached) |
| 2 | Notification dismissed by the user |
| 3 | Closed by a call to `CloseNotification` |
| 4 | Undefined/reserved — some servers use this as a catch-all; don't branch logic on it meaning anything specific |

## Urgency enum (byte, in hints["urgency"])

| Value | Meaning |
|-------|---------|
| 0 | Low |
| 1 | Normal (default if omitted) |
| 2 | Critical — spec says servers *may* choose not to auto-expire these |

## Standard categories (non-exhaustive, dot-namespaced)

`device`, `device.added`, `device.error`, `device.removed`, `email`,
`email.arrived`, `email.bounced`, `im`, `im.error`, `im.received`, `network`,
`network.connected`, `network.disconnected`, `network.error`, `presence`,
`presence.offline`, `presence.online`, `transfer`, `transfer.complete`,
`transfer.error`.

Custom categories are legal (`x-myapp.custom-thing` is the historically
recommended prefix convention for unregistered categories, mirroring the
X11 property naming convention) — servers that don't recognize a category
just treat the notification generically. Never assume a custom category
gets special routing on a server you don't control.
