"""Board lid: opaque wood cover with elliptical holes punched out.

Drawn ABOVE moles so any character that escapes a geometry mask is still
hidden by the lid — moles can only be seen through the wells.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
BACKDROP = ROOT / "public" / "assets" / "art" / "backdrop.png"
OUT = ROOT / "public" / "assets" / "art" / "board_lid.png"

# Must match src/config.ts HOLES + HOLE_MASK (base sizes before hole.scale)
HOLES = [
    (521, 410, 0.78, "back"),
    (822, 410, 0.76, "back"),
    (1125, 410, 0.78, "back"),
    (475, 493, 0.95, "front"),
    (821, 493, 1.0, "front"),
    (1161, 493, 0.95, "front"),
]
# Punch must clear the rim OUTER size so the lip isn't covered by the lid
RIM = {"back": 148, "front": 186}
MASK = {"back": (108, 92), "front": (136, 128)}

W, H = 1280, 720


def main() -> None:
    bg = Image.open(BACKDROP).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    # Sample wood colour from board region
    sample = np.array(bg.crop((400, 380, 900, 560)))
    wood = tuple(int(c) for c in sample.mean(axis=(0, 1)))

    lid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Cover the table band (where moles could spill)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    # Soft wood plate over the hole row area
    # Cover the whole lower playfield incl. under the table (hide rising moles)
    bd.rectangle((0, 300, W, H), fill=(*wood, 255))
    bg_rgba = bg.convert("RGBA")
    band_arr = np.array(band)
    bg_arr = np.array(bg_rgba)
    mask_band = band_arr[:, :, 3] > 0
    out = np.zeros((H, W, 4), dtype=np.uint8)
    # Prefer backdrop pixels where they exist; solid wood fill under the table skirt
    out[mask_band, :3] = bg_arr[mask_band, :3]
    out[mask_band, 3] = 255
    # Below the painted board (~y 600+): keep opaque wood so moles can't show under the table
    under = np.zeros((H, W), dtype=bool)
    under[600:, :] = True
    out[under, 0] = wood[0]
    out[under, 1] = wood[1]
    out[under, 2] = wood[2]
    out[under, 3] = 255
    # Also copy backdrop for mid band
    mid = mask_band & (np.arange(H)[:, None] < 600)
    out[mid, :3] = bg_arr[mid, :3]
    lid = Image.fromarray(out, "RGBA")

    # Punch holes (slightly smaller than rim, match play mask)
    punch = Image.new("L", (W, H), 0)
    pd = ImageDraw.Draw(punch)
    for x, y, scale, row in HOLES:
        # Elliptical well opening ≈ mask, but punch radius must clear the rim ring
        rim = RIM[row] * scale
        mw, mh = MASK[row]
        mw = max(mw * scale, rim * 0.92)
        mh = max(mh * scale, rim * 0.82)
        pad = 4
        pd.ellipse(
            (x - mw / 2 - pad, y - mh / 2 - pad, x + mw / 2 + pad, y + mh / 2 + pad),
            fill=255,
        )
    # Soften punch edge
    punch = punch.filter(ImageFilter.GaussianBlur(0.6))
    la = np.array(lid)
    p = np.asarray(punch).astype(np.float32) / 255.0
    la[:, :, 3] = (la[:, :, 3].astype(np.float32) * (1.0 - p)).astype(np.uint8)
    lid = Image.fromarray(la, "RGBA")

    # Soften only the TOP edge of the lid into the backdrop
    fade = Image.new("L", (W, H), 255)
    fd = ImageDraw.Draw(fade)
    fd.rectangle((0, 300, W, 340), fill=0)
    fade = fade.filter(ImageFilter.GaussianBlur(14))
    la = np.array(lid)
    f = np.asarray(fade).astype(np.float32) / 255.0
    # Only feather alpha near the top; keep bottom fully solid
    top_zone = np.arange(H)[:, None] < 360
    la[:, :, 3] = np.where(
        top_zone,
        (la[:, :, 3].astype(np.float32) * f).astype(np.uint8),
        la[:, :, 3],
    )
    # Punch holes last (always transparent)
    la[np.asarray(punch) > 128, 3] = 0
    # Ensure under-table stays solid
    la[600:, :, 3] = np.where(np.asarray(punch)[600:] > 128, 0, 255)
    lid = Image.fromarray(la, "RGBA")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lid.save(OUT)
    prev = Image.alpha_composite(bg.convert("RGBA"), lid)
    prev.save(ROOT / "_board_lid_preview.png")
    print("wrote", OUT, "wood", wood)


if __name__ == "__main__":
    main()
