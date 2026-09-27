#!/usr/bin/env python3
"""Create the small Privos Plymouth throbber without image dependencies."""

import math
import struct
import sys
import zlib
from pathlib import Path


SIZE = 48
DOTS = 12
RING_RADIUS = 15
DOT_RADIUS = 2.5
COLOR = (169, 156, 247)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(
        ">I", zlib.crc32(kind + data) & 0xFFFFFFFF
    )


def write_png(path: Path, pixels: bytearray) -> None:
    rows = b"".join(
        b"\x00" + pixels[y * SIZE * 4 : (y + 1) * SIZE * 4]
        for y in range(SIZE)
    )
    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(rows, 9))
        + png_chunk(b"IEND", b"")
    )


def render_frame(active: int) -> bytearray:
    pixels = bytearray(SIZE * SIZE * 4)
    for dot in range(DOTS):
        angle = 2 * math.pi * dot / DOTS - math.pi / 2
        cx = SIZE / 2 + math.cos(angle) * RING_RADIUS
        cy = SIZE / 2 + math.sin(angle) * RING_RADIUS
        age = (active - dot) % DOTS
        opacity = 0.14 + 0.86 * ((DOTS - age) / DOTS) ** 2
        for y in range(max(0, math.floor(cy - 3)), min(SIZE, math.ceil(cy + 3))):
            for x in range(max(0, math.floor(cx - 3)), min(SIZE, math.ceil(cx + 3))):
                coverage = sum(
                    (x + sx - cx) ** 2 + (y + sy - cy) ** 2 <= DOT_RADIUS**2
                    for sy in (0.125, 0.375, 0.625, 0.875)
                    for sx in (0.125, 0.375, 0.625, 0.875)
                ) / 16
                if coverage:
                    offset = (y * SIZE + x) * 4
                    pixels[offset : offset + 4] = bytes(
                        (*COLOR, round(255 * opacity * coverage))
                    )
    return pixels


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make-boot-spinner.py OUTPUT_DIRECTORY")
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    for frame in range(DOTS):
        write_png(output / f"throbber-{frame + 1:04d}.png", render_frame(frame))


if __name__ == "__main__":
    main()
