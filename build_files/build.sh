#!/usr/bin/bash
# Einstiegspunkt für den Image-Build. Führt alle nummerierten Schritte der Reihe nach aus.
set -euo pipefail

CTX="$(dirname "$(readlink -f "$0")")"

echo "::group::System-Dateien kopieren"
cp -avf "${CTX}/system_files/." /
echo "::endgroup::"

for step in "${CTX}"/[0-9][0-9]-*.sh; do
    echo "::group::$(basename "${step}")"
    bash "${step}"
    echo "::endgroup::"
done
