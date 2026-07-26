from __future__ import annotations

import logging
import sys

from .notify import send_notification
from .terminal import detect_terminal_name

logger = logging.getLogger(__name__)


def _on_post_llm_call(*, platform: str = "", **kwargs: object) -> None:
    if platform != "cli":
        return

    if not sys.stdout.isatty():
        return

    term_name = detect_terminal_name()
    title = "Hermes"
    message = "Listo para tu input"
    if term_name:
        message += f" (terminal: {term_name})"

    send_notification(title, message)


def register(ctx) -> None:
    ctx.register_hook("post_llm_call", _on_post_llm_call)
