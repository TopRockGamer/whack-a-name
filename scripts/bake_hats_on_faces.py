"""Bake party hats onto faces with an unmistakable hair seat under the brim."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
FACES = ROOT / "public/assets/faces"
SRC = ROOT / "public/assets/faces_backup"
HAT = ROOT / "public/assets/art/party_hat.png"

HAIR_BAND = 48  # source px of visible crown under brim (~14px at 74px display)

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
    y0, y1 = int(h * 0.35), int(h * 0.70)
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
    return Image.fromarray(a, "RGBA")


def find_crown_y(arr: np.ndarray) -> int:
    h, w = arr.shape[:2]
    cx = w // 2
    for y in range(h):
        count = 0
        for x in range(cx - 35, cx + 36):
            r, g, b, al = (int(v) for v in arr[y, x])
            if al >= 100 and max(r, g, b) < 130:
                count += 1
        if count >= 14:
            return y
    return 20


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
            elif max(r, g, b) < 130:
                hair += 1
        if skin >= 10 and skin > hair:
            return y
    return 130


def sample_hair_color(arr: np.ndarray, y0: int, y1: int) -> tuple[int, int, int]:
    h, w = arr.shape[:2]
    cx = w // 2
    rs = gs = bs = n = 0
    for y in range(max(0, y0), min(h, y1)):
        for x in range(cx - 36, cx + 37):
            r, g, b, al = (int(v) for v in arr[y, x])
            if al < 120:
                continue
            if max(r, g, b) < 140:
                rs += r
                gs += g
                bs += b
                n += 1
    if n < 8:
        return 110, 82, 64
    # Lift far above void orange-black (~82,34,6) so crown reads at game scale
    return min(rs // n + 40, 140), min(gs // n + 32, 110), min(bs // n + 24, 88)


for src in sorted(SRC.glob("face_*.png")):
    face0 = Image.open(src).convert("RGBA")
    w, h = face0.size
    arr0 = np.array(face0)
    crown0 = find_crown_y(arr0)
    hairline = find_hairline(arr0)
    hr, hg, hb = sample_hair_color(arr0, crown0, hairline)
    ys, xs = np.where(arr0[:, :, 3] > 40)
    cx = float((xs.min() + xs.max()) / 2)
    content_w = int(xs.max() - xs.min() + 1)

    target_rim = hairline - HAIR_BAND
    target_rim = max(crown0 + 20, min(target_rim, hairline - 22))

    scale = (content_w * 0.36) / hat_src.width
    hat = None
    paste_x = paste_y = 0
    for _ in range(12):
        hw = max(1, int(round(hat_src.width * scale)))
        hh = max(1, int(round(hat_src.height * scale)))
        hat = clean_hat(
            hat_src.resize((hw, hh), Image.Resampling.LANCZOS).rotate(
                5, expand=True, resample=Image.Resampling.BICUBIC
            )
        )
        ha = np.array(hat)
        hys, hxs = np.where(ha[:, :, 3] > 40)
        brim_x = float((hxs.min() + hxs.max()) / 2)
        brim_y = float(hys.max())
        tip_y = float(hys.min())
        paste_x = int(round(cx - brim_x))
        paste_y = int(round(target_rim - brim_y))
        if paste_y + tip_y >= 3 and paste_y >= 1:
            break
        scale *= 0.90

    assert hat is not None

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(face0)
    canvas.alpha_composite(hat, (paste_x, max(1, paste_y)))
    shifted = np.array(canvas)

    # Find actual brim row
    brim_row = target_rim
    for y in range(min(h - 1, target_rim + 14), max(0, target_rim - 28), -1):
        hits = sum(
            1
            for x in range(max(0, int(cx) - 28), min(w, int(cx) + 29))
            if is_cone_stripe(*(int(v) for v in shifted[y, x]))
        )
        if hits >= 3:
            brim_row = y
            break

    cx_i = int(cx)
    rng = np.random.default_rng(abs(hash(src.name)) % (2**31))

    # Rounded crown dome under brim (NOT a flat wood-like bar).
    # Ellipse from brim down to hairline, tapering at the sides.
    seat_top = max(0, brim_row - 1)
    seat_bot = min(h - 1, hairline + 4)
    dome_h = max(8, seat_bot - seat_top)
    dome_w = content_w * 0.48
    for y in range(seat_top, seat_bot + 1):
        ty = (y - seat_top) / dome_h  # 0 at brim → 1 at hairline
        # width grows toward hairline (skull silhouette)
        half = dome_w * (0.85 + 0.20 * ty)
        for x in range(max(0, int(cx - half)), min(w, int(cx + half) + 1)):
            if (x - (w - 1) / 2) ** 2 + (y - (h - 1) / 2) ** 2 > (min(w, h) * 0.49) ** 2:
                continue
            # soft elliptical falloff at sides — keep center solid
            nx = abs(x - cx) / max(1.0, half)
            if nx > 0.98:
                continue
            r2, g2, b2, a2 = (int(v) for v in shifted[y, x])
            if y < brim_row and is_cone_stripe(r2, g2, b2, a2):
                continue
            if y > hairline + 2 and a2 > 160 and max(r2, g2, b2) > 160:
                continue
            strand = int(rng.integers(-22, 20))
            # radial highlight so it reads as hair volume, not a plank
            hi = int(28 * (1.0 - nx)) if (int(x * 2.3 + y) % 7 == 0) else 0
            rr = int(np.clip(hr + strand + hi, 40, 150))
            gg = int(np.clip(hg + strand // 2 + hi // 2, 30, 120))
            bb = int(np.clip(hb + strand // 3 + hi // 3, 22, 95))
            if y >= hairline - 2 and a2 > 100 and max(r2, g2, b2) > 140:
                t = 0.4
                rr = int(r2 * (1 - t) + rr * t)
                gg = int(g2 * (1 - t) + gg * t)
                bb = int(b2 * (1 - t) + bb * t)
            shifted[y, x] = (rr, gg, bb, 255)

    # Hair OVER the lower brim lip (8px) so seating is unmistakable at board scale
    for y in range(max(0, brim_row - 8), min(h, brim_row + 6)):
        for x in range(max(0, cx_i - 46), min(w, cx_i + 47)):
            nx = abs(x - cx) / max(1.0, dome_w * 0.9)
            if nx > 0.95:
                continue
            r2, g2, b2, a2 = (int(v) for v in shifted[y, x])
            # Keep upper cone stripes; only cover brim lip / just-below
            if y < brim_row - 3 and is_cone_stripe(r2, g2, b2, a2):
                continue
            strand = int(rng.integers(-14, 16))
            hi = 36 if (x + y * 2) % 6 == 0 else 0
            shifted[y, x] = (
                int(np.clip(hr - 8 + strand + hi, 35, 145)),
                int(np.clip(hg - 6 + strand // 2 + hi // 2, 26, 115)),
                int(np.clip(hb - 4 + strand // 3, 18, 90)),
                255,
            )

    # Fill hollow cone interior with hair so dark void doesn't read as a gap
    hat_top = max(2, paste_y + 4)
    for y in range(hat_top, brim_row):
        for x in range(max(0, cx_i - 28), min(w, cx_i + 29)):
            r2, g2, b2, a2 = (int(v) for v in shifted[y, x])
            if is_cone_stripe(r2, g2, b2, a2):
                continue
            # transparent / very dark through hollow
            if a2 > 200 and max(r2, g2, b2) > 70:
                continue
            strand = int(rng.integers(-12, 12))
            shifted[y, x] = (
                int(np.clip(hr + strand, 40, 140)),
                int(np.clip(hg + strand // 2, 30, 110)),
                int(np.clip(hb + strand // 3, 22, 88)),
                255,
            )

    # Cover pre-existing grey/blue caps under the party hat so crown reads as hair
    for y in range(max(0, brim_row - 4), min(h, hairline + 18)):
        for x in range(max(0, cx_i - 52), min(w, cx_i + 53)):
            if (x - (w - 1) / 2) ** 2 + (y - (h - 1) / 2) ** 2 > (min(w, h) * 0.49) ** 2:
                continue
            r2, g2, b2, a2 = (int(v) for v in shifted[y, x])
            if a2 < 80:
                continue
            if is_cone_stripe(r2, g2, b2, a2) and y < brim_row:
                continue
            # grey / blue fabric caps
            grey = abs(r2 - g2) < 25 and abs(g2 - b2) < 30 and 90 < r2 < 200
            blueish = b2 > r2 + 15 and b2 > g2 + 5 and b2 > 80
            if not (grey or blueish):
                continue
            if y > hairline + 10 and max(r2, g2, b2) > 170:
                continue
            strand = int(rng.integers(-16, 14))
            shifted[y, x] = (
                int(np.clip(hr + strand, 28, 115)),
                int(np.clip(hg + strand // 2, 20, 90)),
                int(np.clip(hb + strand // 3, 14, 75)),
                255,
            )

    yy, xx = np.mgrid[:h, :w]
    dist = np.sqrt((xx - (w - 1) / 2) ** 2 + (yy - (h - 1) / 2) ** 2)
    alpha = np.clip((min(w, h) * 0.495 + 0.5 - dist) * 255, 0, 255).astype(np.uint8)
    shifted[:, :, 3] = np.minimum(shifted[:, :, 3], alpha)

    Image.fromarray(shifted, "RGBA").save(FACES / src.name)
    print(
        f"{src.name}: crown0={crown0} hl={hairline} paste_y={paste_y} "
        f"brim_row={brim_row} hair_under={hairline - brim_row}"
    )

print("done")
