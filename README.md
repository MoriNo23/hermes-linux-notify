# hermes-linux-notify

Plugin de notificaciones de escritorio para el agente Hermes en Linux.

## Qué hace

El plugin muestra una notificación de escritorio cuando:

- Hermes termina de responder.
- Hermes hace una pregunta (usa la herramienta `clarify`).
- Hermes necesita tu confirmación para ejecutar un comando.

## Requisitos

- Linux con un daemon de notificaciones (GNOME, KDE, XFCE, dunst, entre otros).
- Python 3.8 o superior.
- Hermes CLI instalado.
- `dbus-fast` en el entorno de Hermes para el cierre automático. Sin él, el plugin usa `notify-send` como respaldo.

## Instalación

```
cd ~/.hermes/plugins
git clone https://github.com/MoriNo23/hermes-linux-notify
hermes plugins enable hermes-linux-notify
```

Reinicia Hermes por completo (no basta con `/reset`) para que cargue el plugin.

## Cómo funciona

El plugin registra hooks en Hermes:

- `post_llm_call`: avisa que la respuesta está lista.
- `pre_tool_call` (solo `clarify`): avisa que Hermes pregunta.
- `pre_approval_request`: avisa que se requiere confirmación.
- `post_tool_call` / `post_approval_response`: cierran la notificación cuando respondes o confirmas.

Las notificaciones se entregan por D-Bus (`org.freedesktop.Notifications`) con `dbus_fast`. Si no está disponible, se usa `notify-send`.

El título de la notificación es `Hermes - <sesión>`. El cuerpo muestra la pregunta, la descripción del comando o el aviso correspondiente.

## Configuración

El archivo `plugin.yaml` admite estas opciones:

- `sound_enabled`: reproduce un sonido al notificar.
- `sound_path`: ruta del sonido (por defecto el incluido).
- `sound_volume`: volumen para `paplay`.
- `icon_path`: icono personalizado.
- `notify_question` / `notify_approval`: activan o desactivan cada tipo de aviso.

## Notas

- Las notificaciones son persistentes: se cierran solas cuando interactúas.
- El espejo del dashboard es opcional y usa la variable `HERMES_NOTIFY_MIRROR`.

## Licencia

MIT
