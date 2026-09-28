# Privos UI-Entwürfe

Diese HTML-Entwürfe und Screenshots dokumentieren die Gestaltung vom 27.09.2026. Sie sind Referenzen für die Implementierung, keine Dateien der fertigen ISO.

- `boot-mockup.html`: Live-Vorschau der Bootanimation mit Start-, Passwort- und Update-Ansicht. Sie spielt die Logik von `privos.script` mit den Bildern aus `boot-assets/` nach; neu erzeugen mit `python3 branding/make-boot-assets.py docs/mockups/boot-assets`. Anzeigen über einen lokalen Webserver im Repo-Wurzelverzeichnis, z. B. `python3 -m http.server`, dann `/docs/mockups/boot-mockup.html` öffnen.
- `welcome-mockup.html`: Willkommensfenster in hell und dunkel.
- `installer-mockup.html`: Schritte des eigenen Installers.
- `software-mockup.html`: Privos Software.
- Die PNG-Dateien zeigen die jeweiligen Ansichten sowie Wallpaper-Vorschauen.

Die ausführbaren Quellen liegen weiterhin in `branding/`, `installer/` und `system_files/`. Der lokale `output/`-Ordner enthält gebaute ISOs und Protokolle und wird nicht versioniert.
