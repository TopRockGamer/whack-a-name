"""Prep tight circular face decals for mole-head textures (no hats).

Hats are a separate layer on the mole character stack in PlayScene.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SRC = Path(r"C:\Users\user\Downloads\Face_Pop_8_Separate_PNGs")
BACKUP = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\faces_backup")
NO_HAT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\faces_no_hat")
FACES = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\faces")
SIZE = 256


def strip_bg(im: Image.Image) -> Image.Image:
    a = np.array(im.convert("RGBA"))
    r, g, b, al = a[:, :, 0], a[:, :, 1], a[:, :, 2], a[:, :, 3]
    black = (r < 22) & (g < 22) & (b < 22)
    white = (r > 215) & (g > 215) & (b > 215)
    a[:, :, 3] = np.where(black | white, 0, al)
    return Image.fromarray(a, "RGBA")


def opaque_bbox(arr: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(arr[:, :, 3] > 40)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def erode_frame_ring_fast(im: Image.Image) -> Image.Image:
    a = np.array(im)
    opaque = a[:, :, 3] > 40
    up = np.zeros_like(opaque)
    down = np.zeros_like(opaque)
    left = np.zeros_like(opaque)
    right = np.zeros_like(opaque)
    up[1:] = opaque[:-1]
    down[:-1] = opaque[1:]
    left[:, 1:] = opaque[:, :-1]
    right[:, :-1] = opaque[:, 1:]
    edge = opaque & ~(up & down & left & right)
    dark = np.max(a[:, :, :3], axis=2) < 55
    a[edge & dark, 3] = 0
    return Image.fromarray(a, "RGBA")


def prep_one(src: Path) -> Image.Image:
    raw = erode_frame_ring_fast(strip_bg(Image.open(src)))
    arr0 = np.array(raw)
    x0, y0, x1, y1 = opaque_bbox(arr0)
    pad = 3
    crop = raw.crop((x0 + pad, y0 + pad, x1 + 1 - pad, y1 + 1 - pad))

    # Fill almost the full disc — face is a head decal on the mole body.
    cw, ch = crop.size
    scale = min((SIZE * 0.96) / max(cw, 1), (SIZE * 0.96) / max(ch, 1))
    nw = max(1, int(round(cw * scale)))
    nh = max(1, int(round(ch * scale)))
    face = crop.resize((nw, nh), Image.Resampling.LANCZOS)

    paste_x = (SIZE - nw) // 2
    paste_y = (SIZE - nh) // 2

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(face, (paste_x, paste_y))

    mask = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((2, 2, SIZE - 3, SIZE - 3), fill=255)

    out = np.array(canvas)
    m = np.array(mask)
    out[:, :, 3] = np.where(m > 127, out[:, :, 3], 0)
    keep = (m > 127) & (out[:, :, 3] > 40)
    out[keep, 3] = 255
    return Image.fromarray(out, "RGBA")


def main() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    NO_HAT.mkdir(parents=True, exist_ok=True)
    FACES.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC.glob("face_*.png")):
        out = prep_one(src)
        out.save(BACKUP / src.name)
        out.save(NO_HAT / src.name)
        # Game loads faces/ as head decals (hat is a separate rig layer).
        out.save(FACES / src.name)
        a = np.array(out)
        ys = np.where(a[:, :, 3] > 40)[0]
        print(f"{src.name}: y={ys.min()}..{ys.max()}")
    print("done")


if __name__ == "__main__":
    main()
