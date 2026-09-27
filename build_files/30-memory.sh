#!/usr/bin/bash
# Speicher-Schutz: System bleibt bedienbar, wenn RAM oder VRAM volllaufen.
set -euxo pipefail

# systemd-oomd beendet bei Speicherdruck gezielt die schuldige App statt das ganze System einzufrieren
systemctl enable systemd-oomd.service
