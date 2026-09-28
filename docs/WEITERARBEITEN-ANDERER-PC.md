# Privos auf einem anderen PC weiterentwickeln

Stand: 27. September 2026. Diese Datei ist die Übergabe für den nächsten PC und
für eine neue Codex-Sitzung. **Ziel:** Den Privos-Desktop schnell in einer VM
sehen und am Quellcode weiterarbeiten. Eine neue ISO ist für jeden VM-Start
unnötig.

## Was bereits vorhanden und geprüft ist

- Repository: <https://github.com/Tamino112/Privos>. Der damalige Standardbranch
  heißt `claude/sharp-hypatia-k6959x`; beim Klonen den aktuellen Standardbranch
  von GitHub übernehmen und vor dem Push erneut prüfen.
- Privos ist ein Fedora-Atomic-/bootc-System mit GNOME auf einer Universal-Blue-
  NVIDIA-Basis. Das `Containerfile` erzeugt das installierbare OS-Image;
  `installer/` erzeugt das Live-System und die ISO. Weiteren Projektkontext
  enthalten `CLAUDE.md`, `README.md` und `docs/PLAN.md`.
- Das OS-Image, das Live-Image und die ISO wurden auf dem ersten Windows-PC
  gebaut. Die lokale ISO bootete mit QEMU/KVM unter WSL 2 bis zum sichtbaren
  GNOME-Desktop und Privos-Willkommensfenster. Die Installation auf eine
  virtuelle Festplatte wurde noch nicht geprüft.
- Der [erfolgreiche ISO-Lauf vom 27.09.2026](https://github.com/Tamino112/Privos/actions/runs/36348337298)
  enthält das Artefakt `privos-nvidia-latest-20260927-live-amd64.iso`.
  Das Artefakt läuft am **04.10.2026 um 20:58 UTC** ab. Vor dem Download
  prüfen, ob inzwischen ein neuerer erfolgreicher ISO-Lauf existiert.
- ISO und virtuelle Festplatte liegen absichtlich **nicht** im Git-Repository.
  Der Quellcode ist auf GitHub; eine ISO muss auf dem neuen PC einmalig
  heruntergeladen oder vom ersten PC kopiert werden.

## Auftrag für die nächste Codex-Sitzung

Auf dem neuen PC zuerst Betriebssystem, Virtualisierung, freien Speicherplatz,
vorhandene WSL-Distributionen und Git-Checkout prüfen. Danach die folgenden
Schritte passend zur tatsächlichen Umgebung ausführen und den Privos-Desktop
in der VM sichtbar prüfen. Vorhandene Quellcodeänderungen oder VM-Daten
erhalten; keinen neuen ISO-Build nur für die Vorschau starten.

## 1. Quellcode holen

In PowerShell auf dem neuen Windows-PC:

```powershell
git clone https://github.com/Tamino112/Privos.git
cd Privos
git status
```

Ist das Repository schon vorhanden, dort `git status` prüfen und bei sauberem
Checkout `git pull --ff-only` ausführen. Den aktuellen Standardbranch nicht
aus älteren Notizen ableiten.

## 2. Einmalig WSL 2 und QEMU einrichten

Auf einem Windows-PC muss Hardwarevirtualisierung im BIOS/UEFI aktiviert sein.
Windows 11 oder Windows 10 ab Build 19044 unterstützt die hier genutzten
Linux-GUI-Fenster über WSLg. In einer **PowerShell als Administrator**:

```powershell
wsl --install -d Ubuntu
```

Bei Aufforderung Windows neu starten und Ubuntu einmal öffnen, um das
Linux-Benutzerkonto einzurichten. Falls WSL bereits existiert, zuerst
`wsl --list --verbose` prüfen. In Ubuntu:

```bash
sudo apt update
sudo apt install -y qemu-system-x86 qemu-utils ovmf
test -e /dev/kvm && echo 'KVM verfügbar'
```

Fehlt `/dev/kvm`, WSL 2 und die Virtualisierung prüfen. Microsoft dokumentiert
`nestedVirtualization` in `%UserProfile%\.wslconfig`; diese Option ist
normalerweise bereits eingeschaltet. Das Startskript meldet fehlendes KVM
ausdrücklich. Hat die Distribution einen anderen Namen als `Ubuntu`, beim
Startskript `-Distro "Name"` angeben.

## 3. Fertige ISO einmalig besorgen

Auf GitHub unter [Actions → Build Privos ISO](https://github.com/Tamino112/Privos/actions/workflows/build-iso.yml)
den neuesten **erfolgreichen** Lauf öffnen. Unter **Artifacts** die ISO
herunterladen und aus dem ZIP entpacken. Für GitHub-Artefakte ist eine
Anmeldung nötig. Die ISO ist mehrere Gigabyte groß; bei langsamem Download
kann sie vom ersten PC per USB-Stick oder lokales Netzwerk kopiert werden.

Die auf dem ersten PC lokal gebaute ISO liegt unter
`C:\Users\tamin\Documents\coden\os\Privos\output\privos-nvidia-local-20260927-live-amd64.iso`.
Nur **für genau diese lokale Datei** lautet SHA-256:
`2bee14a4fd73f9057725f51935c8fb290f7ed25997ba0ee454ec8459160d3287`.
Das GitHub-Artefakt kann eine andere Prüfsumme haben.

Ist das Artefakt abgelaufen und keine ISO verfügbar, einen neuen Lauf über
**Run workflow** starten oder die ISO vom ersten PC kopieren. Ein solcher
Build kann dauern; danach wird die fertige ISO auf dem neuen PC beliebig oft
ohne erneuten Build gestartet.

## 4. Privos sofort als Live-System sehen

Im geklonten Repository in PowerShell die **entpackte** ISO angeben:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-privos-vm.ps1 -Live -IsoPath "C:\Pfad\zur\Privos.iso"
```

Das Skript kopiert die ISO beim ersten Aufruf einmal nach WSL, legt eine
virtuelle 80-GB-Festplatte an und startet QEMU mit 4 virtuellen CPUs und 8 GB
RAM. Der erste Kopiervorgang kann einige Minuten brauchen. Nach dem Start
prüfen, ob GNOME und das Privos-Willkommensfenster sichtbar sind. Später:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-privos-vm.ps1 -Live
```

Die VM bootet jetzt nur die schon vorhandene ISO. **Keine Installation und
kein neuer ISO-Build sind zum Anschauen erforderlich.** Änderungen, die man
innerhalb dieses Live-Systems vornimmt, gehen beim Herunterfahren verloren.

## Optional: dauerhafte VM installieren

Im Live-System „Install Privos“ starten und die virtuelle 80-GB-Festplatte
wählen. Nach erfolgreicher Installation das Live-System herunterfahren und
die installierte VM ohne `-Live` starten:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-privos-vm.ps1
```

Die virtuelle Festplatte und die UEFI-Einstellungen liegen in der WSL-
Distribution unter `/root/privos-vm/privos.qcow2` und
`/root/privos-vm/OVMF_VARS_4M.fd`. Sie sind **nicht** auf GitHub. Wenn exakt
derselbe installierte VM-Zustand auf einen weiteren PC soll, beide Dateien
separat und nur bei ausgeschalteter VM übertragen. Auf dem ersten PC war die
Festplatte zuletzt noch nicht installiert; für die Live-Vorschau ist ihre
Übertragung nicht erforderlich.

## Weiterentwickeln ohne unnötige Wartezeit

- `git pull --ff-only` holt neuen Quellcode. `git status` vor Änderungen und
  Pushes prüfen. Nach der Arbeit passende Tests ausführen, committen und
  `git push` verwenden, damit der Stand auf GitHub bleibt.
- `docs/mockups/*.html` kann man für Entwürfe direkt im Browser öffnen. Das
  zeigt ein Mockup sofort, aber nicht automatisch den echten GNOME-Desktop.
- In einer **installierten** VM lassen sich Benutzerdateien und GNOME-
  Einstellungen direkt ändern. Die Live-VM vergisst solche Änderungen beim
  Herunterfahren.
- Änderungen unter `system_files/` ohne Build sofort in der installierten VM
  prüfen: In der VM einmal `sudo systemctl enable --now sshd` ausführen, dann
  auf dem Windows-PC
  `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-sync.ps1 -VmHost <IP-der-VM> -User <Benutzer>`.
  Das Skript macht `/usr` per `bootc usr-overlay` vorübergehend beschreibbar,
  kopiert `system_files/` hinein und lädt dconf, GSettings-Schemas und systemd
  neu. Nach einem Neustart der VM gilt wieder das installierte Image.
- Auf dem zweiten PC (selbst eine Proxmox-VM ohne verschachtelte
  Virtualisierung) läuft Privos als eigene Proxmox-VM 110 „test“; die Konsole
  ist über die Proxmox-Weboberfläche erreichbar. Die dort installierte VM
  verfolgt nach der Installation `ghcr.io/tamino112/privos-nvidia:br-codex-privos-identity`
  (Stand 28.09.2026, `rpm-ostree status`). Für den Standardbranch einmal
  `sudo bootc switch ghcr.io/tamino112/privos-nvidia:latest` ausführen; danach
  holt `sudo bootc upgrade` neue Images dieses Tags.
- Die installierte VM nutzt die Tastaturbelegung, die im Installer gewählt
  wurde (Standard: `us`). In der Proxmox-Konsole liegen Sonderzeichen dann
  anders als auf einer deutschen Tastatur.
- Änderungen am `Containerfile`, unter `system_files/` oder an Systempaketen
  erscheinen nicht automatisch in einer vorhandenen ISO. Dafür ein neues
  OS-Image veröffentlichen und in der installierten VM `sudo bootc upgrade`
  mit anschließendem Neustart ausführen. Für Änderungen an Live-Boot oder
  Installer ist eine neue ISO zum Prüfen dieser Änderungen nötig.
- Der GitHub-Workflow baut nach relevanten Pushes das Image und anschließend
  eine neue ISO. Für die bloße Vorschau immer zuerst die vorhandene ISO oder
  installierte VM starten. Eine QEMU-VM besitzt keine echte NVIDIA-GPU;
  NVIDIA-Funktionen zusätzlich auf passender Hardware testen.
- Vor dem Push die passenden Prüfungen aus `CLAUDE.md` ausführen. Große ISOs,
  `.qcow2`-Dateien und `output/` gehören nicht in Git.

## Referenzen

- [Microsoft: WSL installieren](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Microsoft: Linux-GUI-Apps mit WSL](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)
- [Microsoft: WSL-Konfiguration und nestedVirtualization](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
- [GitHub: Workflow-Artefakte herunterladen](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)
