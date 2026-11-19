#!/usr/bin/env python3
"""Build the browser version of Valley Life.

The browser game (web/template.html) is the same game written in JavaScript. To make both versions look and
play identically, this script takes the world (tiles, trees, rocks), the pre-rendered map and every sprite from
the Python game, packs the sprites into one image atlas, and embeds all of it into the page.

    pip install pygame pillow
    python build_web.py                 # writes valley_life_web.html
    python build_web.py extra_out.html  # also writes a copy without the <html> wrapper (for hosting as an Artifact)
"""
import base64
import io
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

import valley_life as V  # noqa: E402


def to_pil(surf):
    return Image.frombytes("RGBA", surf.get_size(), pygame.image.tobytes(surf, "RGBA"))


def pack(sprites, width=2048):
    """Simple shelf packer: tallest sprites first, left to right, top to bottom."""
    items = sorted(sprites.items(), key=lambda kv: (-kv[1][0].get_height(), kv[0]))
    x = y = row_h = 0
    frames, placed = {}, []
    for name, (surf, ax, ay) in items:
        w, h = surf.get_size()
        if x + w > width:
            x, y, row_h = 0, y + row_h + 1, 0
        frames[name] = [x, y, w, h, round(ax, 2), round(ay, 2)]
        placed.append((surf, x, y))
        x += w + 1
        row_h = max(row_h, h)
    atlas = Image.new("RGBA", (width, y + row_h), (0, 0, 0, 0))
    for surf, px, py in placed:
        atlas.paste(to_pil(surf), (px, py))
    return atlas, frames


def b64(img, fmt, **kw):
    buf = io.BytesIO()
    img.save(buf, fmt, **kw)
    return base64.b64encode(buf.getvalue()).decode()


def main(extra_out=None):
    V.SAVE_FILE = os.devnull
    game = V.Game()
    atlas, frames = pack(game.spr)
    zone_letter = {"river": "r", "lake": "l", "deep": "d", "cave": "c"}
    world = {
        "tiles": "".join(str(v) for row in game.tiles for v in row),
        "zones": "".join(zone_letter.get(game.zone.get((x, y)), "-") for y in range(V.MH) for x in range(V.MW)),
        "trees": [[t["x"], t["y"], t["t"]] for t in game.trees],
        "ores": [[o["x"], o["y"], o["o"]] for o in game.ores],
    }
    with open(os.path.join(HERE, "web", "template.html"), encoding="utf-8") as fh:
        page = fh.read()
    for marker, value in (
        ('"__ATLAS__"', '"data:image/png;base64,' + b64(atlas, "PNG", optimize=True) + '"'),
        ('"__MAP__"', '"data:image/webp;base64,' + b64(to_pil(game.map_surf).convert("RGB"), "WEBP", quality=82) + '"'),
        ("/*__FRAMES__*/null", json.dumps(frames, separators=(",", ":"))),
        ("/*__WORLD__*/null", json.dumps(world, separators=(",", ":"))),
    ):
        assert marker in page, f"missing {marker} in template"
        page = page.replace(marker, value)
    full = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head>'
            '<body style="margin:0">\n' + page + "\n</body></html>\n")
    with open(os.path.join(HERE, "valley_life_web.html"), "w", encoding="utf-8") as fh:
        fh.write(full)
    if extra_out:
        with open(extra_out, "w", encoding="utf-8") as fh:
            fh.write(page)
    print(f"atlas {atlas.size[0]}x{atlas.size[1]}, {len(frames)} sprites, page {len(full) / 1e6:.2f} MB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
