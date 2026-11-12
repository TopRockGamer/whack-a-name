"""Prep circular heads: dense hat-ready crown, face fills the circle."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = Path(r"C:\Users\user\Downloads\Face_Pop_8_Separate_PNGs")
BACKUP = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\faces_backup")
NO_HAT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\faces_no_hat")
SIZE = 256

# Dense layout: crown top → hairline → face → chin packs the circle
HAIRLINE_FRAC = 0.48
CROWN_FRAC = 0.30


def strip_bg(im: Image.Image) -> Image.Image:
    a = np.array(im.convert("RGBA"))
    r, g, b, al = a[:, :, 0], a[:, :, 1], a[:, :, 2], a[:, :, 3]
    black = (r < 28) & (g < 28) & (b < 28)
    white = (r > 210) & (g > 210) & (b > 210)
    a[:, :, 3] = np.where(black | white, 0, al)
    return Image.fromarray(a, "RGBA")


def opaque_bbox(arr: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(arr[:, :, 3] > 40)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def hairline_y(arr: np.ndarray) -> int:
    h, w = arr.shape[:2]
    cx = w // 2
    for y in range(h):
        hits = 0
        for x in range(max(0, cx - 45), min(w, cx + 46)):
            r, g, b, al = (int(v) for v in arr[y, x])
            if al < 90 or (r > 200 and g > 200 and b > 200):
                continue
            hits += 1
        if hits >= 14:
            return y
    return 16


def sample_hair(arr: np.ndarray, y0: int, y1: int) -> tuple[int, int, int]:
    h, w = arr.shape[:2]
    cx = w // 2
    rs = gs = bs = n = 0
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, cx - 40), min(w, cx + 41)):
            r, g, b, al = (int(v) for v in arr[y, x])
            if al < 120:
                continue
            if max(r, g, b) < 150:
                rs += r
                gs += g
                bs += b
                n += 1
    if n < 6:
        return 68, 48, 40
    # Distinct from void orange-black; readable at ~60px display
    return min(rs // n + 18, 105), min(gs // n + 12, 82), min(bs // n + 10, 72)


def prep_one(src: Path) -> Image.Image:
    raw = strip_bg(Image.open(src))
    arr0 = np.array(raw)
    x0, y0, x1, y1 = opaque_bbox(arr0)
    crop = raw.crop((x0, y0, x1 + 1, y1 + 1))
    ca = np.array(crop)
    solid = ca.copy()
    opaque = solid[:, :, 3] > 40
    solid[opaque, 3] = 255
    solid[~opaque, 3] = 0
    crop = Image.fromarray(solid, "RGBA")

    # Large face in circle — chin near bottom, room for crown above
    max_w = int(SIZE * 0.92)
    max_h = int(SIZE * 0.62)
    cw, ch = crop.size
    scale = min(max_w / cw, max_h / ch)
    nw = max(1, int(round(cw * scale)))
    nh = max(1, int(round(ch * scale)))
    face = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    fa = np.array(face)
    hl = hairline_y(fa)
    hr, hg, hb = sample_hair(fa, hl, min(nh, hl + 30))

    paste_x = (SIZE - nw) // 2
    paste_y = int(SIZE * HAIRLINE_FRAC) - hl
    paste_y = max(0, min(paste_y, SIZE - nh))
    paste_x = max(0, min(paste_x, SIZE - nw))

    canvas = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    canvas[paste_y : paste_y + nh, paste_x : paste_x + nw] = fa
    hair_abs = paste_y + hl

    cx = (SIZE - 1) / 2.0
    cy = (SIZE - 1) / 2.0
    rad = SIZE * 0.49
    rng = np.random.default_rng(abs(hash(src.name)) % (2**31))

    crown_top = max(6, int(hair_abs - SIZE * CROWN_FRAC))
    # Radial hair strands (reads as hair, not void noise)
    for y in range(crown_top, min(SIZE, hair_abs + 14)):
        for x in range(SIZE):
            dx = (x - cx) / rad
            dy = (y - cy) / rad
            if dx * dx + dy * dy > 1.0:
                continue
            r0, g0, b0, a0 = (int(v) for v in canvas[y, x])
            if y > hair_abs + 4 and a0 > 140 and max(r0, g0, b0) > 145:
                continue
            crown_t = (hair_abs - y) / max(1.0, hair_abs - crown_top)
            if crown_t > 0.88 and abs(dx) > 0.58:
                continue
            # Strand direction: vertical-ish with slight radial sweep
            strand = int(18 * np.sin((x * 0.35 + y * 0.15) + rng.random()))
            hi = 35 if int(x + y * 2) % 11 == 0 else 0
            rr = int(np.clip(hr + strand + hi, 22, 120))
            gg = int(np.clip(hg + strand // 2 + hi // 2, 16, 95))
            bb = int(np.clip(hb + strand // 3, 12, 85))
            if a0 < 90 or y < hair_abs:
                canvas[y, x] = (rr, gg, bb, 255)
            elif y <= hair_abs + 10 and max(r0, g0, b0) < 170:
                t = 0.65 if y <= hair_abs else 0.35
                canvas[y, x, 0] = int(r0 * (1 - t) + rr * t)
                canvas[y, x, 1] = int(g0 * (1 - t) + gg * t)
                canvas[y, x, 2] = int(b0 * (1 - t) + bb * t)
                canvas[y, x, 3] = 255

    mask = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((1, 1, SIZE - 2, SIZE - 2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    canvas[:, :, 3] = np.minimum(canvas[:, :, 3], np.array(mask))
    return Image.fromarray(canvas, "RGBA")


def main() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    NO_HAT.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC.glob("face_*.png")):
        out = prep_one(src)
        out.save(BACKUP / src.name)
        out.save(NO_HAT / src.name)
        a = np.array(out)
        ys = np.where(a[:, :, 3] > 40)[0]
        cx = SIZE // 2
        skin_y = SIZE
        for y in range(SIZE):
            r, g, b, al = (int(v) for v in a[y, cx])
            if al > 150 and r > 160 and g > 110 and b > 90:
                skin_y = y
                break
        print(
            f"{src.name}: y={ys.min()}..{ys.max()} skin@{skin_y} "
            f"crown_px={skin_y - int(ys.min())}"
        )
    print("done")


if __name__ == "__main__":
    main()
