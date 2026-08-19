# Classic org.freedesktop.Notifications vs org.freedesktop.portal.Notification

If the target app runs inside Flatpak, Snap (strict confinement), or any
sandboxed environment, it likely cannot see the session-bus name
`org.freedesktop.Notifications` directly — it must go through the XDG
Desktop Portal instead:

- Bus name: `org.freedesktop.portal.Desktop`
- Object path: `/org/freedesktop/portal/desktop`
- Interface: `org.freedesktop.portal.Notification`
- Method: `AddNotification(STRING id, DICT notification)` — note: **caller
  picks the id (a string, not server-assigned)**, and the dict shape is
  different from the classic `Notify` hints dict (keys like `title`, `body`,
  `icon`, `priority`, `buttons` instead of `summary`/`app_icon`/`hints`).
- Actions come back via `org.freedesktop.portal.Notification::ActionInvoked`
  signal, not the classic interface's signal of nearly the same name — don't
  conflate the two; they have different argument shapes.

For Mori's use case (native Linux desktop tooling, not sandboxed Flatpak
apps), the classic interface documented in SKILL.md is almost certainly the
right one — this file exists so an agent doesn't waste a debugging session
chasing "why doesn't my Notify call show up" when the actual answer is
"this binary is sandboxed and needs the portal path instead." Quick check:
`systemctl --user status xdg-desktop-portal` and `flatpak info <app>` (if
applicable) to confirm which path applies before assuming classic.
