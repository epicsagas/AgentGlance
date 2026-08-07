#!/usr/bin/env python3
"""One-time generator for the bundled per-host placeholder GIFs.

Produces neutral animated placeholders in assets/hosts/<host>.gif so that gif
mode (preset `hosts`) works out of the box. Users replace these by dropping
their own <host>.gif into ~/.agent-glance/gifs/hosts/.

Re-run any time; output is committed. agent_glance.py never imports this.

  python3 scripts/gen_host_placeholders.py
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

# label -> (monogram, accent color). Colors are distinct per host, neutral
# (no state) so they read the same in working/waiting/done.
HOSTS = {
    "claude code": ("CC", (255, 180, 80)),    # amber
    "codex":       ("CX", (100, 200, 255)),   # cyan
    "antigravity": ("AG", (180, 130, 255)),   # purple
    "hermes":      ("HE", (255, 130, 180)),   # pink
    "agent":       ("AG", (220, 220, 220)),   # neutral
}
SIZE = 120
FRAMES = 12
MS = 100
OUT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "hosts"))


def _font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for host, (mono, color) in HOSTS.items():
        frames = []
        for i in range(FRAMES):
            img = Image.new("RGB", (SIZE, SIZE), (20, 20, 20))
            d = ImageDraw.Draw(img)
            t = i / FRAMES
            # pulsing filled disc + a wider faint ring
            r = 30 + 8 * math.sin(t * 2 * math.pi)
            d.ellipse([SIZE/2 - r, SIZE/2 - r, SIZE/2 + r, SIZE/2 + r], fill=color)
            ring = r + 8
            d.ellipse([SIZE/2 - ring, SIZE/2 - ring, SIZE/2 + ring, SIZE/2 + ring],
                      outline=color, width=2)
            d.text((SIZE/2, SIZE/2), mono, font=_font(34), fill=(20, 20, 20), anchor="mm")
            frames.append(img)
        stem = host.replace(" ", "-").lower()
        out = os.path.join(OUT_DIR, stem + ".gif")
        frames[0].save(out, "GIF", save_all=True, append_images=frames[1:],
                       loop=0, duration=[MS] * FRAMES, disposal=2)
        print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
