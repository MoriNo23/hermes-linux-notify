from __future__ import annotations

import sqlite3

import pytest

from notify_pkg import session


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    """DB temp con una fila de sesion conocida, apuntando session._DB_PATH a ella."""
    path = str(tmp_path / "state.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE sessions (id TEXT, title TEXT)")
    conn.execute(
        "INSERT INTO sessions (id, title) VALUES (?, ?)", ("abc12345", "titulo de prueba")
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(session, "_DB_PATH", path)
    session._cache.clear()
    yield path
    session._cache.clear()


def _insert_row(db_path: str, sid: str, title: str | None) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO sessions (id, title) VALUES (?, ?)", (sid, title))
    conn.commit()
    conn.close()
    session._cache.clear()


def test_returns_exact_title(db_path):
    assert session.session_title("abc12345") == "titulo de prueba"


def test_fallback_when_row_missing(db_path):
    assert session.session_title("zzzz9999") == "zzzz9999"


def test_fallback_when_title_null(db_path):
    _insert_row(db_path, "nullid00", None)
    assert session.session_title("nullid00") == "nullid00"


def test_fallback_when_title_empty(db_path):
    _insert_row(db_path, "emptyid0", "")
    assert session.session_title("emptyid0") == "emptyid0"


def test_fallback_when_db_missing(db_path, monkeypatch):
    monkeypatch.setattr(session, "_DB_PATH", "/nonexistent/state.db")
    session._cache.clear()
    assert session.session_title("abc12345") == "abc12345"


def test_cache_used_after_first_lookup(db_path):
    assert session.session_title("abc12345") == "titulo de prueba"
    # cambiar el titulo en la DB "detras de escena": la cache debe ganar
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE sessions SET title = ? WHERE id = ?", ("cambiado", "abc12345"))
    conn.commit()
    conn.close()
    assert session.session_title("abc12345") == "titulo de prueba"
