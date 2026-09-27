#!/usr/bin/python3
"""Erzeugt das Farbschema "Privos Dark" aus Breeze Dark.

Breeze-Blau wird durch Petrol und kühles Türkis ersetzt, die Grautöne werden
etwas dunkler. Alle anderen Werte (Kontraste, Warn-/Fehlerfarben) bleiben wie in Breeze.
"""

import re
import sys

REPLACEMENTS = {
    # Akzent: Breeze-Blau -> Privos-Petrol/Türkis
    "61,174,233": "76,167,183",
    "29,153,243": "142,203,211",
    "30,87,116": "25,77,88",
    "147,206,233": "185,222,225",
    # Hintergründe: dunkles, neutrales Schiefergrau
    "32,35,38": "20,29,33",
    "41,44,48": "28,39,43",
    "20,22,24": "13,22,26",
    "29,31,34": "20,30,34",
    "49,54,59": "37,51,55",
    "35,38,41": "24,35,39",
    "27,30,32": "18,27,31",
}


def convert(text):
    pattern = re.compile(r"(?<![\d,])(" + "|".join(re.escape(k) for k in REPLACEMENTS) + r")(?![\d,])")
    text = pattern.sub(lambda m: REPLACEMENTS[m.group(1)], text)
    text = re.sub(r"^Name=.*$", "Name=Privos Dark", text, flags=re.M)
    text = re.sub(r"^Name\[[^\]]+\]=.*\n", "", text, flags=re.M)
    text = re.sub(r"^ColorScheme=.*$", "ColorScheme=PrivosDark", text, flags=re.M)
    return text


def main(src, dst):
    with open(src, encoding="utf-8") as f:
        text = f.read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(convert(text))


if __name__ == "__main__":
    main(*sys.argv[1:3])
