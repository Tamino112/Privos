#!/usr/bin/env python3
"""Erzeugt den Privos-Bootspinner für Plymouth.

Design: moderner "Donut"-Ring wie der aktuelle Windows-11-Lader – ein
glatter, dünner Kreisbogen (~270°) mit runden Enden, dessen heller Kopf
um den Kreis wandert. Keine Abhängigkeiten, die PNGs werden direkt
geschrieben.

Aufruf:
    make-boot-spinner.py OUTPUT_DIRECTORY   Frames als throbber-XXXX.png
    make-boot-spinner.py --preview FILE     Filmstreifen-Vorschau (8 Frames)
"""

import math
import struct
import sys
import zlib
from pathlib import Path

SIZE = 96             # Kantenlänge der quadratischen Frames
FRAMES = 36           # Frames pro Umlauf (≈1,8 s bei den 50 ms des two-step-Plugins)
RADIUS = 34.0         # Mittellinie des Ringes
STROKE = 5.5          # Strichstärke in Pixeln
ARC = 1.5 * math.pi   # Länge des Bogens (270°, der Rest bleibt frei)
COLOR = (238, 246, 247)   # fast weiß, zur Marke leicht kühl
SUPER = 4             # Oversampling pro Achse


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(
        ">I", zlib.crc32(kind + data) & 0xFFFFFFFF
    )


def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    rows = b"".join(
        b"\x00" + pixels[y * width * 4 : (y + 1) * width * 4]
        for y in range(height)
    )
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(rows, 9))
        + png_chunk(b"IEND", b"")
    )


def frame_pixels(frame: int) -> bytearray:
    rotation = 2 * math.pi * frame / FRAMES
    half = STROKE / 2 + 0.7  # halbe Strichbreite plus AA-Saum
    cap = (STROKE / 2) / RADIUS  # Bogenlänge der runden Enden in Radiant
    pixels = bytearray(SIZE * SIZE * 4)
    steps = [k / SUPER + 0.5 / SUPER for k in range(SUPER)]
    center = (SIZE - 1) / 2

    for y in range(SIZE):
        for x in range(SIZE):
            cov = 0.0
            for sy in steps:
                for sx in steps:
                    px, py = x + sx, y + sy
                    dx, dy = px - center, py - center
                    dist = math.hypot(dx, dy)
                    # Kantiges Profil: innen konstant, am Rand kurzer weicher Abfall
                    t = abs(dist - RADIUS) / half
                    if t >= 1.0:
                        continue
                    ring = (1.0 - t * t) ** 2
                    # Bogenparameter: 0 = Ansatz, ARC = Kopf des Bogens
                    s = (math.atan2(dy, dx) - rotation) % (2 * math.pi)
                    if s > ARC:
                        continue
                    ends = min(1.0, s / cap, (ARC - s) / cap)
                    # Progressiv: Ansatz fast unsichtbar, Kopf voll hell
                    bright = 0.15 + 0.85 * (s / ARC) ** 1.4
                    cov += ring * ends * bright
            cov /= SUPER * SUPER
            if cov <= 0.0:
                continue
            offset = (y * SIZE + x) * 4
            pixels[offset : offset + 4] = bytes(COLOR) + bytes((round(min(1.0, cov) * 255),))
    return pixels


def render_frames(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("throbber-*.png"):
        old.unlink()
    for frame in range(FRAMES):
        write_png(output / f"throbber-{frame + 1:04d}.png", SIZE, SIZE,
                  frame_pixels(frame))


def render_preview(path: Path) -> None:
    """Acht Frames nebeneinander, 2× vergrößert, als Vorschau."""
    scale = 2
    shown = 8
    width, height = SIZE * scale * shown, SIZE * scale
    pixels = bytearray(width * height * 4)
    bg = bytes((0x0C, 0x17, 0x1B, 0xFF))
    for offset in range(0, len(pixels), 4):
        pixels[offset : offset + 4] = bg
    for i in range(shown):
        frame = round(i * FRAMES / shown) % FRAMES
        small = frame_pixels(frame)
        for y in range(SIZE * scale):
            for x in range(SIZE * scale):
                src = ((y // scale) * SIZE + (x // scale)) * 4
                dst = (y * width + i * SIZE * scale + x) * 4
                alpha = small[src + 3] / 255
                for c in range(3):
                    pixels[dst + c] = round(
                        small[src + c] * alpha + pixels[dst + c] * (1 - alpha))
                pixels[dst + 3] = 255
    write_png(path, width, height, pixels)


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--preview":
        render_preview(Path(sys.argv[2]))
    elif len(sys.argv) == 2:
        render_frames(Path(sys.argv[1]))
    else:
        raise SystemExit(
            "usage: make-boot-spinner.py OUTPUT_DIRECTORY\n"
            "       make-boot-spinner.py --preview FILE")


if __name__ == "__main__":
    main()
