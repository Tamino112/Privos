# Privos

**Ein modernes, cleanes Linux-OS, das mit NVIDIA-Grafikkarten richtig gut läuft –
für Gaming, Game Development und Coding.**

Privos basiert auf Fedora Atomic (GNOME) über [Universal Blue](https://universal-blue.org).
Das ganze Betriebssystem wird aus dem [`Containerfile`](Containerfile) gebaut.
Updates sind atomar: Wenn ein Update Probleme macht, wählst du beim Booten einfach die
vorherige Version.

> Status: **Phase 1 (NVIDIA) + eigene Live-ISO mit Privos-Design**. Siehe [Projektplan](docs/PLAN.md).

Der Desktop nutzt GNOME mit einer Leiste am unteren Bildschirmrand, einem Privos-Startknopf
(auch über die Super-/Windows-Taste), dem hellblauen Standardhintergrund, Inter-Schrift
und Papirus-Icons. „Privos Software“ behält die GNOME-Software-Funktionen und bekommt ein
eigenes Symbol sowie den petrolfarbenen GNOME-Akzent. Die Standardwerte lassen sich in GNOME ändern.

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

## Herunterladen & Installieren

1. Auf GitHub **Actions** → **Build Privos ISO** öffnen und den neuesten grünen Lauf anklicken.
   Fehlt einer, dann oben rechts **Run workflow** drücken; der Build kann einige zehn Minuten dauern.
2. Unten bei **Artifacts** die Datei `privos-nvidia-…-live-amd64.iso` herunterladen.
   GitHub liefert sie als ZIP, darin liegt die ISO.
3. Die ISO mit [Fedora Media Writer](https://fedoraproject.org/workstation/download), balenaEtcher
   oder Ventoy auf einen USB-Stick schreiben (mindestens 16 GB).
4. Vom USB-Stick booten (UEFI, CSM/Legacy aus). Dann „Privos ausprobieren“ oder „Privos installieren“ wählen.
5. Nach der Installation mit Secure Boot: Beim ersten Neustart erscheint ein blauer MOK-Bildschirm.
   Dort **Enroll MOK** → **Continue** → **Yes** wählen, das Passwort `privos` eingeben und neu starten.

Updates kommen danach automatisch von `ghcr.io/tamino112/privos-nvidia:latest`.
Damit installierte PCs sie abrufen können, muss das Paket auf GitHub **öffentlich** sein
(*Packages* → *privos-nvidia* → *Package settings* → *Change visibility*).

**Quellcode:** `git clone https://github.com/Tamino112/Privos.git`, oder auf GitHub **Code** → **Download ZIP**.

## Aufbau

```
Containerfile            Das OS: Basis-Image + Build-Schritte
branding/                Logo, ImageGen-Wallpaper (PNG) und Plymouth-Animation
installer/               Live-ISO: Live-System, Installer (Anaconda), Willkommensfenster
build_files/             Build-Skripte (Pakete, NVIDIA, Speicherschutz, Initramfs)
system_files/            Dateien, die 1:1 ins System kopiert werden (/usr, /etc)
tests/                   Tests (z. B. Entscheidungslogik des VRAM-Wächters)
.github/workflows/       Automatischer Build von Image und ISO
docs/PLAN.md             Vision & Roadmap
docs/mockups/             HTML-Entwürfe und Screenshots für Boot, Welcome, Installer und Software
```

## Lokal bauen

Unter Linux oder WSL 2 mit Podman:

```bash
podman build -t privos-nvidia:dev -f Containerfile .
python3 -m unittest discover -s tests -v
```

## Ohne neue ISO in einer VM testen

Auf dem eingerichteten Windows-PC startet `scripts/start-privos-vm.ps1` Privos in
QEMU/KVM über WSL 2. Zum bloßen Anschauen reicht der Live-Start mit der bereits
gebauten ISO. Dabei wird nichts neu gebaut und keine Installation benötigt:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-privos-vm.ps1 -Live
```

Optional kann Privos aus dem Live-System auf die virtuelle 80-GB-Festplatte
installiert werden. Diese liegt unter `/root/privos-vm/privos.qcow2` in Ubuntu
und bleibt nach dem Schließen erhalten. Danach startet die installierte VM ohne ISO:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-privos-vm.ps1
```

Für Änderungen an GNOME-Einstellungen und Benutzerdateien kann man direkt in
der laufenden VM arbeiten. Änderungen am `Containerfile` oder unter
`system_files/` brauchen ein neues, veröffentlichtes OS-Image und danach in der VM
`sudo bootc upgrade` plus Neustart. Die ISO muss dafür nicht neu gebaut werden.
Die VM emuliert keine NVIDIA-Grafikkarte; NVIDIA-Funktionen brauchen einen Test
auf passender Hardware.

### Auf einem zweiten Windows-PC

1. Virtualisierung im BIOS aktivieren. In einer PowerShell als Administrator
   `wsl --install -d Ubuntu` ausführen und den PC bei Aufforderung neu starten.
2. Ubuntu öffnen und QEMU installieren:

   ```bash
   sudo apt update
   sudo apt install -y qemu-system-x86 qemu-utils ovmf
   ```

3. Das Repository mit `git clone https://github.com/Tamino112/Privos.git`
   herunterladen. Die fertige ISO einmalig vom ersten PC kopieren oder unter
   [GitHub Actions → Build Privos ISO](https://github.com/Tamino112/Privos/actions/workflows/build-iso.yml)
   als Artefakt herunterladen und aus dem ZIP entpacken. Artefakte dieses
   Workflows werden nach sieben Tagen gelöscht.
4. Im Repository die vorhandene ISO starten. `-IsoPath` akzeptiert einen
   Windows-Pfad; das Skript kopiert die ISO einmalig nach WSL:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start-privos-vm.ps1 -Live -IsoPath "C:\Pfad\zur\Privos.iso"
   ```

   Danach genügt `powershell -ExecutionPolicy Bypass -File .\scripts\start-privos-vm.ps1 -Live`.

Den Quellcode auf dem zweiten PC mit `git pull` aktualisieren. Die vorhandene
ISO zeigt weiterhin ihren damaligen Stand; für neue Systemänderungen muss ein
neues OS-Image gebaut oder eine neuere ISO übernommen werden.

## Image-Signatur (optional, empfohlen)

```bash
cosign generate-key-pair   # cosign.key als Repo-Secret SIGNING_SECRET hinterlegen, cosign.pub committen
```
