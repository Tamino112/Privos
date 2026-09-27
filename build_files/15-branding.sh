#!/usr/bin/bash
# Privos-Branding: Logo, Wallpaper, Boot-Animation, KDE-Design, Farbschema, Schriften, Icons.
set -euxo pipefail

BRANDING="$(dirname "$(readlink -f "$0")")/branding"

dnf5 install -y \
    rsms-inter-fonts \
    jetbrains-mono-fonts-all \
    papirus-icon-theme \
    librsvg2-tools

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

# --- Wallpaper (hell + dunkel, Plasma wählt passend zum Farbschema) --------------------
WALL=/usr/share/wallpapers/Privos
mkdir -p "${WALL}/contents/images" "${WALL}/contents/images_dark"
render "${BRANDING}/wallpaper-light.svg" 3840 2160 "${WALL}/contents/images/3840x2160.png"
render "${BRANDING}/wallpaper-dark.svg" 3840 2160 "${WALL}/contents/images_dark/3840x2160.png"
render "${BRANDING}/wallpaper-dark.svg" 640 360 "${WALL}/contents/screenshot.png"
# Alles, was noch auf das Fedora-Wallpaper zeigt (Login, Sperrbildschirm), zeigt jetzt auf Privos
ln -sfn Privos /usr/share/wallpapers/Fedora
sed -i 's|/usr/share/wallpapers/Fedora/|/usr/share/wallpapers/Privos/|g' /usr/lib/plasmalogin/defaults.conf

# --- Boot-Animation (Plymouth) ---------------------------------------------------------
THEME=/usr/share/plymouth/themes/privos
find /usr/share/plymouth/themes/spinner -name '*.png' ! -name 'watermark.png' -exec cp -t "${THEME}" {} +
rm -f "${THEME}"/throbber-*.png
python3 "${BRANDING}/make-boot-spinner.py" "${THEME}"
render "${BRANDING}/privos-logo-boot.svg" 128 128 "${THEME}/watermark.png"
sed -i 's/^Theme=.*/Theme=privos/' /usr/share/plymouth/plymouthd.defaults

# --- KDE-Design (Look-and-Feel "Privos") -----------------------------------------------
LNF=/usr/share/plasma/look-and-feel/org.privos.desktop
# Splash, Abmelde-Dialog und Setup-Skripte vom Fedora-Design übernehmen; eigene Dateien behalten
cp -an /usr/share/plasma/look-and-feel/org.fedoraproject.fedoradark.desktop/contents/. "${LNF}/contents/"
gzip -9n -c "${BRANDING}/privos-logo-boot.svg" > "${LNF}/contents/splash/images/plasma.svgz"
rm -f "${LNF}"/contents/previews/*
render "${BRANDING}/wallpaper-dark.svg" 640 360 "${LNF}/contents/previews/preview.png"
render "${BRANDING}/wallpaper-dark.svg" 640 360 "${LNF}/contents/previews/splash.png"
render "${BRANDING}/wallpaper-dark.svg" 640 360 "${LNF}/contents/previews/lockscreen.png"
render "${BRANDING}/wallpaper-dark.svg" 1920 1080 "${LNF}/contents/previews/fullscreenpreview.jpg"

# --- Farbschema "Privos Dark" (aus Breeze Dark abgeleitet) -----------------------------
python3 "${BRANDING}/make-colorscheme.py" \
    /usr/share/color-schemes/BreezeDark.colors \
    /usr/share/color-schemes/PrivosDark.colors
