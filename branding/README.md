# Privos-Identität

Das Zeichen entstand als Formstudie mit ImageGen. Die produktive Fassung ist als präzises, einfarbiges SVG nachgezeichnet: eine offene P-Form mit einer Richtung nach vorn im Negativraum. Keine Verläufe, Schatten, Lichtreflexe oder violetten Töne. Die gleiche Silhouette erscheint auf Bootscreen, App-Kachel und als Systemzeichen.

| Datei | Einsatz |
| --- | --- |
| `privos-logo.svg` | Systemlogo, Startmenü, Installer-Symbol, „Über Privos“ |
| `privos-logo-symbolic.svg` | Einfarbiges GTK-Symbol bei 16 px |
| `privos-logo-boot.svg` | Helles Zeichen für Plymouth |
| `privos-logo-tile.svg` | Kachel im Live-Willkommensfenster und für App-Darstellungen |
| `privos-software.png` | Mit ImageGen gestaltetes Symbol für Privos Software |
| `privos-wordmark.svg` | Wortmarke auf hellem Hintergrund |
| `privos-wordmark-inverse.svg` | Wortmarke auf dunklem Hintergrund |
| `privos-wallpaper-default.png` | Vom Nutzer ausgewählter ImageGen-Hintergrund; Standard für Desktop und Sperrbildschirm |
| `privos-wallpaper-dark.png`, `privos-wallpaper-light.png` | Weitere ImageGen-Varianten, im Image enthalten |
| `make-boot-assets.py` | Erzeugt Hintergrund, Lichthof, Ladelinie, Update-Fortschritt und Passwortfeld für das Plymouth-Skript-Theme |
| `preview.svg` | Übersicht für die visuelle Abnahme; wird nicht ins System installiert |
| `concepts/privos-mark-imagegen.png` | ImageGen-Formstudie; wird nicht ins System installiert |

**Farben:** Petrol `#176778`, Akzent `#4CA7B7`, Dunkel `#101B2D`, gebrochenes Weiß `#EFF5F6`. Die Wortmarken verwenden Inter SemiBold; beim Image-Build wird Inter installiert und die SVGs werden zusätzlich als PNG gerendert.

**ImageGen-Modus:** neues Logo-Bitmap mit transparentem Hintergrund, anschließend Bearbeitung zur Vereinfachung. Der produktive Vektor wurde aus der Formstudie manuell konstruiert, weil das generierte PNG weiche Kanten hatte. Kern des Prompts: „Primary logo mark for Privos, a Linux operating system, for boot screen and desktop icon. One original minimal emblem on a transparent background. A distinctive negative-space opening suggesting a P and a forward path, at most three solid geometric forms, balanced silhouette legible at 16 px, single flat deep petrol blue (#176778). No text, purple, gradients, glow, shadows, glass, 3D, texture, app-tile background, four window panes, Ubuntu circles, Zorin Z, shield or watermark.“

Das Zeichen braucht rundherum freie Fläche. Für 16 bis 24 px die ungekachelte oder symbolische Version verwenden. Die Kachel ist für größere Flächen gedacht. Farben und Grundform nicht pro Anwendung verändern.

`build_files/15-branding.sh` installiert die Varianten und erzeugt PNG-Größen für das Icon-Theme.

**Bootanimation:** Plymouth nutzt das Skript-Plugin mit `system_files/usr/share/plymouth/themes/privos/privos.script`. Auf fast schwarzem Grund (`#05090D`) liegt ein weiches Petrol-Leuchten; das helle Zeichen gleitet beim Start ein, dahinter atmet ein Lichthof. Statt eines Drehrads zeigt eine schmale Ladelinie einen gleitenden Abschnitt. Bei Updates wird daraus ein Fortschrittsbalken mit Text, eine Passwortabfrage erscheint als abgerundetes Feld. Alle Bilder erzeugt `make-boot-assets.py` für 1080 px Höhe; das Skript skaliert sie beim Start auf die Bildschirmhöhe, breitere Bildschirme werden nahtlos mit der Grundfarbe aufgefüllt. `docs/mockups/boot-mockup.html` spielt die Animation mit denselben Bildern im Browser ab, ohne Image- oder ISO-Build. GNOME nutzt den ausgewählten ImageGen-Hintergrund in hellem und dunklem Modus als Standard. Eine neue ISO enthält diese Änderungen erst, nachdem System-Image und ISO neu gebaut wurden.

Der Startknopf nutzt das bestehende Privos-Zeichen. ArcMenu zeigt dazu ein kompaktes App-Menü und reagiert auf die Super-Taste. Das ImageGen-Symbol `privos-software.png` ersetzt das GNOME-Software-Symbol; der Systemakzent ist Petrol/Teal. Prompt für das Symbol: „Ein einzelnes modernes App-Icon auf transparentem Grund, tief petrolblaue abgerundete Kachel, klare helle Einkaufstasche mit offenem Durchgang im Negativraum, bei 24 px lesbar, ohne Text oder Glanz.“
