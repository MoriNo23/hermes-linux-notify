# Mejora de Notificaciones — hermes-linux-notify

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Que el plugin notifique con imagen (icono), título de sesión real, y avise cuando el modelo hace una *pregunta* (clarify) o pide *confirmación* (aproval).

**Architecture:** El plugin ya usa el sistema de hooks nativos de Hermes. Añadimos 2 hooks nuevos (`pre_tool_call` para detectar `clarify`, `pre_approval_request` para la confirmación), pasamos el `-i` (icono) y `-a` (app-name) a `notify-send`, y recuperamos el title de la sesión desde `~/.hermes/state.db`.

**Tech Stack:** Python 3.8+, SQLite (read-only), `notify-send`/`dunstify` (D-Bus).

---

## Contexto confirmado (del core Hermes v0.19.1)

- **Session title**: `get_session_title(session_id)` ejecuta `SELECT title FROM sessions WHERE id = ?` contra `~/.hermes/state.db` (fuente: `hermes_state.py:5015`). Ruta default = `get_hermes_home()/state.db` (`hermes_state.py:243`). Fallback: `session_id[:8]` si el title es None.
- **Hook aprobal**: `pre_approval_request` y `post_approval_response` disparados por `tools/approval.py:154,163`. Kwargs: `command`, `description`, `pattern_key`, `session_key`, `surface`. Observers only (ignoran return).
- **Hook pregunta**: NO existe hook dedicado para `clarify`. Usar `pre_fl_tool_call` con `tool_name == "clarify"`; args incluyen `question` (y `choices`). Retornar `None` siempre (observer) para no interferir con el gate de aprobación.
- **`notify-send`**: soporta `-i ICON` (ruta o nombre) y `-a APP_NAME` (visto en `notify-send --help`).
- El hook `post_llm_call` ya recibe `session_id` (kwarg) — solo hay que usarlo.

## Tamaño de imagen de notificación (respuesta directa)

**Recomendación principal: PNG/símbolo escalable a 128×128 px (fuente SVG opcional).**

- FreeDesktop/`notify-send` muestra el icono de app a ~48–64 px en la burbuja. Un **PNG a 128×128** se renderiza nítido a 48+ y se adapta bien en HiDPI (escala 2×).
- Si quieres máxima nitidez en pantallas HiDPI, genera el icono a **256×256**, o mejor: entrega un **SVG vectorial** como fuente y exporta el PNG 128×128 como fallback portable.
- NO usar un PNG de 32×32 (se ve borroso al escalar) ni uno gigante comprimido; ruta única **128×128** (o SVG).
- Colócalo en el repo: `assets/icon-128.png` (por convención de tema), y configura `config.icon_path` en `plugin.yaml`.

---

## Task 1: Helper de recuperación de título de sesión

**Objective:** Devolver el `title` real de la sesión dado un `session_id`, sin acoplar el plugin al core.

**Files:**
- Create: `session.py`
- Modify: `notify.py` (usará el helper)

**Step 1: Escribir `session.py`**
- Conexión SQLite read-only a `get_dependencies_home()/state.db` (fallback `~/.hermes/state.db`).
- `session_title(session_id) -> str`: `SELECT title FROM sessions WHERE id=?`; si vacío/None → `session_id[:8]`.
- Cache en memoria (dict) por session_id.
- `try/except` amplio: si la DB falla, return `session_id[:8]`.

**Step 2: Verificar manualmente**
`python3 -c "import sys; sys.path.insert(0,'.'); from session import session_title; print(session_title('<un-session-id-real>'))"  # sha 8-12 chars → título copiado`

---

## Task 2: Icono + aplicar `-i` y `-a` en `notify.py`

**Objective:** add icon & app-name a las llamadas `notify-send`/`dunstify`.

**Files:**
- Create: `assets/icon-128.png` (PNG 128×128, por ejemplo del logo de Hermes), o un SVG.
- Modify: `notify.py:62-94` (`_run_notifier`), `plugin.yaml` (`config.icon_path`).

**Step 1: Editar `_run_notifier`**
Añadir params `icon: str | None`, `app_name: str = "Hermes"`.
Comando: `[binary, "-a", app_name] + (["-i", icon] if icon else []) + ["-u", urgency, "-t", expire, title, message]`.

**Step 2: Cargar `icon_path`** del `_load_config()` (default `assets/icon-128.png` junto al archivo), expandir `~`, comprobar `os.path.exists`, pasar `None` si no.

---

## Task 3: Hook de NOTIFICACIÓN DE PREGUNTA (clarify)

**Objective:** notificar (con sonido + icono de pregunta) cuando el modelo lanza la tool `clarify`.

**Files:**
- Modify: `__init__.py` (nuevo hook handela + registro).

**Step 1: importar `pre_tool_call`**
En `register()`: `ctx.register_hook("pre_tool_call", _on_pre_tool_call)`.

**Step 2: callback**
```python
def _on_pre_tool_call(*, tool_name="", args=None, platform="", **kwargs):
    if tool_name != "clarify":
        return None
    if platform == "cli" and not sys.stdout.isatty():
        return None
    q = (args or {}).get("question", "Hermes te pregunta")
    send_notification(f"📩 Hermes pregunta ({_session_label(kwargs)})", q,
                      overlap="attention")
    return None   # nunca bloquear
```

---

## Task 4 — Hook de CONFIRMACIÓN (aprobación)

**Objective:** notificar cuando Hermes necesita confirmación de una acción peligrosa.

**Files:**
- Modify: `__init__.py`

**Step 1: registro**
`ctx.register_hook("pre_approval_request", _on_pre_approval_request)`.

**Step 2:**
```python
def _on_pre_approval_request(*, command="", description="", surface="", **kwargs):
    if surface == "smart":
        return
    msg = description or command
    send_notification("⚠ Aprobación requerida", f"{msg[:120]}")
```

---

## Task 5 — Añadir título real de sesión a `post_llm_call`

**Objective:** que la notificación "Listo para input" muestre el title de la sesión.

**Files:**
- Modify: `__init__.py` `_on_post_llm_call`

**Step 1:**
```python
sess_id = kwargs.get("session_id", "")
title_part = session_title(sess_id) if sess_id else ""
message = f"Listo para tu input{session_title(sess_id)}"
```
`send_notification(f"{sess_title} — Hermes", "Listo para tu input")`.

---

## Task 6: Config + README

**Files:**
- Modify: `plugin.yaml` (add `icon_path`, `notify_question`, `notify_approval` switches; default `true`).
- Modify: `README.md` (documentar hooks nuevos, tamaño 128×128, config).
- **Tests:** añadir `tests/test_session.py` (mock `sqlite3` o un temp db) y `tests/test_notify.py` won`no_avatar` checks del arg `-i`.

---

## Verification

- `python3 -m py_compile notify.py session.py __init__.py`
- `pytest tests/ -q` (si hay tests) — o al menos una import-run de cada hook con kwargs sintéticos (formato de `hooks.py` que ya es el real).
- Comprobar manual: `notify-send -a Hermes -i /abs/path/icon-128.png -u low -t 1000 "test" "icón"` → debe salir burbuja con icono.
- Ciclo real: arrancar `hermes`, mandar un prompt, disparar una `clarify` y un `commit` peligroso → verificar 3 notificaciones distintas (pregunta / aprobar / listo).

## Risks / Tradeoffs / Open Questions

- `pre_tool_call` es un hook de gate (listo para `approve`/`book`). Nuestro callback SIEMPRE devuelve `None` → inofensivo; no toca la seguridad existente.
- El icono si es SVG puede que algunos deamons (dunst viejo) no lo renderizn; por eso el PNG 128×128 como primary.
- Estado de título leído read-only; si la DB está bloqueada (WAL/lock) el `try/except` devuelve fallback — nunca crashea la burbuja.
- **Open**: ¿tal vez el usuario quiere también notificar en `post_approval_response` (ya resuelto por el modelo smart) o solo el `pre` (cuando él debe confirmar)? plan asume "solo cuando él debe confirmar".