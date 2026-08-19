from __future__ import annotations

import html
import logging
import os
import sys
import threading

from .notify import close_notification, send_notification
from .session import session_title

logger = logging.getLogger(__name__)

# Maps a Hermes session_id to the D-Bus notification id so the matching
# "user interacted" hook can auto-close it. Keyed by session because that is
# the correlation id both the open and close hooks receive.
_pending_lock = threading.Lock()
_pending: dict[str, int] = {}


def _store_pending(session_id: str, notif_id: int | None) -> None:
    if not session_id or notif_id is None:
        return
    with _pending_lock:
        _pending[session_id] = notif_id


def _close_pending(session_id: str) -> None:
    if not session_id:
        return
    with _pending_lock:
        notif_id = _pending.pop(session_id, None)
    if notif_id is not None:
        close_notification(notif_id)


def _title(session: str) -> str:
    """Summary shows app + session context: `Hermes - <session>`."""
    return f"Hermes - {session}" if session else "Hermes"


def _notify_switch(key: str) -> bool:
    """Read a boolean notify_* switch from plugin.yaml (default True)."""
    pkg = os.path.dirname(os.path.abspath(__file__))
    # plugin.yaml lives at the plugin root, one level above the subpackage dir.
    cfg_path = os.path.join(os.path.dirname(pkg), "plugin.yaml")
    try:
        import yaml

        with open(cfg_path, encoding="utf-8") as fh:
            parsed = yaml.safe_load(fh) or {}
        return bool(parsed.get("config", {}).get(key, True))
    except Exception:
        return True


def _is_active(platform: str = "") -> bool:
    """Notifications only make sense on an interactive CLI session."""
    if platform not in ("", "cli", "tui"):
        return False
    return bool(sys.stdout.isatty())


def _session_label(session_id: str = "") -> str:
    if session_id:
        return session_title(session_id)
    return ""


def _on_post_llm_call(*, platform: str = "", **kwargs: object) -> None:
    if not _is_active(platform):
        return

    sess = _session_label(str(kwargs.get("session_id", "")))
    title = _title(sess)
    message = "Respuesta lista"

    send_notification(title, message, source="post_llm_call")


def _on_pre_tool_call(
    *,
    tool_name: str = "",
    args: dict | None = None,
    platform: str = "",
    **kwargs: object,
) -> None:
    """Notify when the model asks the user a question (clarify tool)."""
    if tool_name != "clarify":
        return None
    if not _is_active(platform):
        return None
    if not _notify_switch("notify_question"):
        return None

    question = (args or {}).get("question", "") or "Hermes te pregunta algo"
    sess = _session_label(str(kwargs.get("session_id", "")))
    title = _title(sess)
    message = f"<b>Hermes pregunta</b><br>{html.escape(question[:300])}"
    notif_id = send_notification(title, message, urgency="normal", source="clarify")
    _store_pending(str(kwargs.get("session_id", "")), notif_id)

    # Observer only — never interfere with the tool-call gate.
    return None


def _on_pre_approval_request(
    *,
    command: str = "",
    description: str = "",
    surface: str = "",
    **kwargs: object,
) -> None:
    """Notify when the user must confirm a sensitive action."""
    if not _is_active():
        return
    if surface == "smart":
        # Decided by the auxiliary LLM, no human input needed.
        return
    if not _notify_switch("notify_approval"):
        return

    text = description or command or "Confirmación requerida"
    sess = _session_label(str(kwargs.get("session_id", "")))
    title = _title(sess)
    parts = [f"<b>Confirmación requerida</b>", html.escape(text[:300])]
    if command and command != description:
        parts.append(f"Comando: {html.escape(command)}")
    message = "<br>".join(parts)
    notif_id = send_notification(title, message, urgency="critical", source="approval")
    _store_pending(str(kwargs.get("session_id", "")), notif_id)


def _on_post_tool_call(
    *,
    tool_name: str = "",
    session_id: str = "",
    **kwargs: object,
) -> None:
    """Auto-close the clarify notification once the user has answered it."""
    if tool_name != "clarify":
        return
    _close_pending(str(session_id))


def _on_post_approval_response(
    *,
    session_id: str = "",
    **kwargs: object,
) -> None:
    """Auto-close the approval notification once the user has decided."""
    _close_pending(str(session_id))


def register(ctx) -> None:
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_hook("pre_approval_request", _on_pre_approval_request)
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("post_approval_response", _on_post_approval_response)