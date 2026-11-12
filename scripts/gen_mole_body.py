"""Creature mole body — dark furry shoulders + blank head dome for face decal."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\art\mole_body.png")
W, H = 300, 360


def shade(base, t):
    r, g, b = [float(c) for c in base]
    if t >= 0:
        t = min(1.0, t)
        return (
            int(r + (255 - r) * t * 0.28),
            int(g + (255 - g) * t * 0.28),
            int(b + (255 - b) * t * 0.28),
        )
    t = min(1.0, -t)
    return (int(r * (1 - 0.62 * t)), int(g * (1 - 0.62 * t)), int(b * (1 - 0.62 * t)))


def stamp(canvas, cx, cy, rx, ry, color, strength=1.0, lit=(-0.4, -0.35)):
    y0, y1 = max(0, int(cy - ry - 2)), min(H, int(cy + ry + 3))
    x0, x1 = max(0, int(cx - rx - 2)), min(W, int(cx + rx + 3))
    lx, ly = lit
    for y in range(y0, y1):
        for x in range(x0, x1):
            u = (x - cx) / rx
            v = (y - cy) / ry
            d2 = u * u + v * v
            if d2 >= 1.0:
                continue
            fall = (1.0 - d2) ** 1.25
            z = np.sqrt(max(0.0, 1.0 - d2))
            lit_amt = 0.2 + 0.8 * max(0.0, lx * (-u) + ly * (-v) + 0.48 * z)
            if v > 0.35:
                lit_amt *= 0.7
            col = shade(color, lit_amt - 0.55)
            # fur flecks
            n = ((x * 17 + y * 29) % 9) - 4
            if ((x * 5 + y * 3) % 11) == 0:
                n -= 10
            col = tuple(int(np.clip(c + n, 0, 255)) for c in col)
            a = strength * fall
            if a < 0.03:
                continue
            pr, pg, pb, pa = [float(v) for v in canvas[y, x]]
            out_a = min(1.0, pa / 255.0 + a * (1.0 - pa / 255.0))
            t = min(1.0, a * 1.2)
            canvas[y, x, 0] = int(pr * (1 - t) + col[0] * t)
            canvas[y, x, 1] = int(pg * (1 - t) + col[1] * t)
            canvas[y, x, 2] = int(pb * (1 - t) + col[2] * t)
            canvas[y, x, 3] = int(255 * out_a)


def main() -> None:
    canvas = np.zeros((H, W, 4), dtype=np.float32)
    cx = W / 2.0

    # DARK chocolate fur — never beige paddle
    fur = (86, 52, 32)
    fur_hi = (118, 78, 50)
    fur_lo = (42, 26, 16)
    fur_mid = (96, 60, 38)

    # Wide creature torso / belly (dark)
    stamp(canvas, cx, 275, 128, 88, fur_lo, 1.0, lit=(-0.2, -0.55))
    stamp(canvas, cx, 250, 118, 78, fur, 1.0, lit=(-0.3, -0.45))

    # Big rounded shoulders (reads as arms/creature, not peg)
    stamp(canvas, cx - 95, 240, 58, 62, fur_mid, 1.0, lit=(-0.6, -0.2))
    stamp(canvas, cx + 95, 240, 58, 62, fur_mid, 1.0, lit=(-0.15, -0.2))
    # Shoulder tops highlight
    stamp(canvas, cx - 88, 220, 40, 28, shade(fur_hi, -0.05), 0.7, lit=(-0.5, -0.6))
    stamp(canvas, cx + 88, 220, 40, 28, shade(fur_hi, -0.05), 0.7, lit=(-0.2, -0.6))

    # Folded paws
    stamp(canvas, cx - 40, 295, 24, 16, shade(fur, -0.15), 0.95)
    stamp(canvas, cx + 40, 295, 24, 16, shade(fur, -0.15), 0.95)

    # Neck
    stamp(canvas, cx, 188, 72, 40, fur, 1.0, lit=(-0.35, -0.35))

    # Blank fur HEAD dome
    head_cy, head_rx, head_ry = 122.0, 112.0, 108.0
    stamp(canvas, cx, head_cy, head_rx, head_ry, fur_hi, 1.0, lit=(-0.48, -0.4))
    # Cheek fluff outside head (creature silhouette)
    stamp(canvas, cx - 88, head_cy + 36, 40, 40, fur, 0.9, lit=(-0.55, -0.1))
    stamp(canvas, cx + 88, head_cy + 36, 40, 40, fur, 0.9, lit=(-0.15, -0.1))
    # Soft crown
    stamp(canvas, cx - 14, head_cy - 34, 40, 30, shade(fur_hi, 0.15), 0.5, lit=(-0.2, -0.7))

    a = canvas.copy()
    solid = a[:, :, 3] > 35
    a[solid, 3] = 255

    # Crush any light pixels to dark fur
    rgb = a[:, :, :3]
    light = (rgb[:, :, 0] > 140) & solid
    for i, t in enumerate(fur_lo):
        a[light, i] = a[light, i] * 0.35 + t * 0.65

    img = Image.fromarray(a.astype(np.uint8), "RGBA")

    # Soft bottom fringe only
    arr = np.array(img)
    for i in range(20):
        y = H - 20 + i
        arr[y, :, 3] = (arr[y, :, 3].astype(np.float32) * (1.0 - i / 20.0 * 0.7)).astype(
            np.uint8
        )
    keep = arr[:, :, 3] > 180
    arr[keep, 3] = 255
    img = Image.fromarray(arr, "RGBA")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    prev = Image.new("RGB", (W, H), (18, 10, 6))
    prev.paste(img, (0, 0), img)
    prev.save(Path(r"C:\Users\user\Documents\whack-a-name\_mole_body_preview.png"))
    print("wrote", OUT, img.size)


if __name__ == "__main__":
    main()
