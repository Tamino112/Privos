# Privos – aktueller Projektkontext

Stand: 27.09.2026. Der Nutzer spricht Deutsch; Antworten und Produkttexte sind auf Deutsch, Commit-Nachrichten auf Englisch.

## Produkt und Technik

Privos ist ein Fedora-Atomic/bootc-System auf Basis von `ghcr.io/ublue-os/silverblue-nvidia:latest` mit GNOME und NVIDIA-Open-Treiber. `Containerfile` baut das installierbare OS-Image. `installer/Containerfile` ergänzt Live-Boot, Flatpaks und den Privos-Installer. Die ISO wird mit Titanoboa gebaut. Maßgeblich sind die aktuellen Dateien im Repository, nicht ältere Aussagen über KDE oder Kinoite.

Das fertige Image wird von GitHub Actions nach GHCR (`ghcr.io/tamino112/privos-nvidia`) gepusht. Auf dem Standardbranch erhält es den Tag `latest`; andere Branches erhalten einen `br-…`-Tag. `.github/workflows/build-iso.yml` baut eine Offline-Live-ISO mit eingebettetem Image und lädt sie als Actions-Artefakt hoch.

## Verzeichnisstruktur

- `build_files/`: Schritte für das OS-Image; `build_files/build.sh` führt sie der Reihe nach aus.
- `system_files/`: Dateien für das installierte System, darunter GNOME-Standards, Branding, NVIDIA- und Speicherschutz.
- `branding/`: Logo, Wallpaper und Generator für die Plymouth-Animation.
- `installer/`: Live-System, eigener GTK4/libadwaita-Installer, Polkit-Helfer, Kickstart und ISO-Bootmenü.
- `docs/PLAN.md`: Roadmap; `docs/mockups/`: HTML-Entwürfe und Bilder zur UI-Gestaltung.
- `tests/`: Tests des VRAM-Wächters.
- `output/`: lokale ISOs, Prüfsummen und Build-Protokolle; absichtlich ignoriert. Keine großen ISOs ins Git-Repository committen.

## Verifizierter Stand

Am 27.09.2026 wurden OS-Image, Live-Image und ISO lokal unter Ubuntu/WSL2 mit Podman erfolgreich gebaut. `bootc container lint` bestand 14 Prüfungen. Die lokale ISO war 6.665.021.440 Byte groß; SHA-256: `2bee14a4fd73f9057725f51935c8fb290f7ed25997ba0ee454ec8459160d3287`. Die Windows-Kopie hatte dieselbe Prüfsumme. ISO9660-Signatur und UEFI-El-Torito-Eintrag wurden geprüft. Ein tatsächlicher Boot und eine Installation auf Hardware sind noch offen.

Die lokale ISO wurde danach erfolgreich mit QEMU/KVM unter WSL 2 gebootet; GNOME und das Privos-Willkommensfenster waren sichtbar. Die Installation auf die virtuelle Festplatte steht noch aus. `scripts/start-privos-vm.ps1 -Live` zeigt das Live-System jederzeit ohne neuen Build; eine Installation ist für die Vorschau nicht nötig. Nach einer optionalen Installation startet das Skript ohne Schalter die persistente VM ohne ISO.

Der lokale ISO-Build benutzte eine nur in der WSL-Buildkopie geänderte `installer/build.sh`, damit der Offline-Payload aus einer lokalen Registry gezogen werden konnte. Die Repo-Datei verwendet weiterhin den GitHub-Registry-Ref. Der GitHub-Workflow ist der reguläre Weg für neue ISO-Artefakte.

## Vor Änderungen und Pushes

- Quellcode und Assets im Repository bearbeiten; `output/` enthält nur temporäre Ergebnisse. Vorschauen, die erhalten bleiben sollen, nach `docs/mockups/` übernehmen.
- Shell-Skripte mit `shellcheck` und `bash -n` prüfen.
- `python3 -m unittest discover -s tests -v` sowie `python3 -m py_compile` für die Python-Starter ausführen.
- Bei Änderungen an Installer oder Boot-Dateien einen Image- und ISO-Build durchführen. Build-Erfolg ersetzt keinen Test des Boot- und Installationsablaufs.
- Aktuellen Branch und GitHub-Standardbranch vor dem Push prüfen. Repo: `https://github.com/Tamino112/Privos`.

Weitere Produktdetails stehen in `README.md`, `docs/PLAN.md` und `system_files/usr/share/doc/privos/NVIDIA.md`.
