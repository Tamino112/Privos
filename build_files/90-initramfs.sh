#!/usr/bin/bash
# Initramfs neu bauen, damit die NVIDIA-Moduloptionen schon beim frühen Booten greifen.
set -euxo pipefail

KERNEL_VERSION="$(rpm -q --queryformat='%{evr}.%{arch}' kernel-core)"
export DRACUT_NO_XATTR=1
/usr/bin/dracut --no-hostonly --kver "${KERNEL_VERSION}" --reproducible --zstd -v --add ostree \
    -f "/usr/lib/modules/${KERNEL_VERSION}/initramfs.img"
chmod 0600 "/usr/lib/modules/${KERNEL_VERSION}/initramfs.img"
