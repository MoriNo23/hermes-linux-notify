# hermes-linux-notify

**Linux desktop notification plugin for Hermes CLI agent**
*Plugin de notificaciones de escritorio para el agente Hermes en Linux*

---

## Features / Características

- 🔔 Desktop notification when Hermes finishes a response
  *Notificación de escritorio cuando Hermes termina una respuesta*
- 🖥️ Detects your terminal emulator (Warp, GNOME Terminal, Konsole, Kitty, etc.)
  *Detecta tu emulador de terminal (Warp, GNOME Terminal, Konsole, Kitty, etc.)*
- 🔄 Fallback chain: `notify-send` → `dunstify` → stderr
  *Cadena de fallback: `notify-send` → `dunstify` → stderr*
- 🛡️ Works with KDE Plasma, GNOME, XFCE, and any desktop that supports `notify-send`
  *Funciona con KDE Plasma, GNOME, XFCE y cualquier escritorio que soporte `notify-send`*

---

## Requirements / Requisitos

- Python 3.8+
- Hermes CLI agent installed
- One of these notification daemons:
  - `libnotify` (`notify-send`) – works with GNOME, KDE, XFCE, etc.
  - `dunst` – lightweight notification daemon (optional fallback)
- For window focusing (optional):
  - `wmctrl` or `xdotool`

### Install dependencies / Instalar dependencias
```bash
# Debian/Ubuntu / Debian-based
sudo apt install libnotify-bin   # for notify-send
sudo apt install dunst           # optional fallback
sudo apt install wmctrl xdotool  # optional window focus
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

1. **`notify-send`** – primary (works with any D-Bus notification daemon)
   *principal (funciona con cualquier demonio de notificaciones D-Bus)*
2. **`dunstify`** – if `dunst` is installed and `notify-send` fails
   *si `dunst` está instalado y `notify-send` falla*
3. **stderr** – last resort, prints to terminal
   *último recurso, imprime en la terminal*

---

## Configuration / Configuración

You can customize the notification message, urgency, and expire time by editing `notify.py`.
*Puedes personalizar el mensaje, urgencia y tiempo de expiración editando `notify.py`.*

Default values:
*Valores predeterminados:*
- `urgency="normal"`
- `expire=5000` (milliseconds / milisegundos)

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
├── plugin.yaml       # plugin manifest / manifiesto
├── __init__.py       # hook registration / registro del hook
├── notify.py         # notification logic / lógica de notificación
└── terminal.py       # terminal detection / detección de terminal
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
