"""Full-viewport board lid with only hole wells punched out.

Moles can only be seen through the elliptical punches — no spill onto wood
or into the sky above the holes.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
BACKDROP = ROOT / "public" / "assets" / "art" / "backdrop.png"
OUT = ROOT / "public" / "assets" / "art" / "board_lid.png"

HOLES = [
    (521, 410, 0.78, "back"),
    (822, 410, 0.76, "back"),
    (1125, 410, 0.78, "back"),
    (475, 493, 0.95, "front"),
    (821, 493, 1.0, "front"),
    (1161, 493, 0.95, "front"),
]
RIM = {"back": 196, "front": 248}
MASK = {"back": (150, 132), "front": (190, 176)}

W, H = 1280, 720


def main() -> None:
    bg = Image.open(BACKDROP).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    bg_arr = np.array(bg)

    # Start fully opaque using backdrop pixels (hides anything behind the lid)
    lid = bg_arr.copy()
    lid[:, :, 3] = 255

    # Soften: above the board, keep lid but we'll punch holes; sky stays as backdrop copy
    # so the scene looks unchanged — moles simply can't draw through it.

    punch = Image.new("L", (W, H), 0)
    pd = ImageDraw.Draw(punch)
    for x, y, scale, row in HOLES:
        rim = RIM[row] * scale
        mw, mh = MASK[row]
        # Punch clears the rim outer so the rim sprite (in hole bucket) is visible
        mw = max(mw * scale, rim * 0.95)
        mh = max(mh * scale, rim * 0.88)
        pad = 3
        pd.ellipse(
            (x - mw / 2 - pad, y - mh / 2 - pad, x + mw / 2 + pad, y + mh / 2 + pad),
            fill=255,
        )
    punch = punch.filter(ImageFilter.GaussianBlur(0.5))
    p = np.asarray(punch)

    # Transparent only inside punches
    lid[p > 128, 3] = 0

    out = Image.fromarray(lid, "RGBA")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT)

    # Preview
    prev = Image.alpha_composite(bg, out)
    prev.save(ROOT / "_board_lid_preview.png")
    print("wrote", OUT, "opaque", int((lid[:, :, 3] == 255).sum()), "punched", int((p > 128).sum()))


if __name__ == "__main__":
    main()
