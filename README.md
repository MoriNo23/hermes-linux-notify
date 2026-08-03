# hermes-linux-notify

**Linux desktop notification plugin for Hermes CLI agent**
*Plugin de notificaciones de escritorio para el agente Hermes en Linux*

---

## Features / Características

- 🔔 Desktop notification when Hermes finishes a response
  *Notificación de escritorio cuando Hermes termina una respuesta*
- ❓ Desktop notification when Hermes asks you a question (clarify)
  *Notificación cuando Hermes te hace una pregunta (clarify)*
- ⚠️ Desktop notification when your confirmation is required
  *Notificación cuando se requiere tu confirmación*
- 🏷️ Shows the real session title in the notification
  *Muestra el título real de la sesión en la notificación*
- 🖥️ Detects your terminal emulator (Warp, GNOME Terminal, Konsole, Kitty, etc.)
  *Detecta tu emulador de terminal (Warp, GNOME Terminal, Konsole, Kitty, etc.)*
- 🖼️ Shows the bundled app icon (128×128) on each notification
  *Muestra el icono de la app (128×128) en la notificación*
- 🔄 Uses the native system notifier via `notify-send` → stderr fallback
  *Usa el notificador nativo del sistema vía `notify-send` → stderr*
- 🔊 Plays a short key-click sound on each notification
  *Reproduce un sonido corto de tecla en cada notificación*
- 🛡️ Works with KDE Plasma, GNOME, XFCE, and any desktop that supports `notify-send`
  *Funciona con KDE Plasma, GNOME, XFCE y cualquier escritorio que soporte `notify-send`*

---

## Requirements / Requisitos

- Python 3.8+
- Hermes CLI agent installed
- One of these notification daemons:
  - `libnotify` (`notify-send`) – works with GNOME, KDE, XFCE, etc.
  - `dunst` – lightweight notification daemon (optional fallback)
- A sound player for the key-click:
  - `paplay` (PulseAudio) or `aplay` (ALSA)

### Install dependencies / Instalar dependencias
```bash
# Debian/Ubuntu / Debian-based
sudo apt install libnotify-bin   # for notify-send
sudo apt install dunst           # optional fallback
sudo apt install pulseaudio-utils  # for paplay (or alsa-utils for aplay)
```

---

## Installation / Instalación

### From GitHub (recommended) / Desde GitHub (recomendado)
```bash
cd ~/.hermes/plugins
git clone https://github.com/MoriNo23/hermes-linux-notify
hermes plugins enable hermes-linux-notify
```

### Manual / Manual
```bash
# Copy to plugins directory
cp -r /path/to/hermes-linux-notify ~/.hermes/plugins/
hermes plugins enable hermes-linux-notify
```

---

## Usage / Uso

1. Start a new Hermes session:
   *Inicia una nueva sesión de Hermes:*
   ```bash
   hermes
   ```

2. Send any prompt.
   *Envía cualquier prompt.*

3. When Hermes finishes responding, you'll receive a desktop notification.
   *Cuando Hermes termine de responder, recibirás una notificación de escritorio.*

---

## Fallback Chain / Cadena de fallback

1. **`notify-send`** – the native system notifier (works with any D-Bus daemon: KDE, GNOME, XFCE, etc.)
   *el notificador nativo (funciona con cualquier daemon D-Bus: KDE, GNOME, XFCE, etc.)*
2. **stderr** – fallback, prints to terminal
   *último recurso, imprime en la terminal*

---

## Configuration / Configuración

The notification text and fallback behavior are hardcoded. To change the message or
timeouts, edit the constants in `__init__.py` and `notify.py` directly.
*El texto de la notificación y el comportamiento de fallback están fijos. Para cambiar
el mensaje o los tiempos, edita las constantes en `__init__.py` y `notify.py` directamente.*

The key-click sound, icon, and which notifications to send are configured via the
optional `config` block in `plugin.yaml`:

*El sonido, el icono y qué notificaciones enviar se configuran con el bloque
opcional `config` en `plugin.yaml`:*

```yaml
config:
  sound_enabled: true      # false disables the key-click
  sound_path: ""           # empty = bundled sounds/keyclick.wav; or ~/ruta/click.wav
  sound_volume: 100        # 0-100, only applied when using paplay
  icon_path: ""            # empty = bundled assets/icon-128.png; or ~/ruta/icono.png
  notify_question: true    # false disables the "Hermes asks" notification (clarify)
  notify_approval: true    # false disables the "confirmation required" notification
```

### Icon / Icono

The bundled icon is `assets/icon-128.png` (128×128). Manage desktops scale it well
on HiDPI. If you make your own, use a **128×128 PNG** (or an SVG source exported to
128×128 PNG) — big enough to stay crisp, small enough to load instantly.

*El icono incluido es `assets/icon-128.png` (128×128). Si querés el tuyo, usá un
PNG de **128×128** (o SVG con export a PNG 128×128) — nítido en HiDPI y de carga
rápida.*

If no audio player (`paplay`/`aplay`) is found, the plugin emits a terminal bell
(`\a`) as fallback. The sound plays on a background thread so it never delays the
notification.
*Si no hay reproductor (`paplay`/`aplay`), el plugin emite una campana de terminal
(`\a`) como fallback. El sonido se reproduce en un hilo aparte y no retrasa la
notificación.*

---

## Troubleshooting / Solución de problemas

**No notification appears / No aparece notificación**
- Check if `notify-send` works: `notify-send "test" "hello"`
- Check if `dunst` is running: `pgrep -x dunst`
- If using KDE, ensure `plasmashell` is running: `pgrep -x plasmashell`

**Plugin not loading / El plugin no se carga**
- Verify it's enabled: `hermes plugins list`
- Restart Hermes completely (not just `/reset`)

---

## Files / Archivos

```
~/.hermes/plugins/hermes-linux-notify/
├── plugin.yaml          # plugin manifest / manifiesto
├── __init__.py          # Hermes entry: re-exports register / entrypoint del plugin
├── pytest.ini           # pytest config (import-mode=importlib)
├── notify_pkg/          # plugin logic / lógica del plugin
│   ├── __init__.py      # register() + hooks
│   ├── notify.py        # notification logic / lógica de notificación
│   ├── session.py       # session title lookup / título de sesión
│   └── terminal.py      # terminal detection / detección de terminal
├── tests/
│   ├── conftest.py
│   └── test_session.py
└── assets/
    ├── icon-128.png            # notification icon (128×128) / icono de notificación
    └── icon-original-1024.png  # source image / imagen fuente (1024×1024)
```

---

## License / Licencia

MIT

---

## Author / Autor

[MoriNo23](https://github.com/MoriNo23)

---

*Inspired by / Inspirado en:*
[konyu/hermes-macos-notify](https://github.com/konyu/hermes-macos-notify)
