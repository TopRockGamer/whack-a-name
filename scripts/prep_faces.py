"""Tight circular face decals — face only, minimal neck/shirt (no light paddle)."""
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
    # Bias crop upward — keep crown/face, drop shirt collar (reads as paddle)
    h = y1 - y0 + 1
    # Keep face/crown only — neck/collar reads as a light "paddle" under the head
    y1 = y0 + int(h * 0.74)
    pad = 2
    crop = raw.crop((x0 + pad, y0 + pad, x1 + 1 - pad, y1 + 1))

    cw, ch = crop.size
    scale = min((SIZE * 0.94) / max(cw, 1), (SIZE * 0.94) / max(ch, 1))
    nw = max(1, int(round(cw * scale)))
    nh = max(1, int(round(ch * scale)))
    face = crop.resize((nw, nh), Image.Resampling.LANCZOS)

    paste_x = (SIZE - nw) // 2
    # Seat slightly high in the disc so chin isn't a light bar at the bottom
    paste_y = max(4, (SIZE - nh) // 2 - 8)

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

    # Soft fade only at the very bottom edge (don't bisect the face)
    yy = np.arange(SIZE).reshape(-1, 1)
    fade = np.clip((SIZE * 0.94 - yy) / (SIZE * 0.12), 0, 1)
    out[:, :, 3] = (out[:, :, 3].astype(np.float32) * fade).astype(np.uint8)

    return Image.fromarray(out, "RGBA")


def main() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    NO_HAT.mkdir(parents=True, exist_ok=True)
    FACES.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC.glob("face_*.png")):
        out = prep_one(src)
        out.save(BACKUP / src.name)
        out.save(NO_HAT / src.name)
        out.save(FACES / src.name)
        a = np.array(out)
        ys = np.where(a[:, :, 3] > 40)[0]
        print(f"{src.name}: y={ys.min()}..{ys.max()}")
    print("done")


if __name__ == "__main__":
    main()
