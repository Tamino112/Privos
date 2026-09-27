#!/usr/bin/bash
# Privos-Branding: Logo, GNOME-Desktop, Wallpaper, Boot-Animation, Schriften und Icons.
set -euxo pipefail

BRANDING="$(dirname "$(readlink -f "$0")")/branding"

dnf5 install -y \
    rsms-inter-fonts \
    jetbrains-mono-fonts-all \
    papirus-icon-theme \
    librsvg2-tools \
    dconf \
    gnome-shell-extension-appindicator \
    gnome-shell-extension-dash-to-panel

render() { rsvg-convert -w "$2" -h "$3" "$1" -o "$4"; }

# --- Logo / Icons --------------------------------------------------------------------
install -Dm644 "${BRANDING}/privos-logo.svg" /usr/share/icons/hicolor/scalable/apps/privos-logo.svg
install -Dm644 "${BRANDING}/privos-logo-symbolic.svg" \
    /usr/share/icons/hicolor/symbolic/apps/privos-logo-symbolic.svg
ASSETS=/usr/share/privos/branding
mkdir -p "${ASSETS}"
for asset in privos-logo-boot.svg privos-logo-tile.svg privos-wordmark.svg privos-wordmark-inverse.svg; do
    install -m644 "${BRANDING}/${asset}" "${ASSETS}/${asset}"
done
for size in 16 22 24 32 48 64 128 256 512; do
    mkdir -p "/usr/share/icons/hicolor/${size}x${size}/apps"
    render "${BRANDING}/privos-logo.svg" "${size}" "${size}" \
        "/usr/share/icons/hicolor/${size}x${size}/apps/privos-logo.png"
done
render "${BRANDING}/privos-logo.svg" 256 256 /usr/share/pixmaps/privos-logo.png
render "${BRANDING}/privos-logo-tile.svg" 128 128 "${ASSETS}/privos-logo-tile.png"
render "${BRANDING}/privos-wordmark.svg" 720 160 "${ASSETS}/privos-wordmark.png"
render "${BRANDING}/privos-wordmark-inverse.svg" 720 160 "${ASSETS}/privos-wordmark-inverse.png"
gtk-update-icon-cache -f /usr/share/icons/hicolor || true

# --- Wallpaper (GNOME wählt passend zum hellen oder dunklen Stil) ----------------------
WALL=/usr/share/backgrounds/privos
mkdir -p "${WALL}"
render "${BRANDING}/wallpaper-light.svg" 3840 2160 "${WALL}/privos-light.png"
render "${BRANDING}/wallpaper-dark.svg" 3840 2160 "${WALL}/privos-dark.png"

# Die GNOME-Einstellungen liegen als Standard vor und bleiben für Nutzer veränderbar.
glib-compile-schemas /usr/share/glib-2.0/schemas
dconf update

# --- Boot-Animation (Plymouth) ---------------------------------------------------------
THEME=/usr/share/plymouth/themes/privos
find /usr/share/plymouth/themes/spinner -name '*.png' ! -name 'watermark.png' -exec cp -t "${THEME}" {} +
rm -f "${THEME}"/throbber-*.png
python3 "${BRANDING}/make-boot-spinner.py" "${THEME}"
render "${BRANDING}/privos-logo-boot.svg" 128 128 "${THEME}/watermark.png"
sed -i 's/^Theme=.*/Theme=privos/' /usr/share/plymouth/plymouthd.defaults
