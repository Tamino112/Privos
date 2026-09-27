# Privos

**Ein modernes, cleanes Linux-OS, das mit NVIDIA-Grafikkarten richtig gut läuft –
für Gaming, Game Development und Coding.**

Privos basiert auf Fedora Atomic (KDE Plasma) über [Universal Blue](https://universal-blue.org).
Das ganze Betriebssystem wird aus dem [`Containerfile`](Containerfile) gebaut.
Updates sind atomar: Wenn ein Update Probleme macht, wählst du beim Booten einfach die
vorherige Version.

> Status: **Phase 1 (NVIDIA)**. Siehe [Projektplan](docs/PLAN.md).

## Was Privos für NVIDIA macht

- NVIDIA-Open-Treiber vorinstalliert und für Secure Boot signiert, CUDA und Container-Support eingebaut
- **Schutz vor Einfrieren bei vollem VRAM**: [`privos-vram-guard`](system_files/usr/bin/privos-vram-guard)
  warnt früh und beendet im Notfall gezielt die schuldige App, statt dass der ganze PC hängt.
  Notfall-Taste: `Strg+Alt+Umschalt+Esc`
- systemd-oomd, ZRAM und Kernel-Tuning halten das System bedienbar, wenn der Speicher knapp wird
- DLSS/NVAPI in Proton, großer Shader-Cache, Hardware-Videodekodierung, Flatpak-Treiber-Sync
- [`privos-gpu-check`](system_files/usr/bin/privos-gpu-check): Diagnose mit einem Befehl

Details: [NVIDIA.md](system_files/usr/share/doc/privos/NVIDIA.md)

## Voraussetzungen

- NVIDIA **GTX 16xx / RTX 20xx oder neuer**. Ein Image für ältere Karten (GTX 9xx/10xx) ist geplant.
- UEFI; Secure Boot wird unterstützt

## Installieren / Testen

**Von einem bestehenden Fedora-Atomic-System aus** (Bazzite, Bluefin, Aurora, Kinoite …):

```bash
sudo bootc switch ghcr.io/tamino112/privos-nvidia:latest
systemctl reboot
```

**Per ISO:** Unter *Actions* → *Build Privos ISO* → *Run workflow* bauen. Die ISO erscheint
danach als Download beim Workflow-Lauf.

Das Container-Paket auf GHCR muss dafür **öffentlich** sein
(*Packages* → *privos-nvidia* → *Package settings* → *Change visibility*).

## Aufbau

```
Containerfile            Das OS: Basis-Image + Build-Schritte
build_files/             Build-Skripte (Pakete, NVIDIA, Speicherschutz, Initramfs)
system_files/            Dateien, die 1:1 ins System kopiert werden (/usr, /etc)
disk_config/             Installer-(ISO-)Konfiguration
tests/                   Tests (z. B. Entscheidungslogik des VRAM-Wächters)
.github/workflows/       Automatischer Build von Image und ISO
docs/PLAN.md             Vision & Roadmap
```

## Lokal bauen

```bash
podman build -t privos-nvidia:dev -f Containerfile .
python3 -m unittest discover -s tests -v
```

## Image-Signatur (optional, empfohlen)

```bash
cosign generate-key-pair   # cosign.key als Repo-Secret SIGNING_SECRET hinterlegen, cosign.pub committen
```
