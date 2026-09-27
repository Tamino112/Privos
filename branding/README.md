# Privos-Identität

Das Zeichen ist ein geometrisches **P** mit zwei schrägen Abschlüssen. Es kommt ohne Verlauf, Glanz, Schatten und Punkt aus. Seine Form bleibt einfarbig und in kleinen Größen erkennbar.

| Datei | Einsatz |
| --- | --- |
| `privos-logo.svg` | Systemlogo, Startmenü, Installer-Symbol, „Über Privos“ |
| `privos-logo-symbolic.svg` | Einfarbiges GTK/KDE-Symbol bei 16 px |
| `privos-logo-boot.svg` | Helles Zeichen für Plymouth und KDE-Splash |
| `privos-logo-tile.svg` | Kachel im Live-Willkommensfenster und für App-Darstellungen |
| `privos-wordmark.svg` | Wortmarke auf hellem Hintergrund |
| `privos-wordmark-inverse.svg` | Wortmarke auf dunklem Hintergrund |
| `make-boot-spinner.py` | Erzeugt zwölf transparente Plymouth-Frames für den dezenten Punktring |
| `preview.svg` | Übersicht für die visuelle Abnahme; wird nicht ins System installiert |

**Farben:** Violett `#6757E5`, helles Violett `#A99CF7`, Nachtblau `#151729`, Weiß `#F8F8FF`. Die Wortmarken verwenden Inter SemiBold; beim Image-Build wird Inter installiert und die SVGs werden zusätzlich als PNG gerendert.

Das Zeichen braucht rundherum freie Fläche. Für 16 bis 24 px die ungekachelte oder symbolische Version verwenden. Die Kachel ist für größere Flächen gedacht. Farben und Grundform nicht pro Anwendung verändern.

`build_files/15-branding.sh` installiert die Varianten und erzeugt PNG-Größen für das Icon-Theme. Die Boot-Variante ersetzt das Plymouth-Wasserzeichen; die Punktring-Frames ersetzen dort den Fedora-Lader. Der KDE-Splash nutzt dieselbe helle Boot-Variante. Eine neue ISO enthält die Identität erst, nachdem das System-Image mit diesen Dateien neu gebaut wurde.
