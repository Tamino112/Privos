#!/usr/bin/env python3
"""Create a quiet, horizontal Plymouth loading animation without dependencies."""

import math
import struct
import sys
import zlib
from pathlib import Path


WIDTH = 128
HEIGHT = 8
FRAMES = 32
TRACK_START = 4
TRACK_END = WIDTH - 4
SEGMENT_WIDTH = 34
TRACK_COLOR = (48, 74, 80)
ACCENT_COLOR = (200, 228, 231)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(
        ">I", zlib.crc32(kind + data) & 0xFFFFFFFF
    )


def write_png(path: Path, pixels: bytearray) -> None:
    rows = b"".join(
        b"\x00" + pixels[y * WIDTH * 4 : (y + 1) * WIDTH * 4]
        for y in range(HEIGHT)
    )
    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(rows, 9))
        + png_chunk(b"IEND", b"")
    )


def render_frame(frame: int) -> bytearray:
    """Move one short highlight back and forth over a static rounded track."""
    pixels = bytearray(WIDTH * HEIGHT * 4)
    phase = frame / FRAMES
    position = (1 - math.cos(2 * math.pi * phase)) / 2
    segment_start = TRACK_START + (TRACK_END - TRACK_START - SEGMENT_WIDTH) * position
    segment_end = segment_start + SEGMENT_WIDTH

    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Four subpixels per axis keep the two-pixel line crisp at 1:1 size.
            coverage = 0
            for sy in (0.125, 0.375, 0.625, 0.875):
                for sx in (0.125, 0.375, 0.625, 0.875):
                    px = x + sx
                    py = y + sy
                    nearest_x = min(max(px, TRACK_START + 1), TRACK_END - 1)
                    coverage += (px - nearest_x) ** 2 + (py - HEIGHT / 2) ** 2 <= 1.25**2
            if not coverage:
                continue

            # A small feather at either end makes the motion feel continuous.
            highlight = min(
                1.0,
                max(0.0, (x + 0.5 - segment_start) / 4),
                max(0.0, (segment_end - x - 0.5) / 4),
            )
            offset = (y * WIDTH + x) * 4
            pixels[offset : offset + 4] = bytes(
                round(base * (1 - highlight) + accent * highlight)
                for base, accent in zip(TRACK_COLOR, ACCENT_COLOR)
            ) + bytes((round(coverage / 16 * (145 + 110 * highlight)),))

    return pixels


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make-boot-progress.py OUTPUT_DIRECTORY")
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    for frame in range(FRAMES):
        write_png(output / f"throbber-{frame + 1:04d}.png", render_frame(frame))


if __name__ == "__main__":
    main()
