#!/usr/bin/bash
# Privos-Branding: Logo, GNOME-Desktop, Wallpaper, Boot-Animation, Schriften und Icons.
set -euxo pipefail

BRANDING="$(dirname "$(readlink -f "$0")")/branding"

dnf5 install -y \
    rsms-inter-fonts \
    jetbrains-mono-fonts-all \
    papirus-icon-theme \
    librsvg2-tools \
    curl \
    dconf \
    gnome-shell-extension-appindicator \
    gnome-shell-extension-dash-to-panel \
    gnome-menus \
    gnome-software

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
install -m644 "${BRANDING}/privos-software.png" /usr/share/pixmaps/privos-software.png
gtk-update-icon-cache -f /usr/share/icons/hicolor || true

# Der Software-Starter behält seine App-ID und alle Aktionen, bekommt aber Privos-Branding.
python3 - <<'PY'
from pathlib import Path

desktop = Path('/usr/share/applications/org.gnome.Software.desktop')
if not desktop.is_file():
    raise SystemExit(f'Software-Starter fehlt: {desktop}')

lines = desktop.read_text(encoding='utf-8').splitlines()
in_entry = False
found_entry = False
result = []
for line in lines:
    if line == '[Desktop Entry]':
        found_entry = True
        in_entry = True
        result.extend((line, 'Name=Privos Software', 'Icon=/usr/share/pixmaps/privos-software.png'))
        continue
    if line.startswith('[') and line.endswith(']'):
        in_entry = False
    if in_entry and (line.startswith('Icon=') or line.startswith('Name=') or line.startswith('Name[')):
        continue
    result.append(line)
if not found_entry:
    raise SystemExit(f'Ungültiger Software-Starter: {desktop}')
desktop.write_text('\n'.join(result) + '\n', encoding='utf-8')
PY

# ArcMenu liefert ein echtes Startmenü und öffnet es auch mit der Super-Taste.
ARC_DIR=/usr/share/gnome-shell/extensions/arcmenu@arcmenu.com
ARC_ZIP=/tmp/privos-arcmenu.zip
curl --fail --location --retry 3 \
    'https://extensions.gnome.org/download-extension/arcmenu@arcmenu.com.shell-extension.zip?version_tag=75483' \
    -o "${ARC_ZIP}"
echo "ef414c90dcb5f2b0c6ccb5f8e59fd9963c584789d3d8d26740ddb731100c4b40  ${ARC_ZIP}" | sha256sum -c -
mkdir -p "${ARC_DIR}"
python3 -m zipfile -e "${ARC_ZIP}" "${ARC_DIR}"
glib-compile-schemas "${ARC_DIR}/schemas"
rm -f "${ARC_ZIP}"

# --- Wallpaper ------------------------------------------------------------------------
WALL=/usr/share/backgrounds/privos
mkdir -p "${WALL}"
install -m644 "${BRANDING}/privos-wallpaper-default.png" "${WALL}/privos-default.png"
install -m644 "${BRANDING}/privos-wallpaper-light.png" "${WALL}/privos-light.png"
install -m644 "${BRANDING}/privos-wallpaper-dark.png" "${WALL}/privos-dark.png"

# Die GNOME-Einstellungen liegen als Standard vor und bleiben für Nutzer veränderbar.
glib-compile-schemas /usr/share/glib-2.0/schemas
dconf update

# --- Boot-Animation (Plymouth) ---------------------------------------------------------
# Skript-Theme: Hintergrund, Lichthof und Ladelinie aus make-boot-assets.py; das Zeichen
# in mehreren Größen, damit Plymouth beim Skalieren keine Treppenkanten erzeugt.
dnf5 install -y plymouth-plugin-script
THEME=/usr/share/plymouth/themes/privos
python3 "${BRANDING}/make-boot-assets.py" "${THEME}"
for size in 64 96 144 192; do
    render "${BRANDING}/privos-logo-boot.svg" "${size}" "${size}" "${THEME}/logo-${size}.png"
done
sed -i 's/^Theme=.*/Theme=privos/' /usr/share/plymouth/plymouthd.defaults
