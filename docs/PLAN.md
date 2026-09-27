# Privos – Projektplan

> Ein modernes, cleanes Linux-OS, das mit NVIDIA-Grafikkarten richtig gut läuft –
> gebaut für Gaming, Game Development und Coding.

---

## 1. Vision

| Ziel | Was das konkret heißt |
|---|---|
| **NVIDIA first** | Treiber, CUDA, Wayland, Suspend, Secure Boot, DLSS – alles funktioniert ab der Installation, ohne Terminal-Gebastel |
| **Schön** | Modern, clean, einheitlich (eigenes Theme, Icons, Schrift, Boot-Screen, Login-Screen, Welcome-App) |
| **Gaming** | Steam/Proton, Lutris, Heroic, Gamescope, MangoHud, GameMode vorinstalliert und abgestimmt |
| **Game Dev** | Blender (CUDA/OptiX), Godot, Unreal Engine 5, Unity Hub, Krita, RenderDoc |
| **Coding** | VS Code/Zed, Git, Container (Podman/Distrobox), CUDA-Toolkit, Dev-Umgebungen per Klick |
| **Stabil** | Updates können das System nicht kaputt machen – jederzeit Rollback auf die vorherige Version |

---

## 2. Die wichtigste Entscheidung: Worauf bauen wir auf?

Ein OS komplett von Null (eigener Kernel, eigener Paketmanager) ist für eine Person
unrealistisch und bringt keinen Vorteil. Alle guten Gaming-Distros (Bazzite, CachyOS,
Nobara, Pop!_OS) bauen auf einer bestehenden Basis auf und verändern sie stark.
Genau das machen wir auch.

| Option | Basis | Vorteile | Nachteile |
|---|---|---|---|
| **A – Fedora Atomic / Universal Blue (empfohlen)** | Fedora Kinoite/Silverblue als Container-Image (bootc) | Atomare Updates + Rollback, NVIDIA-Treiber fertig gebaut und für Secure Boot signiert, ganzes OS wird aus einer `Containerfile` in GitHub Actions gebaut, ISO automatisch. Bazzite beweist, dass es funktioniert | Root-Dateisystem ist read-only (Apps kommen als Flatpak/Distrobox) – ist aber eher ein Feature |
| B – Arch (wie CachyOS) | archiso | Neueste Pakete, maximale Kontrolle, optimierte Kernel | Viel mehr Wartung, Updates können kaputtgehen, kein eingebautes Rollback |
| C – Ubuntu (wie Zorin) | Cubic / live-build | Riesige Community | Ältere Treiber & Mesa, genau das "nicht optimiert"-Problem von Zorin |

**Empfehlung: Option A.** Wir starten mit dem Universal-Blue-Image-Template und einem
NVIDIA-Basis-Image (z. B. `kinoite-nvidia-open`). Damit haben wir in Tag 1 ein
bootendes System mit funktionierendem NVIDIA-Treiber und können uns auf das
konzentrieren, was Privos besonders macht.

---

## 3. Architektur

```
  GitHub Repo (Privos)
  ├── Containerfile          ← definiert das komplette OS
  ├── build_files/           ← Skripte: Pakete, Tweaks, Theme
  ├── system_files/          ← Dateien, die 1:1 ins System kopiert werden (/etc, /usr)
  ├── branding/              ← Logo, Wallpaper, Theme, Plymouth, SDDM
  ├── hub/                   ← "Privos Hub" Welcome-/Settings-App
  └── .github/workflows/     ← baut Image + ISO automatisch
            │
            ▼
  GitHub Actions ──► Container-Image (ghcr.io/…/privos) ──► signiert mit cosign
            │
            ▼
  ISO-Installer (bootc-image-builder)  ──►  PC installiert Privos
            │
            ▼
  Updates: PC zieht einfach das neue Image  ──►  bei Problemen: Rollback beim Booten
```

### Image-Varianten

| Image | Für wen |
|---|---|
| `privos-nvidia` | RTX 20/30/40/50 & GTX 16 (NVIDIA Open Kernel Module) – Hauptfokus |
| `privos-nvidia-legacy` | GTX 9xx/10xx (proprietärer Treiber, letzter unterstützter Zweig 580) |
| `privos` | AMD/Intel (später, fast gratis mitgebaut) |

---

## 4. Die Bausteine im Detail

### 4.1 NVIDIA-Optimierung (Kern des Projekts)
- NVIDIA Open Kernel Modules, aktueller Treiberzweig, vorgebaut & signiert (Secure Boot via MOK)
- Wayland als Standard mit Explicit Sync (flüssig, kein Flackern), X11-Session als Fallback
- Kernel-Parameter: `nvidia-drm.modeset=1`, `nvidia-drm.fbdev=1`
- Suspend/Hibernate korrekt: `NVreg_PreserveVideoMemoryAllocations=1` + `nvidia-suspend/resume/hibernate`-Services
- VRR/G-Sync, HDR (KDE Plasma 6 + Gamescope)
- DLSS/Reflex/Ray Tracing in Proton: `PROTON_ENABLE_NVAPI=1`, DXVK-NVAPI standardmäßig an
- CUDA + `nvidia-container-toolkit` → CUDA/PyTorch in Containern ohne Setup
- Hardware-Video-Decode (NVDEC) für Browser & Videoplayer (`nvidia-vaapi-driver`)
- Laptops mit Hybrid-Grafik: Umschalten iGPU/dGPU per Klick (`supergfxctl` o. ä.)
- `privos-gpu-check`: Diagnose-Tool (Treiber geladen? Secure Boot ok? Wayland? Vulkan?)

### 4.2 Performance
- Scheduler: `sched_ext` mit `scx_lavd`/`scx_bpfland` (weniger Ruckler unter Last), optional später eigener Kernel mit BORE
- ZRAM statt Swap-Partition, `vm.max_map_count` hoch (nötig für viele Spiele)
- GameMode (CPU-Governor/Priorität beim Spielen), `ananicy-cpp`
- Shader-Cache-Größe erhöht (`__GL_SHADER_DISK_CACHE_SIZE`)
- Schnelles Booten: unnötige Services raus, Ziel < 15 s bis Desktop
- Benchmarks gegen Zorin & Windows (FPS, Frametimes, Bootzeit) → messbar besser, nicht nur "gefühlt"

### 4.3 Gaming
- Steam (mit Steam-Input-udev-Regeln), Lutris, Heroic (Epic/GOG/Amazon), ProtonPlus (Proton-GE verwalten)
- Gamescope, MangoHud (FPS-Overlay), vkBasalt
- Controller: Xbox (xpadneo/xone), PlayStation, Switch – ab Werk
- Optional später: "Game Mode"-Session im Stil von SteamOS (Big Picture direkt beim Boot)

### 4.4 Anti-Cheat – ehrliche Einschätzung
Das ist **keine technische OS-Frage**, sondern eine Entscheidung der Spielehersteller.

| Anti-Cheat | Status auf Linux |
|---|---|
| Easy Anti-Cheat (EAC) | Funktioniert über Proton – **wenn** der Entwickler es freischaltet (z. B. Elden Ring, Apex war mal an) |
| BattlEye | Ebenso – funktioniert, wenn freigeschaltet (z. B. DayZ, ARK) |
| Kernel-Anti-Cheat: Vanguard (Valorant, LoL), FACEIT, Ricochet (CoD), Javelin (Battlefield) | **Geht nicht** – blockiert Linux absichtlich |
| Fortnite | EAC unterstützt Linux, Epic hat es aber bewusst deaktiviert |

Anti-Cheat austricksen oder Windows vortäuschen führt zu **Account-Banns** und bricht die
Nutzungsbedingungen – das machen wir nicht. Was Privos stattdessen tun kann:
1. Beste Kompatibilität für alles, was freigeschaltet ist (aktuelles Proton, richtige Runtime)
2. **Anti-Cheat-Checker im Privos Hub**: zeigt für deine Spiele-Bibliothek an, was läuft
   (Daten von areweanticheatyet.com / ProtonDB)
3. **Dual-Boot mit Windows einfach machen**: Installer erkennt Windows, "Neustart in Windows"-Button
   für die paar Spiele, die es wirklich brauchen

### 4.5 Game Development
- Blender (CUDA/OptiX-Rendering out of the box), Godot (inkl. .NET), Krita, GIMP, Inkscape
- Unreal Engine 5 (native Linux-Version, Setup-Skript), Unity Hub
- RenderDoc (Grafik-Debugging), Audacity/LMMS, OBS Studio (NVENC-Aufnahme)
- Tablets (Wacom etc.) ab Werk

### 4.6 Coding
- VS Code und/oder Zed, JetBrains Toolbox (optional)
- Podman + Docker-Kompatibilität, Distrobox (beliebige Distro als Dev-Umgebung – z. B. Ubuntu-Box für alles, was nur für Ubuntu gibt)
- Vorgefertigte Dev-Boxen per Klick: C/C++, Rust, Python+CUDA/PyTorch, Node, .NET, Go
- Terminal: modern (z. B. Ptyxis oder WezTerm), Shell mit guten Defaults (Starship-Prompt, fzf, zoxide)
- `just`-Befehle für alles: `pv update`, `pv setup-dev python-cuda`, `pv gpu-check` …

### 4.7 Look & Feel ("Zorin-schön, aber eigenständig")
- **Desktop: KDE Plasma 6** (beste NVIDIA-Wayland-, HDR- und VRR-Unterstützung, extrem anpassbar)
  – Alternativ GNOME (näher am Zorin-Look). → *Entscheidung offen, siehe unten*
- Eigenes Theme: dunkel/hell, abgerundete Ecken, dezente Transparenz, eine Akzentfarbe
- Layout-Presets wie bei Zorin: "Windows-Style", "macOS-Style", "Minimal"
- Schrift: Inter (UI) + JetBrains Mono (Code); Icon-Set (z. B. Papirus, angepasst)
- Eigenes Logo, Wallpaper-Set, Plymouth-Bootanimation, Login-Screen, GRUB-Theme
- **Privos Hub** (eigene App): Willkommen-Tour, Layout wählen, Apps-Bundles (Gaming/GameDev/Coding) installieren, GPU-Check, Anti-Cheat-Checker, Updates & Rollback

---

## 5. Roadmap

| Phase | Inhalt | Ergebnis |
|---|---|---|
| **0 – Fundament** | Repo-Struktur, Containerfile auf NVIDIA-Basis, GitHub Actions, Image-Signierung | Image baut automatisch und bootet in einer VM |
| **1 – NVIDIA** | Treiber, Secure Boot, Wayland, Suspend, CUDA, NVDEC, `gpu-check` | Auf echter NVIDIA-Hardware getestet, alles läuft |
| **2 – Gaming** | Steam, Proton, Lutris, Heroic, Gamescope, MangoHud, Controller, Tweaks | Erste Spiele laufen, FPS-Benchmarks vs. Zorin/Windows |
| **3 – Look & Feel** | Theme, Branding, Boot/Login-Screen, Layout-Presets | Sieht aus wie ein eigenes, fertiges OS |
| **4 – Dev & GameDev** | Tools, Dev-Boxen, CUDA-Container, `pv`-Befehle | Blender/Godot/UE5 + Coding-Setup in Minuten |
| **5 – Privos Hub + ISO** | Welcome-App, Anti-Cheat-Checker, grafischer Installer, Dual-Boot | Installierbare ISO für andere Leute |
| **6 – Feinschliff** | Performance-Tuning, Laptop-Support, Legacy-NVIDIA-Image, Doku, Website | Erster öffentlicher Release (v1.0) |

---

## 6. Was du brauchst
- **Echte NVIDIA-Hardware zum Testen** (VMs haben keine echte NVIDIA-GPU)
- USB-Stick (8 GB+) oder zweite SSD / Partition zum Testen
- GitHub-Account (Builds laufen kostenlos in GitHub Actions)
- Optional: zweiter Rechner / VM mit virt-manager für schnelle Tests

---

## 7. Offene Entscheidungen
1. **Desktop:** KDE Plasma 6 (empfohlen) oder GNOME (Zorin-ähnlicher)?
2. **Welche NVIDIA-Karte hast du?** (Bestimmt, ob wir mit `nvidia-open` oder Legacy starten)
3. **Basis:** Universal Blue selbst (volle Kontrolle) oder direkt auf Bazzite aufsetzen (schneller viel Gaming-Zeug gratis, aber weniger "eigenes" OS)?
4. **Look:** Hast du Referenzen (Screenshots, Farben, Stil), wie Privos aussehen soll?
5. **Name/Branding:** Bleibt es bei "Privos"?
