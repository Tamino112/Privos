# Privos & NVIDIA

Privos baut auf dem NVIDIA-Open-Treiber von Universal Blue auf. Er ist vorgebaut und
für Secure Boot signiert. Diese Datei beschreibt, was Privos zusätzlich einstellt und warum.

## Treiber

| Was | Einstellung | Warum |
|---|---|---|
| Treiber | NVIDIA Open Kernel Modules (aktueller Zweig) | Offizieller Weg für GTX 16xx / RTX 20xx und neuer |
| Nouveau/NVK | per Kernel-Parameter gesperrt, NVK-Vulkan entfernt | Spiele wählen nie versehentlich den falschen Treiber |
| Modeset/fbdev | Treiber-Standard (an) | Wayland, sauberer Bootscreen |
| Standby | VRAM wird nach `/var/tmp` gesichert (Treiber-Standard) | Keine Grafikfehler nach dem Aufwachen |
| `NVreg_UsePageAttributeTable=1` | Privos | Schnellere CPU↔GPU-Speicherzugriffe |
| Shader-Cache | 12 GB, kein Auto-Aufräumen | Weniger Shader-Ruckler |
| `PROTON_ENABLE_NVAPI=1` | Privos | DLSS, Reflex und NVIDIA-Features in Proton-Spielen |
| `nvidia-persistenced` | aus | Hält sonst die GPU wach (Laptop-Akku) |
| `nvidia-powerd` | an | Dynamic Boost auf Laptops |
| Flatpak | passende NVIDIA-Laufzeit wird automatisch installiert | Steam, Blender, OBS usw. als Flatpak nutzen die GPU |
| CUDA in Containern | `nvidia-container-toolkit` + CDI | `podman run --device nvidia.com/gpu=all …` |

## Schutz vor Einfrieren bei vollem VRAM

**Das Problem:** Ist der Grafikspeicher voll, lagert der NVIDIA-Treiber unter Linux in den
normalen RAM aus, oder Speicheranfragen schlagen fehl. Wird dann auch der RAM knapp, stockt
alles. Der Desktop kann den Bildschirm nicht mehr zeichnen, und der PC scheint aufgehängt.

**Die Lösung in Privos:** Mehrere Schutzschichten.

1. **privos-vram-guard**: ein eigener Dienst mit hoher Priorität. Er ist im RAM gesperrt,
   wird also nie ausgelagert, und ist vor dem OOM-Killer geschützt.
   - Er misst jede Sekunde über NVML den VRAM pro GPU und pro App.
   - Ab **90 %** VRAM zeigt er eine Warnung mit dem größten Verbraucher,
     zum Beispiel „Game.exe nutzt 6,1 GB“.
   - Liegt der VRAM über **97 %** und das System stockt 3 Sekunden lang
     (Linux-Speicherdruck, PSI), wird die App mit dem meisten VRAM beendet.
   - Sind weniger als **150 MB** VRAM frei, und das 8 Sekunden lang, wird die App ebenfalls beendet.
   - Die App bekommt erst ein höfliches Beenden-Signal (SIGTERM) und nach 3 Sekunden ein hartes (SIGKILL).
   - Desktop, Login, Audio und Systemprozesse werden **nie** beendet.
   - Auf Laptops lässt er die dGPU schlafen und weckt sie nicht zum Messen auf.
2. **Notfall-Taste `Strg+Alt+Umschalt+Esc`** beendet sofort die App mit dem meisten VRAM.
   Den gleichen Effekt hat `privos-vram-guard panic` im Terminal.
3. **systemd-oomd**: Wenn der RAM 10 Sekunden lang unter starkem Druck steht, beendet es
   gezielt die verursachende App. Standard wären mehr als 20 Sekunden.
4. **ZRAM**: komprimierter Swap im RAM, so groß wie der RAM, höchstens 16 GB, mit zstd.
   Er puffert Speicherspitzen ab, statt einzufrieren.
5. **Magic SysRq** als letzter Ausweg: `Alt+Druck+F` beendet den größten RAM-Verbraucher,
   `Alt+Druck+B` startet den PC neu.

### Einstellungen anpassen

Die Standardwerte stehen in `/usr/share/privos/vram-guard.conf`. Eigene Werte gehören nach
`/etc/privos/vram-guard.conf`, zum Beispiel:

```ini
[guard]
# nur warnen, nie etwas beenden
mode = notify
# oder: früher warnen
warn_percent = 85
# eigene Apps schützen
protected = kwin_wayland, plasmashell, Xwayland, meine-app
```

Danach: `sudo systemctl restart privos-vram-guard`

**Hinweis:** Eine eigene `protected`-Liste ersetzt die Standardliste. Übernimm deshalb die
Desktop-Prozesse aus der Standarddatei in deine Liste.

## Diagnose

```bash
privos-gpu-check           # prüft Treiber, Secure Boot, Wayland, Vulkan, Flatpak, CUDA, Speicherschutz
privos-vram-guard status   # VRAM-Belegung pro App
nvtop                      # Live-Monitor für GPU-Auslastung und VRAM
journalctl -u privos-vram-guard   # Log des VRAM-Wächters
```

## Secure Boot

Die Treibermodule sind mit dem Universal-Blue-Schlüssel signiert. Bei aktivem Secure Boot
muss der Schlüssel einmalig registriert werden:

```bash
sudo mokutil --import /etc/pki/akmods/certs/akmods-ublue.der   # Passwort: universalblue
```

Beim nächsten Neustart erscheint ein blauer MOK-Bildschirm. Dort wählst du
„Enroll MOK“ → „Continue“ → „Yes“, gibst das Passwort ein und startest neu.
`privos-gpu-check` zeigt den genauen Befehl an, falls der Treiber nicht lädt.
