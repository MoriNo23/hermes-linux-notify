#!/usr/bin/env bash
# Language-agnostic diagnosis for org.freedesktop.Notifications setup issues.
# Run before debugging any client/server code — most "my Notify() call
# hangs/fails" reports trace back to one of the checks below.
set -uo pipefail

echo "== Session bus address =="
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
    echo "[WARN] DBUS_SESSION_BUS_ADDRESS is not set. No client library in this"
    echo "       skillset (dbus-next, dbus-fast, pydbus, dbus-python) will find"
    echo "       a session bus without it. If you're in a headless shell/SSH"
    echo "       session outside a full desktop login, this is expected --"
    echo "       use 'dbus-run-session -- <your command>' to get one."
else
    echo "[OK] $DBUS_SESSION_BUS_ADDRESS"
fi

echo
echo "== Is a notification daemon registered? =="
if command -v busctl >/dev/null 2>&1; then
    if busctl --user list 2>/dev/null | grep -qi notifications; then
        echo "[OK] org.freedesktop.Notifications is owned:"
        busctl --user list 2>/dev/null | grep -i notifications
    else
        echo "[FAIL] No service owns org.freedesktop.Notifications on the session bus."
        echo "       Every Notify() call will time out or error until one starts."
        echo "       Minimal Wayland/Hyprland setups ship NO notification daemon"
        echo "       by default -- install and start one, e.g.: dunst, mako,"
        echo "       swaync, or your DE's built-in one (GNOME Shell / KDE Plasma"
        echo "       both include their own, no separate daemon needed there)."
    fi
else
    echo "[SKIP] busctl not found. Try: dbus-send --session --print-reply \\"
    echo "       --dest=org.freedesktop.DBus /org/freedesktop/DBus \\"
    echo "       org.freedesktop.DBus.ListNames | grep -i notif"
fi

echo
echo "== Manual round-trip test (dbus-send, no Python needed) =="
if command -v dbus-send >/dev/null 2>&1; then
    echo "Run this to fire a real notification independent of any library:"
    echo
    echo "  dbus-send --session --type=method_call --print-reply \\"
    echo "    --dest=org.freedesktop.Notifications \\"
    echo "    /org/freedesktop/Notifications \\"
    echo "    org.freedesktop.Notifications.Notify \\"
    echo "    string:'diagnose_bus.sh' uint32:0 string:'' \\"
    echo "    string:'Test' string:'Manual dbus-send round-trip' \\"
    echo "    array:string:'' dict:string:variant:'' int32:4000"
    echo
    echo "If this shows a notification but your Python code doesn't, the bug"
    echo "is in the Python binding usage, not the bus/daemon setup."
else
    echo "[SKIP] dbus-send not found. Install the 'dbus' or 'dbus-tools' package."
fi

echo
echo "== Python bindings importable? =="
for mod in dbus_next dbus_fast pydbus dbus; do
    if python3 -c "import $mod" 2>/dev/null; then
        echo "[OK] $mod imports cleanly"
    else
        echo "[--] $mod not importable (fine if you're not using it)"
    fi
done
