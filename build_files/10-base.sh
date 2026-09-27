#!/usr/bin/bash
# Grundlegende Pakete und Identität des Systems.
set -euxo pipefail

dnf5 install -y \
    python3 \
    nvtop \
    vulkan-tools \
    libva-utils \
    pciutils \
    mokutil

# Identität: Privos statt Fedora Kinoite anzeigen (Kompatibilitäts-IDs bleiben fedora)
IMAGE_PRETTY="Privos"
sed -i \
    -e "s|^NAME=.*|NAME=\"${IMAGE_PRETTY}\"|" \
    -e "s|^PRETTY_NAME=.*|PRETTY_NAME=\"${IMAGE_PRETTY} (${IMAGE_NAME:-privos}:${IMAGE_TAG:-latest})\"|" \
    -e "s|^HOME_URL=.*|HOME_URL=\"https://github.com/Tamino112/Privos\"|" \
    -e "s|^BUG_REPORT_URL=.*|BUG_REPORT_URL=\"https://github.com/Tamino112/Privos/issues\"|" \
    /usr/lib/os-release
grep -q '^IMAGE_VENDOR=' /usr/lib/os-release || echo "IMAGE_VENDOR=${IMAGE_VENDOR:-tamino112}" >> /usr/lib/os-release
