# hermes-linux-notify

A desktop notification plugin for the Hermes CLI agent on Linux.

## What it does

The plugin shows a desktop notification when:

- Hermes finishes a response.
- Hermes asks a question (via the `clarify` tool).
- Hermes needs your confirmation to run a command.

## Requirements

- Linux with a notification daemon (GNOME, KDE, XFCE, dunst, and others).
- Python 3.8 or newer.
- Hermes CLI installed.
- `dbus-fast` in the Hermes environment for automatic closing. Without it, the plugin falls back to `notify-send`.

## Installation

```
cd ~/.hermes/plugins
git clone https://github.com/MoriNo23/hermes-linux-notify
hermes plugins enable hermes-linux-notify
```

Restart Hermes completely (a `/reset` is not enough) so the plugin loads.

## How it works

The plugin registers hooks in Hermes:

- `post_llm_call`: reports that the response is ready.
- `pre_tool_call` (only `clarify`): reports that Hermes is asking.
- `pre_approval_request`: reports that confirmation is required.
- `post_tool_call` / `post_approval_response`: close the notification once you answer or confirm.

Notifications are delivered over D-Bus (`org.freedesktop.Notifications`) with `dbus_fast`. If that is unavailable, `notify-send` is used instead.

The notification title is `Hermes - <session>`. The body shows the question, the command description, or the relevant notice.

## Configuration

The `plugin.yaml` file accepts these options:

- `sound_enabled`: play a sound when notifying.
- `sound_path`: path to the sound (defaults to the bundled one).
- `sound_volume`: volume for `paplay`.
- `icon_path`: a custom icon.
- `notify_question` / `notify_approval`: toggle each kind of notice.

## Notes

- Notifications persist until you interact with them, then close on their own.
- The dashboard mirror is optional and uses the `HERMES_NOTIFY_MIRROR` variable.

## License

MIT
