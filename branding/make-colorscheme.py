#!/usr/bin/python3
"""Erzeugt das Farbschema "Privos Dark" aus Breeze Dark.

Breeze-Blau wird durch das Privos-Violett ersetzt, die Grautöne werden etwas dunkler und
kühler. Alle anderen Werte (Kontraste, Warn-/Fehlerfarben) bleiben wie in Breeze.
"""

import re
import sys

REPLACEMENTS = {
    # Akzent: Breeze-Blau -> Privos-Violett
    "61,174,233": "139,92,246",
    "29,153,243": "167,139,250",
    "30,87,116": "76,52,150",
    "147,206,233": "196,181,253",
    # Hintergründe: dunkler und leicht bläulich
    "32,35,38": "22,24,31",
    "41,44,48": "30,32,41",
    "20,22,24": "15,16,22",
    "29,31,34": "21,23,30",
    "49,54,59": "36,39,50",
    "35,38,41": "25,27,35",
    "27,30,32": "19,20,27",
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
