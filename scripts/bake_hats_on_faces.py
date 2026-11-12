"""Bake party hat onto REAL photo hair — one connected person.

Brim digs into opaque photo hair. Only plug transparent pixels that already
sit next to real hair (never invent a dome in empty circle space).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
FACES = ROOT / "public/assets/faces"
SRC = ROOT / "public/assets/faces_backup"
HAT = ROOT / "public/assets/art/party_hat.png"

RIM_INTO_HAIR = 28
HAT_WIDTH_FRAC = 0.70
MAX_HAT_H = 70

hat_src = Image.open(HAT).convert("RGBA")


def is_cone_stripe(r: int, g: int, b: int, al: int) -> bool:
    if al < 100:
        return False
    if r > 190 and g > 140 and b < 80 and (r - b) > 120:
        return True
    if 40 < r < 170 and g > 150 and b > 130 and g > r + 15 and (g + b) > 300:
        return True
    return False


def clean_hat(hat: Image.Image) -> Image.Image:
    a = np.array(hat)
    h, w = a.shape[:2]
    scores = [
        sum(1 for x in range(w) if is_cone_stripe(*(int(v) for v in a[y, x])))
        for y in range(h)
    ]
    y0, y1 = int(h * 0.32), int(h * 0.72)
    band = scores[y0:y1]
    if not band or max(band) < 8:
        rim = int(h * 0.58)
    else:
        peak = max(band)
        rim = y0
        for y in range(y1 - 1, y0 - 1, -1):
            if scores[y] >= peak * 0.45 and scores[y] >= 8:
                rim = y
                break
    a[rim + 1 :, :, 3] = 0
    for y in range(max(0, rim - 2), rim + 1):
        for x in range(w):
            r, g, b, al = (int(v) for v in a[y, x])
            if al > 40 and r > 200 and g > 200 and b > 170:
                a[y, x, 3] = 0
    ys, xs = np.where(a[:, :, 3] > 40)
    if len(ys) == 0:
        return Image.fromarray(a, "RGBA")
    return Image.fromarray(a[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1], "RGBA")


def find_crown_y(arr: np.ndarray) -> int:
    h, w = arr.shape[:2]
    cx = w // 2
    for y in range(h):
        count = sum(
            1
            for x in range(cx - 42, cx + 43)
            if (lambda p: p[3] >= 200 and max(p[0], p[1], p[2]) < 145)(
                tuple(int(v) for v in arr[y, x])
            )
        )
        if count >= 8:
            return y
    ys = np.where(arr[:, :, 3] > 40)[0]
    return int(ys.min()) if len(ys) else 48


def find_hairline(arr: np.ndarray) -> int:
    h, w = arr.shape[:2]
    cx = w // 2
    for y in range(h):
        skin = hair = 0
        for x in range(cx - 28, cx + 29):
            r, g, b, al = (int(v) for v in arr[y, x])
            if al < 100:
                continue
            if r > 160 and g > 110 and b > 90 and max(r, g, b) > 150:
                skin += 1
            elif max(r, g, b) < 145:
                hair += 1
        if skin >= 10 and skin > hair:
            return y
    return 120


def nearest_hair(arr: np.ndarray, x: int, y: int, crown: int, hairline: int):
    h, w = arr.shape[:2]
    best = None
    best_d = 9999
    y0 = max(0, crown)
    y1 = min(h, max(hairline, crown + 1))
    for yy in range(y0, y1):
        for xx in range(max(0, x - 40), min(w, x + 41)):
            r, g, b, al = (int(v) for v in arr[yy, xx])
            if al < 200 or max(r, g, b) > 140:
                continue
            d = (xx - x) * (xx - x) + (yy - y) * (yy - y)
            if d < best_d:
                best_d = d
                best = (r, g, b, 255)
    return best


for src in sorted(SRC.glob("face_*.png")):
    face0 = Image.open(src).convert("RGBA")
    w, h = face0.size
    arr0 = np.array(face0)
    crown0 = find_crown_y(arr0)
    hairline = max(find_hairline(arr0), crown0 + 18)
    ys, xs = np.where(arr0[:, :, 3] > 40)
    cx = float((xs.min() + xs.max()) / 2)
    content_w = int(xs.max() - xs.min() + 1)

    hair_span = max(1, hairline - crown0)
    target_rim = crown0 + min(RIM_INTO_HAIR, max(16, int(hair_span * 0.55)))
    target_rim = min(target_rim, hairline - 4)

    headroom = max(12, target_rim - 2)
    max_hat_h = min(MAX_HAT_H, headroom + 12)
    target_w = max(1, int(round(content_w * HAT_WIDTH_FRAC)))
    base = clean_hat(hat_src)
    bw, bh = base.size
    scale = min(target_w / bw, max_hat_h / bh)
    hw = max(1, int(round(bw * scale)))
    hh = max(1, int(round(bh * scale)))
    hat = base.resize((hw, hh), Image.Resampling.LANCZOS).rotate(
        3, expand=True, resample=Image.Resampling.BICUBIC
    )
    ha = np.array(hat)
    hys, hxs = np.where(ha[:, :, 3] > 40)
    hat = Image.fromarray(
        ha[hys.min() : hys.max() + 1, hxs.min() : hxs.max() + 1], "RGBA"
    )
    ha = np.array(hat)
    hys, hxs = np.where(ha[:, :, 3] > 40)
    brim_x = float((hxs.min() + hxs.max()) / 2)
    brim_y = float(hys.max())
    tip_y = float(hys.min())
    paste_x = int(round(cx - brim_x))
    paste_y = int(round(target_rim - brim_y))
    if paste_y + tip_y < 1:
        paste_y = int(1 - tip_y)
    paste_y = max(1, paste_y)

    # Plug ONLY transparent pixels that are adjacent to real opaque hair —
    # never paint a dome into empty circle space above the crown.
    plugged = np.array(face0)
    plug_r = int(hw * 0.34)
    for y in range(max(crown0, target_rim - 2), min(h, target_rim + 8)):
        for x in range(max(0, int(cx) - plug_r), min(w, int(cx) + plug_r + 1)):
            if plugged[y, x, 3] >= 200:
                continue
            # Must be near an existing opaque photo pixel
            near = False
            for oy in range(-2, 3):
                for ox in range(-2, 3):
                    yy, xx = y + oy, x + ox
                    if 0 <= yy < h and 0 <= xx < w and arr0[yy, xx, 3] >= 200:
                        near = True
                        break
                if near:
                    break
            if not near:
                continue
            pix = nearest_hair(arr0, x, y, crown0, hairline)
            if pix is None:
                continue
            plugged[y, x] = pix

    canvas = Image.fromarray(plugged, "RGBA")
    canvas.alpha_composite(hat, (paste_x, paste_y))
    shifted = np.array(canvas)

    brim_row = target_rim
    for y in range(min(h - 1, target_rim + 8), max(0, target_rim - 20), -1):
        hits = sum(
            1
            for x in range(max(0, int(cx) - 30), min(w, int(cx) + 31))
            if is_cone_stripe(*(int(v) for v in shifted[y, x]))
        )
        if hits >= 3:
            brim_row = y
            break

    # Real photo hair over brim lip
    cx_i = int(cx)
    for y in range(max(0, brim_row - 1), min(h, brim_row + 7)):
        for x in range(max(0, cx_i - 55), min(w, cx_i + 56)):
            r, g, b, al = (int(v) for v in arr0[y, x])
            if al < 200 or max(r, g, b) > 140:
                continue
            r2, g2, b2, a2 = (int(v) for v in shifted[y, x])
            if y < brim_row and is_cone_stripe(r2, g2, b2, a2):
                continue
            shifted[y, x] = (r, g, b, 255)

    Image.fromarray(shifted, "RGBA").save(FACES / src.name)
    print(
        f"{src.name}: crown0={crown0} hl={hairline} hat={hat.size} "
        f"paste_y={paste_y} brim_row={brim_row}"
    )

print("done")
