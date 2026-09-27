#!/usr/bin/bash
# Macht aus dem Privos-Image ein bootfähiges Live-System mit Installer.
# Läuft innerhalb von "podman build" (siehe installer/Containerfile).
# Aufbau angelehnt an Bazzite/Titanoboa (Container-native ISO contract v0.1.0).
set -exo pipefail

SRC="$(dirname "$(readlink -f "$0")")"
PAYLOAD_REF=${PAYLOAD_REF:?}
UPDATE_REF=${UPDATE_REF:?}
if [[ -s /run/secrets/registry-auth ]]; then
    export REGISTRY_AUTH_FILE=/run/secrets/registry-auth
fi

# /root zeigt auf /var/roothome, das im Container-Build noch fehlt
mkdir -p "$(realpath /root)"
# bwrap (Flatpak) braucht Schreibzugriff auf /proc/sys
mount -o remount,rw /proc/sys

# --- Flatpaks vorinstallieren (werden bei der Installation mitkopiert) -----------------
mkdir -p /etc/flatpak/remotes.d
curl --retry 3 -Lo /etc/flatpak/remotes.d/flathub.flatpakrepo https://dl.flathub.org/repo/flathub.flatpakrepo
xargs -r flatpak install -y --noninteractive flathub < "${SRC}/flatpaks"
# Passender NVIDIA-Treiber für Flatpak-Apps (falls Flathub ihn noch nicht hat,
# installiert ihn privos-nvidia-flatpak-sync später automatisch)
nvidia_version="$(rpm -q --queryformat '%{VERSION}' nvidia-driver | tr '.' '-')"
flatpak install -y --noninteractive flathub \
    "org.freedesktop.Platform.GL.nvidia-${nvidia_version}" \
    "org.freedesktop.Platform.GL32.nvidia-${nvidia_version}" || \
    echo "::warning::NVIDIA-Flatpak-Laufzeit ${nvidia_version} nicht auf Flathub gefunden"

# --- Das zu installierende Privos-Image in die ISO legen (Offline-Installation) --------
podman pull "${PAYLOAD_REF}"

# --- Live-spezifische Dateien ----------------------------------------------------------
cp -a "${SRC}/system_files/." /

# Cockpit wählt das Branding anhand von ID=privos. Das Logo stammt aus dem
# bereits gebauten Privos-Image; der Installer zeigt damit kein Fedora-Symbol.
install -m644 /usr/share/pixmaps/privos-logo.png \
    /usr/share/cockpit/branding/privos/logo.png

# Nur die Live-Umgebung zeigt einen kurzen Produktnamen im Installer-Kopf.
# Das installierte Payload-Image behält seine vollständige Versionsbezeichnung.
sed -i 's/^PRETTY_NAME=.*/PRETTY_NAME="Privos"/' /usr/lib/os-release

# Im Live-System darf nouveau einspringen, falls der NVIDIA-Treiber nicht lädt
# (z. B. bei Secure Boot vor der Schlüssel-Registrierung). Installiert wird trotzdem NVIDIA.
sed -i '/^blacklist nouveau/d; /^blacklist nova-core/d' /usr/lib/modprobe.d/nvidia.conf
dnf -y reinstall mesa-vulkan-drivers || dnf -y install mesa-vulkan-drivers
mkdir -p /etc/environment.d
echo "GSK_RENDERER=gl" > /etc/environment.d/90-privos-live-nvidia.conf

# --- Live-Boot: Initramfs mit dmsquash-live ------------------------------------------
dnf install -y dracut-live
kernel="$(find /usr/lib/modules -maxdepth 1 -mindepth 1 -type d -printf '%P\n' | head -1)"
DRACUT_NO_XATTR=1 dracut -v --force --zstd --reproducible --no-hostonly \
    --add "dmsquash-live dmsquash-live-autooverlay" \
    "/usr/lib/modules/${kernel}/initramfs.img" "${kernel}"

# --- Live-Sitzung (automatische Anmeldung als liveuser in GNOME) -----------------------
dnf install -y livesys-scripts
sed -i "s/^livesys_session=.*/livesys_session=gnome/" /etc/sysconfig/livesys
systemctl enable livesys.service livesys-late.service

# --- Installer (Anaconda) --------------------------------------------------------------
dnf install -y --allowerasing anaconda-live libblockdev-{btrfs,lvm,dm} python3-gobject gtk4 libadwaita
mkdir -p /var/lib/rpm-state
test -s /usr/share/cockpit/branding/privos/branding.css
test -s /usr/share/cockpit/branding/privos/logo.png

# GNOME zeigt Desktop-Dateien nicht von selbst an. Gtk4 DING 100.29 unterstützt GNOME 50.
# Die feste Version und Prüfsumme halten den Live-Desktop reproduzierbar.
DING_DIR=/usr/share/gnome-shell/extensions/gtk4-ding@smedius.gitlab.com
DING_ZIP=/tmp/privos-gtk4-ding.zip
curl --fail --location --retry 3 \
    'https://extensions.gnome.org/download-extension/gtk4-ding@smedius.gitlab.com.shell-extension.zip?version_tag=75162' \
    -o "${DING_ZIP}"
echo "4a884fa3976aeb814726fd96428c09cfeca2da01aec3ac8629ddd6cd22bff2c1  ${DING_ZIP}" | sha256sum -c -
mkdir -p "${DING_DIR}"
python3 -m zipfile -e "${DING_ZIP}" "${DING_DIR}"
glib-compile-schemas "${DING_DIR}/schemas"
rm -f "${DING_ZIP}"
dconf update

cat >> /usr/share/anaconda/interactive-defaults.ks <<EOF

ostreecontainer --url=${PAYLOAD_REF} --transport=containers-storage --no-signature-verification

%post --erroronfail --log=/tmp/privos-update-source.log
# Updates kommen direkt aus der Privos-Registry
bootc switch --mutate-in-place --transport registry ${UPDATE_REF}
%end

%include /usr/share/anaconda/post-scripts/disable-fedora-flatpak.ks
%include /usr/share/anaconda/post-scripts/install-flatpaks.ks
%include /usr/share/anaconda/post-scripts/restore-selinux-labels.ks
%include /usr/share/anaconda/post-scripts/secureboot-enroll-key.ks
EOF

# Installer-Starter mit Privos-Namen und -Logo
for desktop in /usr/share/applications/liveinst.desktop /etc/xdg/autostart/liveinst-setup.desktop; do
    [[ -f "${desktop}" ]] || continue
    sed -i \
        -e 's/^Name=.*/Name=Privos installieren/' \
        -e '/^Name\[/d' \
        -e 's/^Icon=.*/Icon=privos-logo/' \
        "${desktop}"
done
# Der eigene Assistent (privos-installer) ersetzt den automatischen Anaconda-Start:
# sonst öffnet das alte Anaconda-Fenster zusätzlich zum Willkommensfenster.
rm -f /etc/xdg/autostart/liveinst-setup.desktop

# --- Dienste, die im Live-System nichts zu suchen haben --------------------------------
for unit in \
    privos-nvidia-flatpak-sync.service \
    rpm-ostree-countme.service \
    rpm-ostreed-automatic.timer \
    bootloader-update.service \
    flatpak-add-fedora-repos.service \
    greenboot-healthcheck.service; do
    systemctl disable "${unit}" 2>/dev/null || true
done
systemctl --global disable podman-auto-update.timer 2>/dev/null || true

# --- ISO-Boot (UEFI) ------------------------------------------------------------------
dnf install -y grub2-efi-x64-cdboot
mkdir -p /boot/efi
cp -av /usr/lib/efi/*/*/EFI /boot/efi/
cp -v /boot/efi/EFI/fedora/grubx64.efi /boot/efi/EFI/BOOT/fbx64.efi
mkdir -p /usr/lib/bootc-image-builder
cp "${SRC}/iso.yaml" /usr/lib/bootc-image-builder/iso.yaml

# --- Laufzeit-Anpassungen für das Live-System -----------------------------------------
rm -f /etc/localtime
systemd-firstboot --timezone UTC

# /var/tmp liegt im Live-System im kleinen RAM-/run; ostree braucht dort viel Platz
rm -rf /var/tmp
mkdir /var/tmp
cat > /etc/systemd/system/var-tmp.mount <<'EOF'
[Unit]
Description=Größeres tmpfs für /var/tmp im Live-System

[Mount]
What=tmpfs
Where=/var/tmp
Type=tmpfs
Options=size=50%%,nr_inodes=1m

[Install]
WantedBy=local-fs.target
EOF
systemctl enable var-tmp.mount

# Flatpaks read-only, damit sie unverändert ins neue System kopiert werden
cat > /etc/systemd/system/var-lib-flatpak.mount <<'EOF'
[Mount]
Type=none
What=/var/lib/flatpak
Where=/var/lib/flatpak
Options=bind,ro

[Install]
WantedBy=multi-user.target
EOF
systemctl enable var-lib-flatpak.mount

dnf clean all
