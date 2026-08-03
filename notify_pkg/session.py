from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_hermes_home = os.environ.get("HERMES_HOME")
_DB_PATH = (
    os.path.join(_hermes_home, "state.db")
    if _hermes_home
    else os.path.expanduser("~/.hermes/state.db")
)

# cache en memoria: {session_id: title} para no re-consultar la DB en cada notificacion
_cache: dict[str, str] = {}


def session_title(session_id: str) -> str:
    """Devuelve el titulo de la sesion desde la DB de estado de Hermes.

    Nunca lanza excepciones: cualquier fallo (DB inexistente, fila faltante,
    title NULL/vacio) hace fallback a session_id[:8].
    """
    if not session_id:
        return ""
    if session_id in _cache:
        return _cache[session_id]
    title = _query_title(session_id)
    if title is None:
        return session_id[:8]
    _cache[session_id] = title
    return title


def _query_title(session_id: str) -> str | None:
    try:
        uri = Path(_DB_PATH).as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
    except Exception:
        logger.debug("state db open failed", exc_info=True)
        return None
    try:
        with conn:
            row = conn.execute(
                "SELECT title FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
    except Exception:
        logger.debug("state db query failed", exc_info=True)
        return None
    finally:
        conn.close()
    if row is None:
        return None
    title = row[0]
    if title is None or not str(title).strip():
        return None
    return str(title)
