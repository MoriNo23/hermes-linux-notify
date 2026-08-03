from __future__ import annotations

import logging
import os
import sys

from .notify import send_notification
from .session import session_title
from .terminal import detect_terminal_name

logger = logging.getLogger(__name__)


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

    term_name = detect_terminal_name()
    title = "Hermes"
    message = "Listo para tu input"
    if term_name:
        message += f" (terminal: {term_name})"

    send_notification(title, message)


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
    title = "Hermes pregunta" if not sess else f"Hermes pregunta · {sess}"
    send_notification(title, question[:300], urgency="normal")

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
    title = "Confirmación requerida" if not sess else f"Confirmación · {sess}"
    send_notification(title, text[:300], urgency="critical")


def register(ctx) -> None:
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_hook("pre_approval_request", _on_pre_approval_request)