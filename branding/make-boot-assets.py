#!/usr/bin/env python3
"""Erzeugt die Bilder für die Privos-Bootanimation (Plymouth-Skript-Theme).

Design: tiefdunkler Grund mit weichem Petrol-Leuchten hinter dem Zeichen,
darunter eine schmale Ladelinie, über die ein heller Abschnitt gleitet.
Kein Drehrad. Alle Bilder werden ohne Abhängigkeiten direkt als PNG
geschrieben; das Logo selbst rendert der Image-Build mit rsvg-convert.

Die Bilder sind für 1080 Pixel Bildschirmhöhe ausgelegt, Ladelinie,
Eingabefeld und Punkte in doppelter Auflösung. privos.script skaliert
alles einmalig beim Start auf die tatsächliche Bildschirmhöhe.

Aufruf:
    make-boot-assets.py OUTPUT_DIRECTORY
"""

import math
import random
import struct
import sys
import zlib
from pathlib import Path

# Farben der Marke (siehe branding/README.md)
BASE = (5, 9, 13)             # Grund, identisch mit Window-Hintergrund im Skript
PETROL = (23, 103, 120)       # #176778
ACCENT = (76, 167, 183)       # #4CA7B7
DEEP = (12, 34, 58)           # kühles Blau für den unteren Schimmer
WHITE = (246, 248, 246)       # #F6F8F6, wie das Boot-Zeichen

BG_W, BG_H = 2560, 1080       # 21:9, bei 16:9 werden die Seiten beschnitten
LOGO_Y = 0.44                 # Mitte des Zeichens als Anteil der Höhe

BAR_W, BAR_H = 360, 6         # Ladelinie in doppelter Auflösung (180 × 3 px)
BAR_FRAMES = 75               # 1,5 s pro Durchlauf bei 50 Bildern/s
PROGRESS_STEPS = 50           # Fortschrittsbalken für Updates in 2-%-Schritten
SUPER = 4                     # Oversampling pro Achse


# --- PNG ---------------------------------------------------------------------------

def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(
        ">I", zlib.crc32(kind + data) & 0xFFFFFFFF
    )


def write_png(path: Path, width: int, height: int, pixels, channels: int = 4) -> None:
    stride = width * channels
    rows = b"".join(
        b"\x00" + bytes(pixels[y * stride:(y + 1) * stride]) for y in range(height)
    )
    color_type = 6 if channels == 4 else 2
    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(rows, 9))
        + png_chunk(b"IEND", b"")
    )


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


# --- Hintergrund -------------------------------------------------------------------

def background() -> bytearray:
    """Weiche Lichtfelder, gaußförmig und damit pro Achse separierbar.

    Zum Rand hin läuft alles exakt in BASE aus, damit breitere Bildschirme
    nahtlos mit der Hintergrundfarbe aufgefüllt werden können. Gegen
    Farbstufen wird mit festem Rauschen gedithert.
    """
    cx, cy = BG_W / 2, BG_H * LOGO_Y
    # (Farbe, Stärke, Mittelpunkt-Versatz y in H, Radius x in H, Radius y in H)
    fields = [
        (PETROL, 0.34, 0.00, 0.50, 0.36),   # Leuchten hinter dem Zeichen
        (ACCENT, 0.09, 0.00, 0.16, 0.14),   # heller Kern direkt am Zeichen
        (DEEP, 0.60, 0.80, 0.85, 0.26),     # kühler Schimmer am unteren Rand
    ]
    columns, rows = [], []
    for color, strength, offset, rx, ry in fields:
        columns.append([
            math.exp(-(((x + 0.5 - cx) / BG_H) / rx) ** 2)
            * (1 - smoothstep(0.90, 1.18, abs(x + 0.5 - cx) / BG_H))
            for x in range(BG_W)
        ])
        rows.append([
            strength * math.exp(-((((y + 0.5 - cy) / BG_H) - offset) / ry) ** 2)
            for y in range(BG_H)
        ])

    rng = random.Random(1707)
    tile = [rng.random() for _ in range(128 * 128)]
    pixels = bytearray(BG_W * BG_H * 3)
    for y in range(BG_H):
        weights = [r[y] for r in rows]
        noise = tile[(y % 128) * 128:(y % 128) * 128 + 128]
        base = y * BG_W * 3
        for x in range(BG_W):
            n = noise[x % 128]
            r, g, b = BASE
            for (color, *_), column, weight in zip(fields, columns, weights):
                k = column[x] * weight
                r += color[0] * k
                g += color[1] * k
                b += color[2] * k
            o = base + x * 3
            pixels[o] = min(255, int(r + n))
            pixels[o + 1] = min(255, int(g + n))
            pixels[o + 2] = min(255, int(b + n))
    return pixels


def halo(size: int = 480) -> bytearray:
    """Atmender Lichthof hinter dem Zeichen (Akzentfarbe, weich auslaufend)."""
    pixels = bytearray(size * size * 4)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            a = 0.0 if d >= 1 else math.exp(-(d / 0.42) ** 2) * (1 - d) ** 0.5
            o = (y * size + x) * 4
            pixels[o:o + 4] = bytes(ACCENT) + bytes((round(a * 0.55 * 255),))
    return pixels


# --- Ladelinie ---------------------------------------------------------------------

def capsule_distance(px: float, py: float, x0: float, x1: float, cy: float) -> float:
    """Abstand zu einer waagerechten Strecke von x0 bis x1 in der Höhe cy."""
    qx = min(max(px, x0), x1)
    return math.hypot(px - qx, py - cy)


def bar_image(segment, glide: bool = True) -> bytearray:
    """Schiene mit abgerundeten Enden; segment = (von, bis) in 0..1 oder None.

    glide blendet den Abschnitt zu den Enden der Schiene hin aus.
    """
    r = BAR_H / 2
    cy = BAR_H / 2
    x_min, x_max = r, BAR_W - r
    steps = [(k + 0.5) / SUPER for k in range(SUPER)]
    pixels = bytearray(BAR_W * BAR_H * 4)
    for y in range(BAR_H):
        for x in range(BAR_W):
            track = seg = 0.0
            for sy in steps:
                for sx in steps:
                    px, py = x + sx, y + sy
                    if capsule_distance(px, py, x_min, x_max, cy) > r:
                        continue
                    track += 1
                    if segment is None:
                        continue
                    lo = x_min + segment[0] * (x_max - x_min)
                    hi = x_min + segment[1] * (x_max - x_min)
                    if hi > lo and capsule_distance(px, py, lo, hi, cy) <= r:
                        seg += 1
            n = SUPER * SUPER
            track, seg = track / n, seg / n
            # Nach außen blendet der gleitende Abschnitt weich aus.
            u = (x + 0.5) / BAR_W
            fade = smoothstep(0.0, 0.14, u) * smoothstep(1.0, 0.86, u) if glide else 1.0
            seg_a = seg * 0.95 * fade
            track_a = track * 0.14
            alpha = seg_a + track_a * (1 - seg_a)
            if alpha <= 0:
                continue
            o = (y * BAR_W + x) * 4
            pixels[o:o + 4] = bytes(WHITE) + bytes((round(alpha * 255),))
    return pixels


def bar_segment(frame: int):
    """Unbestimmte Ladeanzeige: der Abschnitt wächst beim Losgleiten und
    schrumpft beim Auslaufen, wie aktuelle Material- und macOS-Lader."""
    t = frame / BAR_FRAMES
    ease = 0.45 * t + 0.55 * t * t * (3 - 2 * t)
    length = 0.10 + 0.32 * math.sin(math.pi * t)
    head = -0.02 + ease * 1.16
    return (head - length, head)


def entry_field(width: int = 520, height: int = 76, radius: float = 18) -> bytearray:
    """Eingabefeld für die Passwortabfrage (doppelte Auflösung)."""
    pixels = bytearray(width * height * 4)
    for y in range(height):
        for x in range(width):
            # Abgerundetes Rechteck als Abstandsfunktion
            qx = max(abs(x + 0.5 - width / 2) - (width / 2 - radius), 0)
            qy = max(abs(y + 0.5 - height / 2) - (height / 2 - radius), 0)
            d = math.hypot(qx, qy) - radius
            inside = min(1.0, max(0.0, 0.5 - d))
            border = min(1.0, max(0.0, 1.5 - abs(d + 1.5)))
            alpha = inside * 0.08 + border * 0.22
            if alpha <= 0:
                continue
            o = (y * width + x) * 4
            pixels[o:o + 4] = bytes(WHITE) + bytes((round(min(1.0, alpha) * 255),))
    return pixels


def bullet(size: int = 18) -> bytearray:
    pixels = bytearray(size * size * 4)
    c = size / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) - (c - 1)
            a = min(1.0, max(0.0, 0.5 - d))
            o = (y * size + x) * 4
            pixels[o:o + 4] = bytes(WHITE) + bytes((round(a * 255),))
    return pixels


def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for pattern in ("throbber-*.png", "bar-*.png", "progress-*.png"):
        for old in output.glob(pattern):
            old.unlink()
    write_png(output / "background.png", BG_W, BG_H, background(), channels=3)
    write_png(output / "halo.png", 480, 480, halo())
    for frame in range(BAR_FRAMES):
        write_png(output / f"bar-{frame}.png", BAR_W, BAR_H, bar_image(bar_segment(frame)))
    for step in range(PROGRESS_STEPS + 1):
        segment = (0.0, step / PROGRESS_STEPS) if step else None
        write_png(output / f"progress-{step}.png", BAR_W, BAR_H, bar_image(segment, glide=False))
    write_png(output / "entry.png", 520, 76, entry_field())
    write_png(output / "bullet.png", 18, 18, bullet())


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make-boot-assets.py OUTPUT_DIRECTORY")
    render(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
