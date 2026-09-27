# Privos-Identität

Das Zeichen entstand als Formstudie mit ImageGen. Die produktive Fassung ist als präzises, einfarbiges SVG nachgezeichnet: eine offene P-Form mit einer Richtung nach vorn im Negativraum. Keine Verläufe, Schatten, Lichtreflexe oder violetten Töne. Die gleiche Silhouette erscheint auf Bootscreen, App-Kachel und als Systemzeichen.

| Datei | Einsatz |
| --- | --- |
| `privos-logo.svg` | Systemlogo, Startmenü, Installer-Symbol, „Über Privos“ |
| `privos-logo-symbolic.svg` | Einfarbiges GTK-Symbol bei 16 px |
| `privos-logo-boot.svg` | Helles Zeichen für Plymouth |
| `privos-logo-tile.svg` | Kachel im Live-Willkommensfenster und für App-Darstellungen |
| `privos-wordmark.svg` | Wortmarke auf hellem Hintergrund |
| `privos-wordmark-inverse.svg` | Wortmarke auf dunklem Hintergrund |
| `wallpaper-dark.svg`, `wallpaper-light.svg` | Zurückhaltende Desktop-Hintergründe |
| `make-boot-spinner.py` | Erzeugt zwölf transparente Plymouth-Frames |
| `preview.svg` | Übersicht für die visuelle Abnahme; wird nicht ins System installiert |
| `concepts/privos-mark-imagegen.png` | ImageGen-Formstudie; wird nicht ins System installiert |

**Farben:** Petrol `#176778`, Akzent `#4CA7B7`, Dunkel `#101B2D`, gebrochenes Weiß `#EFF5F6`. Die Wortmarken verwenden Inter SemiBold; beim Image-Build wird Inter installiert und die SVGs werden zusätzlich als PNG gerendert.

**ImageGen-Modus:** neues Logo-Bitmap mit transparentem Hintergrund, anschließend Bearbeitung zur Vereinfachung. Der produktive Vektor wurde aus der Formstudie manuell konstruiert, weil das generierte PNG weiche Kanten hatte. Kern des Prompts: „Primary logo mark for Privos, a Linux operating system, for boot screen and desktop icon. One original minimal emblem on a transparent background. A distinctive negative-space opening suggesting a P and a forward path, at most three solid geometric forms, balanced silhouette legible at 16 px, single flat deep petrol blue (#176778). No text, purple, gradients, glow, shadows, glass, 3D, texture, app-tile background, four window panes, Ubuntu circles, Zorin Z, shield or watermark.“

Das Zeichen braucht rundherum freie Fläche. Für 16 bis 24 px die ungekachelte oder symbolische Version verwenden. Die Kachel ist für größere Flächen gedacht. Farben und Grundform nicht pro Anwendung verändern.

`build_files/15-branding.sh` installiert die Varianten und erzeugt PNG-Größen für das Icon-Theme. Die Boot-Variante ersetzt das Plymouth-Wasserzeichen; die Punktring-Frames ersetzen dort den Fedora-Lader. GNOME nutzt die gerenderten Hintergründe für hellen und dunklen Modus. Eine neue ISO enthält diese Änderungen erst, nachdem System-Image und ISO neu gebaut wurden.
