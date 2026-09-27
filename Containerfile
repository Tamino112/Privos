# Privos – ein modernes Linux-OS, optimiert für NVIDIA, Gaming, Game Dev und Coding.
#
# Das komplette Betriebssystem wird aus dieser Datei gebaut (bootc / Fedora Atomic).
# Basis: Universal Blue "silverblue-nvidia" = Fedora Silverblue (GNOME) mit vorgebautem,
# für Secure Boot signiertem NVIDIA-Open-Treiber, CUDA-Container-Support und Multilib.

ARG BASE_IMAGE="ghcr.io/ublue-os/silverblue-nvidia"
ARG BASE_TAG="latest"

# Build-Skripte und Systemdateien, die nicht selbst im fertigen Image landen sollen
FROM scratch AS ctx
COPY build_files /
COPY system_files /system_files
COPY branding /branding

FROM ${BASE_IMAGE}:${BASE_TAG}

ARG IMAGE_NAME="privos-nvidia"
ARG IMAGE_VENDOR="tamino112"
ARG IMAGE_TAG="latest"

RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=cache,dst=/var/log \
    --mount=type=tmpfs,dst=/tmp \
    IMAGE_NAME="${IMAGE_NAME}" IMAGE_VENDOR="${IMAGE_VENDOR}" IMAGE_TAG="${IMAGE_TAG}" \
    /ctx/build.sh

RUN bootc container lint
