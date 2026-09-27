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
   - Ab **90 %** VRAM zeigt er einmal pro App eine Warnung mit dem größten Verbraucher,
     zum Beispiel „Game.exe nutzt 6,1 GB“.
   - **Volles VRAM allein ist kein Notfall.** Spiele wie ARK füllen den Grafikspeicher
     absichtlich bis zum Rand und laufen dabei stabil. Solange der PC reagiert, wird nichts beendet.
   - Eingegriffen wird erst, wenn der VRAM über **97 %** liegt **und** der PC 3 Sekunden lang
     wirklich hängt: Entweder stockt der Arbeitsspeicher (Linux-Speicherdruck, PSI), oder der
     Desktop (GNOME Shell/Mutter) antwortet nicht mehr. Dann wird die App mit dem meisten VRAM beendet.
   - Die App bekommt erst ein höfliches Beenden-Signal (SIGTERM) und nach 3 Sekunden ein hartes (SIGKILL).
   - **Spiel-Tipp:** Startet ein Spiel, während andere Apps zusammen mehr als 400 MB VRAM belegen
     (Browser, Discord …), nennt eine Benachrichtigung diese Apps. Geschlossen wird dabei nichts.
   - Desktop, Login, Audio und Systemprozesse werden **nie** beendet.
   - Auf Laptops lässt er die dGPU schlafen und weckt sie nicht zum Messen auf.
2. **VRAM-Budget für Spiele** (`privos-vram-budget.service`): Beim Start misst Privos das VRAM
   und meldet Proton-Spielen (DirectX 9–12) **1 GB weniger**, als die Karte hat. Bei einer
   8-GB-Karte sieht ARK also 7 GB. Unreal-Engine-Spiele richten ihren Texturspeicher danach aus,
   und der Desktop behält Platz. Technisch ist das die DXVK-Option `dxgi.maxDeviceMemory`, die beim
   Login als `DXVK_CONFIG` gesetzt wird. Das ist keine harte Grenze, sondern eine Angabe, nach der
   sich Spiele richten. Pro Spiel abschalten: Steam-Startoption `DXVK_CONFIG= %command%`.
3. **Desktop spart VRAM**: Ein NVIDIA-Anwendungsprofil
   (`/etc/nvidia/nvidia-application-profiles-rc.d/50-privos-desktop-vram.json`) verhindert, dass
   GNOME Shell freigegebenen Grafikspeicher horten (`GLVidHeapReuseRatio=0`). Das spart
   je nach Nutzung einige hundert MB.
4. **Notfall-Taste `Strg+Alt+Umschalt+Esc`** beendet sofort die App mit dem meisten VRAM.
   Den gleichen Effekt hat `privos-vram-guard panic` im Terminal.
5. **systemd-oomd**: Wenn der RAM 10 Sekunden lang zu 60 % blockiert ist, beendet es gezielt
   die App-Gruppe, die den Druck verursacht. Fedora-Standard wäre 80 % nach 20 Sekunden.
   Ist der Swap zu 90 % voll, greift es ebenfalls ein.
6. **ZRAM**: komprimierter Swap im RAM, so groß wie der RAM, höchstens 16 GB, mit zstd.
   Er puffert Speicherspitzen ab, statt einzufrieren.
7. **Magic SysRq** als letzter Ausweg: `Alt+Druck+F` beendet den größten RAM-Verbraucher,
   `Alt+Druck+B` startet den PC neu.

### Warum geht VRAM unter Linux nicht einfach in den RAM wie bei Windows?

Windows verschiebt bei vollem VRAM automatisch Daten in den normalen RAM („Gemeinsam genutzter
GPU-Speicher“). Das Spiel ruckelt dann, läuft aber weiter. Der NVIDIA-Treiber für Linux kann das
nur teilweise. Seit Treiber 595 weicht er unter Wayland besser auf den RAM aus, aber nicht so
zuverlässig wie Windows. Proton (vkd3d-proton) hätte eine eigene Auslagerung in den RAM, schaltet
sie bei NVIDIA aber ab, weil es sich auf den Treiber verlässt.

**Zum Ausprobieren** (pro Spiel, als Steam-Startoption):

```
VKD3D_DISABLE_EXTENSIONS=VK_EXT_pageable_device_local_memory %command%
```

Dann lagert Proton bei DirectX-12-Spielen selbst in den RAM aus, wenn der VRAM voll ist.
Das ist **experimentell**. Es kann Leistung kosten, und manche Spiele laufen damit schlechter.
Wenn es bei einem Spiel gut klappt, kann Privos es später für dieses Spiel automatisch setzen.

### ARK: Survival Ascended mit 8 GB VRAM

- Texturen auf **Mittel**, DLSS an (Qualität oder Balanced).
- In `ShooterGame/Saved/Config/Windows/Engine.ini` (im Spielordner) diesen Abschnitt ergänzen.
  Er legt den Texturspeicher fest auf 4 GB. Laut Community hilft das bei 8-GB-Karten
  (4000–4800 ausprobieren):
  ```ini
  [SystemSettings]
  r.Streaming.PoolSize=4000
  r.Streaming.LimitPoolSizeToVRAM=0
  ```
- Seit dem Unreal-5.5-Update berichten Spieler von einem VRAM-Leck. Wird es nach langen
  Sessions ruckelig, hilft ein Neustart des Spiels.

### Einstellungen anpassen

Die Standardwerte stehen in `/usr/share/privos/vram-guard.conf`. Eigene Werte gehören nach
`/etc/privos/vram-guard.conf`, zum Beispiel:

```ini
[guard]
# nur warnen, nie etwas beenden
mode = notify
# oder: schon eingreifen, wenn VRAM lange voll ist (auch ohne Hängen)
# mode = aggressive
# Spiel-Tipp ausschalten
game_hint = no
# oder: früher warnen
warn_percent = 85
# eigene Apps schützen
protected = gnome-shell, gdm, Xwayland, meine-app

[budget]
# nur 512 MB statt 1 GB für den Desktop reservieren (oder: enabled = no)
reserve_mib = 512
```

Danach: `sudo systemctl restart privos-vram-guard privos-vram-budget`, und für das
VRAM-Budget einmal ab- und wieder anmelden.

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

Die Treibermodule sind signiert. Der Privos-Installer registriert den Schlüssel automatisch.
Beim ersten Neustart nach der Installation erscheint ein blauer MOK-Bildschirm. Dort wählst du
„Enroll MOK“ → „Continue“ → „Yes“, gibst das Passwort **`privos`** ein und startest neu.

Manuell geht es so:

```bash
sudo mokutil --import /etc/pki/akmods/certs/akmods-ublue.der   # ein Einmal-Passwort festlegen
```

`privos-gpu-check` zeigt den genauen Befehl an, falls der Treiber nicht lädt.
