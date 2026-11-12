"""Bevelled wooden hole rim — reads as a well lip, not a flat clover plate."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\art\hole_rim.png")
S = 280


def main() -> None:
    cx = cy = S // 2
    # Wider bevelled lip; large open centre for the mole
    outer, mid, inner = 132, 118, 100

    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)

    # Outer wood ring
    d.ellipse((cx - outer, cy - outer, cx + outer, cy + outer), fill=(168, 108, 64, 255))
    # Mid bevel (slightly darker)
    d.ellipse((cx - mid, cy - mid, cx + mid, cy + mid), fill=(128, 78, 44, 255))
    # Punch open centre
    d.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=(0, 0, 0, 0))

    a = np.array(base, dtype=np.int16)
    ys, xs = np.where(a[:, :, 3] > 0)
    rng = np.random.default_rng(7)
    for i in range(0, len(ys), 2):
        y, x = int(ys[i]), int(xs[i])
        n = int(rng.integers(-12, 13))
        a[y, x, 0] = int(np.clip(int(a[y, x, 0]) + n, 40, 255))
        a[y, x, 1] = int(np.clip(int(a[y, x, 1]) + n // 2, 28, 255))
        a[y, x, 2] = int(np.clip(int(a[y, x, 2]) + n // 3, 16, 255))
    ring = Image.fromarray(a.astype(np.uint8), "RGBA")

    # Inner drop-shadow (into the well)
    lip = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lip)
    ld.ellipse(
        (cx - inner - 2, cy - inner - 2, cx + inner + 2, cy + inner + 2),
        outline=(18, 8, 4, 220),
        width=6,
    )
    ld.ellipse(
        (cx - inner + 4, cy - inner + 6, cx + inner - 4, cy + inner - 2),
        outline=(8, 4, 2, 160),
        width=4,
    )
    lip = lip.filter(ImageFilter.GaussianBlur(1.4))

    # Outer soft contact shadow on the board
    outer_sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    od = ImageDraw.Draw(outer_sh)
    od.ellipse(
        (cx - outer - 3, cy - outer + 2, cx + outer + 3, cy + outer + 6),
        outline=(0, 0, 0, 90),
        width=5,
    )
    outer_sh = outer_sh.filter(ImageFilter.GaussianBlur(2.2))

    # Highlight on top of the bevel
    hi = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.arc(
        (cx - outer + 4, cy - outer + 4, cx + outer - 4, cy + outer - 4),
        start=200,
        end=340,
        fill=(230, 190, 140, 140),
        width=4,
    )
    hi = hi.filter(ImageFilter.GaussianBlur(1.0))

    # Rivets
    riv = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rv = ImageDraw.Draw(riv)
    riv_r = (mid + outer) / 2.0
    for ang in range(0, 360, 36):
        rad = np.deg2rad(ang)
        x = cx + riv_r * np.cos(rad)
        y = cy + riv_r * np.sin(rad)
        rv.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(62, 44, 30, 255))
        rv.ellipse((x - 1.6, y - 1.8, x + 1.4, y + 1.2), fill=(220, 195, 150, 230))

    out = Image.alpha_composite(outer_sh, ring)
    out = Image.alpha_composite(out, lip)
    out = Image.alpha_composite(out, hi)
    out = Image.alpha_composite(out, riv)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT)
    print("wrote", OUT, "inner", inner, "outer", outer)


if __name__ == "__main__":
    main()
