"""Verify hat brim seats on hair in baked assets AND in the pose screenshot."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")


def is_hat(r, g, b, al=255):
    if al < 80:
        return False
    if r > 190 and g > 140 and b < 90 and (r - b) > 100:
        return True
    if 30 < r < 180 and g > 145 and b > 120 and g > r + 10:
        return True
    return False


def is_hair(r, g, b, al=255):
    if al < 80:
        return False
    if is_hat(r, g, b, al):
        return False
    # include lifted crown browns (up to ~150) used for game-scale readability
    return max(r, g, b) < 155 and abs(r - g) < 50 and b < 110


def is_skin(r, g, b, al=255):
    if al < 80:
        return False
    return r > 160 and g > 110 and b > 85 and max(r, g, b) > 150


print("=== BAKED ASSETS ===")
for p in sorted((ROOT / "public/assets/faces").glob("face_*.png")):
    a = np.array(Image.open(p))
    h, w = a.shape[:2]
    cx = w // 2
    brim = None
    for y in range(h - 1, -1, -1):
        if any(is_hat(*(int(v) for v in a[y, x])) for x in range(cx - 25, cx + 26)):
            brim = y
            break
    if brim is None:
        print(p.name, "NO HAT")
        continue
    hair_rows = 0
    for y in range(brim + 1, min(h, brim + 40)):
        if sum(1 for x in range(cx - 30, cx + 31) if is_hair(*(int(v) for v in a[y, x]))) >= 8:
            hair_rows += 1
        elif sum(1 for x in range(cx - 30, cx + 31) if is_skin(*(int(v) for v in a[y, x]))) >= 8:
            break
    print(f"{p.name}: brim@{brim} hair_rows_under={hair_rows}")

print("\n=== POSE HOLES (center column) ===")
a = np.array(Image.open(ROOT / "_shot_pose.png").convert("RGB"))
dump = json.loads((ROOT / "_pose_dump.json").read_text())
for h in dump:
    x = int(h["root"]["x"])
    y = int(h["root"]["y"])
    fw = int(h["face"]["w"])
    top = y - fw // 2
    # find brim in upper 55% of face
    brim = None
    for yy in range(top + int(fw * 0.55), top - 1, -1):
        if yy < 0 or yy >= a.shape[0]:
            continue
        if any(is_hat(*(int(v) for v in a[yy, xx])) for xx in range(x - 20, x + 21)):
            brim = yy
            break
    if brim is None:
        print(f"hole {h['i']}: NO HAT found")
        continue
    hair_rows = 0
    void_rows = 0
    skin_hit = False
    for yy in range(brim + 1, brim + 45):
        if yy >= a.shape[0]:
            break
        band = [tuple(int(v) for v in a[yy, xx]) for xx in range(x - 22, x + 23)]
        hc = sum(1 for r, g, b in band if is_hair(r, g, b))
        sc = sum(1 for r, g, b in band if is_skin(r, g, b))
        dark = sum(1 for r, g, b in band if max(r, g, b) < 45)
        if sc >= 8:
            skin_hit = True
            break
        if hc >= 8:
            hair_rows += 1
        elif dark >= 20:
            void_rows += 1
    status = "SEATED" if hair_rows >= 4 and void_rows < 3 else "GAP?"
    print(
        f"hole {h['i']}: brim@{brim} hair_under={hair_rows} void_under={void_rows} "
        f"skin_after={skin_hit} -> {status}"
    )
