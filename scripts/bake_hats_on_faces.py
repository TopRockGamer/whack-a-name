"""Bake party hats onto faces with hair overlapping the brim (no float gap).

Steps:
1. Crop hollow open-brim junk off party_hat.png
2. Shift face so crown sits at TARGET_CROWN
3. Paste hat with stripe rim at crown + RIM_INTO_HAIR
4. Re-stamp original crown hair ON TOP of the brim so strands cover any gap
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
FACES = ROOT / "public/assets/faces"
SRC = ROOT / "public/assets/faces_backup"
HAT = ROOT / "public/assets/art/party_hat.png"

TARGET_CROWN = 108
RIM_INTO_HAIR = 26  # nest into hair; keep above ROSS/forehead

hat_src = Image.open(HAT).convert("RGBA")


def is_cone_stripe(r: int, g: int, b: int, al: int) -> bool:
    if al < 100:
        return False
    # saturated gold (exclude skin: skin has higher b relative to chroma)
    if r > 190 and g > 140 and b < 80 and (r - b) > 120:
        return True
    if 40 < r < 170 and g > 150 and b > 130 and g > r + 15 and (g + b) > 300:
        return True
    return False


def clean_hat(hat: Image.Image) -> Image.Image:
    a = np.array(hat)
    h, w = a.shape[:2]
    scores = []
    for y in range(h):
        n = 0
        for x in range(w):
            r, g, b, al = (int(v) for v in a[y, x])
            if is_cone_stripe(r, g, b, al):
                n += 1
        scores.append(n)
    y0 = int(h * 0.35)
    y1 = int(h * 0.70)
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
    # Kill bright cutout fringe on the brim row (reads as float gap)
    for y in range(max(0, rim - 2), rim + 1):
        for x in range(w):
            r, g, b, al = (int(v) for v in a[y, x])
            if al < 40:
                continue
            if r > 220 and g > 220 and b > 200:
                a[y, x, 3] = 0
            # darken near-white fringe toward teal so edge isn't a halo
            elif r > 200 and g > 200 and b > 170 and al < 220:
                a[y, x, 3] = 0
    return Image.fromarray(a, "RGBA")


def find_crown_y(arr: np.ndarray) -> int:
    h, w = arr.shape[:2]
    cx = w // 2
    best_y = None
    for y in range(h):
        count = 0
        for x in range(cx - 40, cx + 41):
            aa = int(arr[y, x, 3])
            if aa < 100:
                continue
            r, g, b = int(arr[y, x, 0]), int(arr[y, x, 1]), int(arr[y, x, 2])
            if r > 215 and g > 215 and b > 215:
                continue
            if r + g + b < 50:
                continue
            count += 1
        if count >= 12:
            return y
        if count >= 6 and best_y is None:
            best_y = y
    return best_y if best_y is not None else 24


def hair_mask(arr: np.ndarray, y0: int, y1: int) -> np.ndarray:
    """Alpha mask of dark hair pixels in [y0, y1)."""
    h, w = arr.shape[:2]
    out = np.zeros((h, w), dtype=np.uint8)
    y0 = max(0, y0)
    y1 = min(h, y1)
    for y in range(y0, y1):
        for x in range(w):
            r, g, b, al = (int(v) for v in arr[y, x])
            if al < 120:
                continue
            if r > 210 and g > 210 and b > 210:
                continue
            # dark hair / brow
            if max(r, g, b) < 130 and r + g + b < 280:
                out[y, x] = al
            # medium brown hair
            elif r < 120 and g < 100 and b < 95 and al > 160:
                out[y, x] = al
    return out


cleaned = clean_hat(hat_src)
cleaned.save(ROOT / "_hat_cleaned.png")


for src in sorted(SRC.glob("face_*.png")):
    face0 = Image.open(src).convert("RGBA")
    w, h = face0.size
    arr0 = np.array(face0)
    crown0 = find_crown_y(arr0)
    aa = arr0[:, :, 3]
    ys, xs = np.where(aa > 40)
    content_w = int(xs.max() - xs.min() + 1)
    cx = (xs.min() + xs.max()) / 2.0

    scale = (content_w * 0.50) / hat_src.width
    target_rim = TARGET_CROWN + RIM_INTO_HAIR

    hat = None
    paste_x = 0
    paste_y = 0
    for _ in range(8):
        hw = max(1, int(round(hat_src.width * scale)))
        hh = max(1, int(round(hat_src.height * scale)))
        hat = clean_hat(
            hat_src.resize((hw, hh), Image.Resampling.LANCZOS).rotate(
                8, expand=True, resample=Image.Resampling.BICUBIC
            )
        )
        ha = np.array(hat)
        hys, hxs = np.where(ha[:, :, 3] > 40)
        brim_x = float((hxs.min() + hxs.max()) / 2)
        brim_y = float(hys.max())
        paste_x = int(round(cx - brim_x))
        paste_y = int(round(target_rim - brim_y))
        if paste_y >= -16:
            break
        scale *= 0.90

    assert hat is not None
    shift = max(0, TARGET_CROWN - crown0)

    # Shifted face
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(face0, (0, shift))

    # Hat on top
    canvas.alpha_composite(hat, (paste_x, paste_y))

    shifted = np.array(canvas)
    fs = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fs.alpha_composite(face0, (0, shift))
    fsa = np.array(fs)

    # Locate actual stripe brim row on the composited canvas
    brim_row = None
    for y in range(min(h - 1, target_rim + 8), max(0, TARGET_CROWN - 5), -1):
        hits = 0
        for x in range(max(0, int(cx) - 35), min(w, int(cx) + 36)):
            r_, g_, b_, al_ = (int(v) for v in shifted[y, x])
            if is_cone_stripe(r_, g_, b_, al_):
                hits += 1
        if hits >= 4:
            brim_row = y
            break

    # Thin hair strands over brim edge only (not through cone, not onto forehead).
    if brim_row is not None:
        cx_i = int(cx)
        hm = hair_mask(fsa, brim_row - 5, brim_row + 6)
        for y in range(brim_row - 4, min(h, brim_row + 5)):
            for x in range(max(0, cx_i - 50), min(w, cx_i + 51)):
                if hm[y, x] < 120:
                    continue
                r_, g_, b_, al_ = (int(v) for v in shifted[y, x])
                # Never wipe the cone body — only the brim lip / just under it
                if y < brim_row - 1 and is_cone_stripe(r_, g_, b_, al_):
                    continue
                shifted[y, x, 0] = fsa[y, x, 0]
                shifted[y, x, 1] = fsa[y, x, 1]
                shifted[y, x, 2] = fsa[y, x, 2]
                shifted[y, x, 3] = max(al_, int(hm[y, x]))

        # Fill clear pixels under brim with hair (kills black float gap)
        for y in range(brim_row, min(h, brim_row + 4)):
            for x in range(max(0, cx_i - 48), min(w, cx_i + 49)):
                al_ = int(shifted[y, x, 3])
                r_, g_, b_ = (int(v) for v in shifted[y, x, :3])
                if al_ >= 50 and r_ + g_ + b_ >= 40:
                    continue
                sr = sg = sb = sn = 0
                for yy2 in range(max(0, y - 4), min(h, y + 5)):
                    for xx2 in range(max(0, x - 4), min(w, x + 5)):
                        rr, gg, bb, aa = (int(v) for v in fsa[yy2, xx2])
                        if aa > 140 and max(rr, gg, bb) < 130:
                            sr += rr
                            sg += gg
                            sb += bb
                            sn += 1
                if sn:
                    shifted[y, x, 0] = sr // sn
                    shifted[y, x, 1] = sg // sn
                    shifted[y, x, 2] = sb // sn
                    shifted[y, x, 3] = 255

    # Soft circular crop with top headroom for pom
    yy, xx = np.mgrid[:h, :w]
    r = min(w, h) * 0.495
    dist = np.sqrt((xx - (w - 1) / 2) ** 2 + (yy - (h - 1) / 2) ** 2)
    face_alpha = np.clip((r + 0.5 - dist) * 255, 0, 255).astype(np.uint8)
    top_r = min(w, h) * 0.60
    top_dist = np.sqrt((xx - (w - 1) / 2) ** 2 + (yy - (h * 0.34)) ** 2)
    top_alpha = np.clip((top_r + 0.5 - top_dist) * 255, 0, 255).astype(np.uint8)
    upper = yy < (h * 0.48)
    combined = np.where(upper, np.maximum(face_alpha, top_alpha), face_alpha)
    shifted[:, :, 3] = np.minimum(shifted[:, :, 3], combined)
    near_white = (shifted[:, :, 0] > 230) & (shifted[:, :, 1] > 230) & (shifted[:, :, 2] > 230)
    rim_mask = (dist > r * 0.86) & (dist < r * 1.02)
    shifted[:, :, 3][near_white & rim_mask] = 0
    Image.fromarray(shifted, "RGBA").save(FACES / src.name)

    # Gap check: after hair stamp, any clear band between stripe and hair at cx?
    cx_i = w // 2
    hat_lo = None
    for y in range(min(h - 1, target_rim + 20), max(0, TARGET_CROWN - 30), -1):
        r_, g_, b_, al_ = (int(v) for v in shifted[y, cx_i])
        if is_cone_stripe(r_, g_, b_, al_):
            hat_lo = y
            break
    hair_at_rim = 0
    if hat_lo is not None:
        for x in range(cx_i - 20, cx_i + 21):
            r_, g_, b_, al_ = (int(v) for v in shifted[hat_lo, x])
            if al_ > 120 and max(r_, g_, b_) < 130 and r_ + g_ + b_ < 280:
                hair_at_rim += 1
    print(
        f"{src.name}: paste_y={paste_y} rim@{target_rim} hat_lo={hat_lo} "
        f"hair_px_on_rim_row={hair_at_rim}"
    )

print("done")
