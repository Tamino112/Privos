# Privos – Projektstand für Claude

> Diese Datei liest Claude Code automatisch, wenn es in diesem Ordner gestartet wird.
> Sie beschreibt, was Privos ist, wie es gebaut wird und wie weit das Projekt ist.
> Stand: 27.09.2026 (zuletzt in einer Cloud-Sitzung bearbeitet, jetzt lokal weiter).

## Was ist Privos?

Ein eigenes Linux-Betriebssystem, inspiriert von **Zorin OS**, aber stärker optimiert:

- **Das Beste für NVIDIA-Grafikkarten**: aktueller Open-Treiber, Wayland, Secure Boot, CUDA.
- **Friert bei vollem VRAM/RAM nicht ein**: eigener VRAM-Wächter plus RAM-Schutz.
- **Modern und clean**: eigenes Logo, Wallpaper, Boot-Animation, Farbschema und KDE-Layout.
- **Gut für Game-Design und Coding**: Blender, Godot, UE5, IDEs und CUDA-Container (geplant).
- **Gaming**: Steam, Proton usw. (geplant).
  - Anti-Cheat ist ehrlich eingeordnet: Kernel-Anti-Cheat (Valorant, FACEIT usw.) läuft auf Linux nicht.
  - Umgehen wird es nicht geben.
  - Siehe die Anti-Cheat-Tabelle in `docs/PLAN.md`.
- **Eigene ISO mit Installer**, wie bei Zorin OS.

Der Nutzer spricht Deutsch. Antworten, Doku und UI-Texte sind deshalb auf Deutsch, Commit-Messages auf Englisch.

## Technische Basis

- **Fedora Atomic / bootc**: Das OS ist ein Container-Image. Updates kommen als neues Image, Rollback ist jederzeit möglich.
- **Basis-Image**: `ghcr.io/ublue-os/kinoite-nvidia:latest` von Universal Blue.
  - Fedora 44 mit KDE Plasma 6 und dem NVIDIA-Open-Treiber (negativo17).
  - Der Treiber ist mit dem ublue-Schlüssel für Secure Boot signiert.
- **Fertiges Privos-Image**: `ghcr.io/tamino112/privos-nvidia:latest`
  - Wird von GitHub Actions gebaut, zusätzlich mit den Tags `latest.YYYYMMDD` und `YYYYMMDD`.
- **ISO**: Wird mit **Titanoboa** (Universal Blue) aus dem Live-Image `installer/` gebaut.
  - Die Installation läuft über Anaconda, offline mit eingebettetem Image.

## Aufbau des Repos

| Pfad | Inhalt |
|---|---|
| `Containerfile` | Baut das Privos-Image auf `kinoite-nvidia` und startet `build_files/build.sh` |
| `build_files/10-base.sh` | Grundpakete und eigene Identität in `os-release` (`ID=privos`, Name „Privos“) |
| `build_files/15-branding.sh` | Logo-Icons, Wallpaper, Plymouth, KDE-Look-and-Feel, Farbschema, Schriften (Inter, JetBrains Mono), Papirus-Icons |
| `build_files/20-nvidia.sh` | Treiber-Prüfung, NVK-ICD entfernen, NVIDIA-Dienste aktivieren |
| `build_files/30-memory.sh` | systemd-oomd aktivieren |
| `build_files/90-initramfs.sh` | Initramfs neu bauen (enthält NVIDIA-Module und Privos-Optionen) |
| `build_files/99-cleanup.sh` | Aufräumen, damit `bootc container lint` sauber durchläuft |
| `system_files/` | Wird 1:1 ins Image kopiert. Enthält: |
| | • NVIDIA-Tuning: kargs, modprobe, Umgebungsvariablen |
| | • Speicherschutz: sysctl, ZRAM, oomd |
| | • Dienste und Tools: `privos-vram-guard`, `privos-gpu-check`, Flatpak-Treiber-Sync |
| | • KDE-Branding in `etc/xdg`, `usr/share/plasma/look-and-feel/org.privos.desktop` |
| `branding/` | Quell-SVGs (Logo, Wallpaper) und `make-colorscheme.py` (Breeze Dark → „Privos Dark“) |
| `installer/` | Live-ISO: `Containerfile` + `build.sh` machen aus dem Image ein Live-System mit Installer. Dazu gehören: |
| | • `iso.yaml`: Bootmenü |
| | • `flatpaks`: vorinstallierte Apps |
| | • Anaconda-Profil und Kickstart-Skripte |
| | • Willkommensfenster `privos-live-welcome` |
| `.github/workflows/build.yml` | Checks (shellcheck, Python-Tests), dann Image bauen, prüfen und nach GHCR pushen. Läuft bei jedem Push und wöchentlich |
| `.github/workflows/build-iso.yml` | Baut die ISO automatisch nach erfolgreichem Image-Build oder manuell per „Run workflow“. Die ISO landet als Artifact |
| `tests/` | Unit-Tests für VRAM-Wächter und Farbschema: `python3 -m unittest discover -s tests` |
| `docs/PLAN.md` | Gesamtplan: Vision, Architektur, Roadmap, Hardware-Testliste |
| `system_files/usr/share/doc/privos/NVIDIA.md` | Nutzer-Doku zu NVIDIA, Secure Boot und VRAM-Wächter |

## Wichtige Bausteine

### VRAM-Wächter (`system_files/usr/bin/privos-vram-guard`, Python)

- Liest über NVML (ctypes auf `libnvidia-ml.so.1`), wie voll der VRAM ist und welche Prozesse ihn belegen.
- Kombiniert das mit dem Speicherdruck aus PSI (`/proc/pressure/memory`).
- **Warnung**: ab 90 % VRAM für 5 s, als Desktop-Benachrichtigung.
- **Notfall** (beendet den größten VRAM-Verbraucher, zuerst mit SIGTERM, dann mit SIGKILL). Auslöser:
  - VRAM ≥97 % und das System stockt seit 3 s
  - oder weniger als 150 MiB frei für 8 s
- **Geschützt** sind Desktop-Prozesse (kwin, plasmashell, Xwayland, gamescope, pipewire …) und Systemprozesse (UID < 1000).
- **Modi** in `/etc/privos/vram-guard.conf`: `notify`, `balanced` (Standard), `aggressive`. Die Vorlage liegt in `usr/share/privos/vram-guard.conf`.
- **Notfall-Taste**: `Strg+Alt+Umschalt+Esc` (`privos-vram-guard panic`).
- **Laptops**: Schläft die GPU gerade, wird sie nicht geweckt.
- **Dienst**: `privos-vram-guard.service` mit hoher Priorität und OOM-geschützt.

### RAM-Schutz

- **ZRAM**: bis 16 GB, zstd.
- **systemd-oomd**: schärfer eingestellt als bei Fedora, 60 % Druck für 10 s.
- **sysctl**: Werte in `usr/lib/sysctl.d/60-privos-memory.conf`.
- **Notfall-Kombination**: SysRq ist aktiv.

### Diagnose

`privos-gpu-check` zeigt, ob Treiber, Secure Boot, Wayland, Vulkan, VA-API, Flatpak-Laufzeit, CUDA-Container, Wächter, oomd und ZRAM passen.

### Branding

- Violett (#8B5CF6) → Cyan, dunkles Design „Privos Dark“.
- Look-and-Feel `org.privos.desktop` mit Privos-Logo im Startmenü.
- Plymouth-Theme `privos`.
- Login- und Sperrbildschirm mit Privos-Wallpaper.

### Live-ISO

- **Bootmenü**:
  - „Privos starten“
  - „Grafik-Kompatibilitätsmodus“ (nomodeset)
- **Willkommensfenster**: „Ausprobieren“ oder „Privos installieren“.
- **Installer**: Anaconda installiert das eingebettete Image. Danach werden Updates über `bootc switch` auf `ghcr.io/tamino112/privos-nvidia:latest` umgestellt.
- **Secure Boot**: Der Schlüssel wird automatisch vorgemerkt. Beim ersten Neustart „Enroll MOK“ wählen, das Passwort ist `privos`.

## Wie weit sind wir? (Roadmap-Stand)

| Phase | Stand |
|---|---|
| 0 – Fundament (Repo, Containerfile, CI, GHCR) | ✅ fertig, Image baut in CI |
| 1 – NVIDIA (Treiber, Secure Boot, VRAM-Wächter, Diagnose) | 🔧 gebaut und im Container geprüft, **Test auf echter Hardware offen** |
| 3 – Look & Feel (Branding, Theme, Boot/Login) | 🔧 Grundausstattung fertig, auf echter Hardware noch nicht angesehen |
| 5 – ISO + Installer | 🔧 gebaut, **der erste CI-Lauf der ISO steht noch aus** |
| 2 – Gaming (Steam, Proton, Gamescope, MangoHud …) | ⏳ als Nächstes sinnvoll |
| 4 – Dev & GameDev (Blender, Godot, IDEs, CUDA-Dev-Boxen) | ⏳ |
| 6 – Feinschliff, Legacy-NVIDIA-Image (GTX 9xx/10xx), Release | ⏳ |

### Zuletzt passiert
- Commit `eacdc2d` „Add Privos branding and own live ISO with installer“ ist gepusht.
- Beim Pushen lief dafür der Workflow „Build Privos image“. Danach startet automatisch „Build Privos ISO“, das dauert etwa eine Stunde.
- Status prüfen: GitHub → Actions. Erst `build.yml`, dann `build-iso.yml`.

### Offene Punkte / Risiken
1. **ISO-Build ist unerprobt.** Wahrscheinliche Fehlerstellen:
   - das verschachtelte `podman pull` im Build
   - Flathub-Downloads
   - Titanoboa
   - Artifact-Upload
2. **Das Repo ist privat.** Das hat zwei Folgen:
   - Der Artifact-Speicher ist klein (ca. 500 MB im Free-Plan), der Upload der mehrere GB großen ISO scheitert dann.
   - Das GHCR-Paket `privos-nvidia` muss **öffentlich** sein, sonst bekommen installierte Systeme keine Updates.
   - Empfehlung: Repo öffentlich machen. Alternativ die ISO anders verteilen, z. B. in Teilen als Release-Asset.
3. **Hardware-Test**: Die Checkliste steht in `docs/PLAN.md` (Phase 1).
4. Image-Signierung mit cosign ist vorbereitet. Aktiv wird sie erst, wenn das Secret `SIGNING_SECRET` gesetzt ist.

### Nächste sinnvolle Schritte
1. Den ISO-Lauf in Actions beobachten und Fehler beheben.
2. ISO auf USB schreiben und auf dem NVIDIA-PC testen: `privos-gpu-check`, VRAM-Wächter, Standby, Aussehen.
3. Phase 2 (Gaming): Steam, Gamescope, MangoHud, Lutris/Heroic, Controller-Regeln usw. ins Image.
4. Phase 4 (Dev/GameDev): Entwickler-Tools und CUDA-Container-Setup.
5. Eine eigene Welcome-/Hub-App statt des einfachen yad-Dialogs.

## Arbeitsweise und Regeln

- **Branch**: `claude/sharp-hypatia-k6959x`. Das ist der Standard-Branch des Repos, Pushes darauf bauen `latest`.
- **Vor jedem Push lokal prüfen**:
  - `shellcheck build_files/*.sh installer/build.sh installer/system_files/usr/bin/* system_files/usr/bin/privos-gpu-check system_files/usr/libexec/privos/*`
  - `python3 -m unittest discover -s tests`
- **Image lokal bauen** (nur unter Linux mit podman, braucht viel Platz):
  `podman build -t localhost/privos-nvidia:test .`, danach `podman run --rm -it localhost/privos-nvidia:test bash` zum Nachsehen.
  - Unter Windows: Code bearbeiten und pushen reicht, GitHub baut in der Cloud.
- **Neue Dateien für das System** kommen nach `system_files/` (landen 1:1 im Image). Neue Build-Schritte kommen als `build_files/NN-name.sh` (werden der Reihe nach ausgeführt).
- **In `/usr` ablegen**: Nur `/usr` ist Teil des Images. `/etc` ist nur Vorgabe, `/var` bleibt beim Update unverändert.
- **Neue Tools im Workflow prüfen**: Ergänzungen in `.github/workflows/build.yml` im Schritt „Verify image“ mit prüfen lassen.
