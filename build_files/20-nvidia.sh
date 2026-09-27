#!/usr/bin/bash
# NVIDIA-Feinschliff auf Basis des Universal-Blue-Treibers.
set -euxo pipefail

# Build sofort abbrechen, falls das Basis-Image keinen passenden Treiber mitbringt
rpm -q kmod-nvidia nvidia-driver
KMOD_VERSION="$(rpm -q --queryformat '%{VERSION}' kmod-nvidia)"
DRIVER_VERSION="$(rpm -q --queryformat '%{VERSION}' nvidia-driver)"
if [[ "${KMOD_VERSION}" != "${DRIVER_VERSION}" ]]; then
    echo "kmod-nvidia (${KMOD_VERSION}) passt nicht zu nvidia-driver (${DRIVER_VERSION})" >&2
    exit 1
fi
echo "NVIDIA-Treiber ${DRIVER_VERSION}"

# Nouveau-Vulkan (NVK) entfernen, damit Spiele nie versehentlich den falschen Treiber wählen
rm -f /usr/share/vulkan/icd.d/nouveau_icd.*.json

# Persistence-Daemon hält die GPU dauerhaft wach (schlecht für Laptops/Akku).
# nvidia-powerd liefert Dynamic Boost auf Laptops und beendet sich sonst selbst.
systemctl disable nvidia-persistenced.service || true
systemctl enable nvidia-powerd.service || true

# Privos-Dienste
systemctl enable privos-vram-guard.service
systemctl enable privos-nvidia-flatpak-sync.service
