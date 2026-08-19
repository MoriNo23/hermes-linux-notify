# AGENTS.md — hermes-linux-notify

Hermes CLI plugin (Python 3.8+) that fires Linux desktop notifications on
`post_llm_call`, `pre_tool_call` (clarify), and `pre_approval_request`.

## Layout / entrypoints
- Root `__init__.py` only re-exports `register` from the `notify_pkg` subpackage.
  All real logic lives in `notify_pkg/`.
- `notify_pkg/__init__.py` defines the hooks and calls `register(ctx)`.
- `notify_pkg/notify.py` = notification delivery + sound + dashboard mirror.
- `notify_pkg/session.py` = looks up the real session title from Hermes' SQLite DB
  (`~/.hermes/state.db`, overridable via `HERMES_HOME`); cached in memory.
- `notify_pkg/terminal.py` = terminal emulator detection (display only).

## Naming quirk (do not "fix")
The subpackage is intentionally named `notify_pkg`, NOT `hermes_linux_notify`.
The plugin dir name slugifies to `hermes_linux_notify`, which would collide with
pytest's package inference. Renaming it breaks the test import setup.

## Verify changes
- Python: `python3 -m pytest` (from repo root). Uses `import-mode=importlib`
  + `pythonpath=.`; `tests/conftest.py` puts the repo root on `sys.path` so
  `import notify_pkg`/`import session` resolve as top-level. No `python` alias
  on this machine — use `python3`.
- Tests only cover `session.py` (title lookup + cache + fallbacks). `notify.py`
  (subprocess/urllib) has no tests.
- Dashboard: `cd dashboard && npm test` (mocha) for `test/dashboard.test.js`.
  The Node server is stdlib-only (no runtime deps); don't add npm deps.

## Notification model (Linux desktop API limits)
- Delivery is **D-Bus primary** (`org.freedesktop.Notifications` via `dbus_fast`
  in `notify_pkg/dbus_notify.py`), falling back to `notify-send` → stderr.
  D-Bus is required for the auto-close feature (it returns the notification id).
  `dbus_fast` must be installed in the Hermes venv (`pip install dbus-fast`).
- Hierarchy is fixed by the API: **summary (título) = bold/large**,
  **body (mensaje) = normal**. Font-size tags are NOT supported on GNOME/KDE.
- Convention used here:
  - título = `Hermes - <session>` (or `Hermes`); the event category is shown
    bold at the top of the body: `Hermes pregunta` / `Confirmación requerida` /
    `Respuesta lista`
  - body = the question / description + `Comando:` etc.
  - body text is passed through `html.escape`; only `<br>` and `<b>`/`<i>` added.
- `app_name` is always `Hermes`. Urgency: `normal` (clarify) / `critical`
  (approval). Expire **0** (persistent) so it stays until the user interacts.
  Icon = bundled `assets/icon-128.png`.
- **Auto-close**: notifications opened by `pre_tool_call`(clarify) and
  `pre_approval_request` are tracked by `session_id` in `_pending` and closed by
  `post_tool_call`(clarify) / `post_approval_response` respectively.
- Sound: `paplay`/`aplay` on a daemon thread; terminal bell `\a` if neither exists.
- PyYAML is optional — `plugin.yaml` `config` is read lazily and falls back to
  defaults if PyYAML or the file is missing.

## Operational gotchas
- Hooks are imported at Hermes boot. **Any edit to the plugin requires a full
  Hermes restart** (not `/reset`) to take effect.
- The live install is a separate git clone at `~/.hermes/plugins/hermes-linux-notify`.
  Editing there also needs a restart. Keep it in sync with this repo.
- Dashboard mirror is opt-in via `HERMES_NOTIFY_MIRROR` (e.g.
  `http://localhost:8787/mirror`); unset = zero network cost. It never blocks
  or fails the real notification.
- `clarify` notifications only fire for `pre_tool_call` with `tool_name == "clarify"`.
  `approval` notifications are skipped when `surface == "smart"`.

## D-Bus skills (for future auto-close work)
- If a task touches D-Bus, desktop notifications, `org.freedesktop.Notifications`,
  `dbus_next`/`dbus_fast`/`pydbus`/`dbus-python`, load the matching skill under
  `.opencode/skills/` first. Always read `dbus-notifications-spec` before any
  implementation. Default binding for new code is `dbus-fast` (5.0.22).
- Closing a notification programmatically needs `CloseNotification(id)`, but the
  plugin currently has no hook for "user interacted" — see prior notes.
