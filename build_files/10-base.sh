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

# Identität: überall "Privos" statt Fedora Silverblue (ID_LIKE=fedora hält Fedora-Tools kompatibel)
# shellcheck source=/dev/null
source /usr/lib/os-release
PRIVOS_VERSION="${VERSION_ID}.$(date -u +%Y%m%d)"
sed -i \
    -e "s|^NAME=.*|NAME=\"Privos\"|" \
    -e "s|^PRETTY_NAME=.*|PRETTY_NAME=\"Privos ${VERSION_ID}\"|" \
    -e "s|^ID=fedora$|ID=privos\nID_LIKE=\"fedora\"|" \
    -e "s|^VERSION=.*|VERSION=\"${PRIVOS_VERSION} (NVIDIA Edition)\"|" \
    -e "s|^VARIANT=.*|VARIANT=\"NVIDIA Edition\"|" \
    -e "s|^LOGO=.*|LOGO=privos-logo|" \
    -e "s|^ANSI_COLOR=.*|ANSI_COLOR=\"0;38;2;76;167;183\"|" \
    -e "s|^CPE_NAME=.*|CPE_NAME=\"cpe:/o:privos:privos:${VERSION_ID}\"|" \
    -e "s|^DEFAULT_HOSTNAME=.*|DEFAULT_HOSTNAME=\"privos\"|" \
    -e "s|^HOME_URL=.*|HOME_URL=\"https://github.com/Tamino112/Privos\"|" \
    -e "s|^DOCUMENTATION_URL=.*|DOCUMENTATION_URL=\"https://github.com/Tamino112/Privos#readme\"|" \
    -e "s|^SUPPORT_URL=.*|SUPPORT_URL=\"https://github.com/Tamino112/Privos/issues\"|" \
    -e "s|^BUG_REPORT_URL=.*|BUG_REPORT_URL=\"https://github.com/Tamino112/Privos/issues\"|" \
    -e "/^REDHAT_/d" \
    /usr/lib/os-release
cat >> /usr/lib/os-release <<EOT
BOOTLOADER_NAME="Privos ${PRIVOS_VERSION}"
IMAGE_ID="${IMAGE_NAME:-privos-nvidia}"
IMAGE_VENDOR="${IMAGE_VENDOR:-tamino112}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
EOT
