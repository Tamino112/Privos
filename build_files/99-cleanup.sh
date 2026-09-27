#!/usr/bin/bash
# Build-Reste entfernen, die nicht ins fertige Image gehören (bootc container lint).
set -euxo pipefail

dnf5 clean all
rm -rf /run/dnf /var/lib/dnf/repos
find /tmp /var/tmp -mindepth 1 -delete
