"""Turn generated fairground mole art into a blank-head body sprite.

Face photo + party hat are layered in Phaser; this asset is torso + fur head dome.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = Path(
    r"C:\Users\user\AppData\Local\Cursor\AgentStores\cursor_agent_stores"
    r"\bc-f425ebc7-cc0c-567e-b4a8-cec4b7d5c8cc\files\media\assets\mole_body_fairground.jpg"
)
OUT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\art\mole_body.png")
W, H = 280, 320


def shade(base, t):
    r, g, b = base
    if t >= 0:
        return tuple(int(c + (255 - c) * t * 0.4) for c in (r, g, b))
    t = -t
    return tuple(int(c * (1 - 0.55 * t)) for c in (r, g, b))


def main() -> None:
    raw = Image.open(SRC).convert("RGB")
    # Crop subject tightly (generated art is centered with white/cream BG)
    arr = np.asarray(raw)
    # Non-background: not near-white / pale cream
    lum = arr.astype(np.float32).mean(axis=2)
    sat = arr.max(axis=2).astype(np.float32) - arr.min(axis=2).astype(np.float32)
    subject = (lum < 235) & ((sat > 18) | (lum < 200))
    ys, xs = np.where(subject)
    if len(xs) < 100:
        raise SystemExit("failed to find subject")
    pad = 8
    x0, x1 = max(0, xs.min() - pad), min(raw.width, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(raw.height, ys.max() + pad + 1)
    crop = raw.crop((x0, y0, x1, y1))
    c_arr = np.asarray(crop)
    c_lum = c_arr.astype(np.float32).mean(axis=2)
    c_sat = c_arr.max(axis=2).astype(np.float32) - c_arr.min(axis=2).astype(np.float32)
    mask = ((c_lum < 235) & ((c_sat > 18) | (c_lum < 200))).astype(np.uint8) * 255
    rgba = np.dstack([c_arr, mask])
    img = Image.fromarray(rgba, "RGBA")

    # Soften matte edge
    a = np.array(img)
    alpha = Image.fromarray(a[:, :, 3], "L").filter(ImageFilter.GaussianBlur(1.2))
    a[:, :, 3] = np.array(alpha)
    # Fully opaque where subject is solid
    a[a[:, :, 3] > 90, 3] = 255
    img = Image.fromarray(a, "RGBA")

    # Fit into canonical canvas (bottom-heavy origin for Phaser setOrigin 0.5,1)
    img = img.resize((W, int(W * img.height / img.width)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    oy = H - img.height
    if oy < 0:
        img = img.crop((0, -oy, W, img.height))
        oy = 0
    canvas.paste(img, (0, oy), img)
    img = canvas
    a = np.array(img)

    # Locate head region (upper third opaque mass) and paint blank fur dome over face+hat
    opaque = a[:, :, 3] > 120
    ys, xs = np.where(opaque)
    cx = int(np.median(xs))
    top_y = int(ys.min())
    bot_y = int(ys.max())
    height = bot_y - top_y + 1
    # Face sits roughly in upper 42% of character
    head_cy = top_y + int(height * 0.28)
    head_rx = int(W * 0.34)
    head_ry = int(height * 0.28)

    fur = (122, 78, 48)
    fur_hi = (168, 118, 78)
    fur_lo = (72, 44, 28)

    # Sample actual fur colour from cheeks (left/right of face)
    sample_pts = []
    for dx in (-int(head_rx * 0.85), int(head_rx * 0.85)):
        for dy in (0, int(head_ry * 0.35)):
            x, y = cx + dx, head_cy + dy
            if 0 <= x < W and 0 <= y < H and a[y, x, 3] > 180:
                sample_pts.append(a[y, x, :3].astype(np.float32))
    if sample_pts:
        fur = tuple(int(c) for c in np.mean(sample_pts, axis=0))
        fur_hi = shade(fur, 0.35)
        fur_lo = shade(fur, -0.35)

    # Erase hat: anything above head_cy - head_ry * 0.55 becomes transparent then refill dome
    hat_cut = head_cy - int(head_ry * 0.55)
    for y in range(0, max(0, hat_cut)):
        for x in range(W):
            if a[y, x, 3] > 0:
                # keep only if clearly brown fur (not red/yellow hat)
                r, g, b = a[y, x, :3]
                if r > 160 and g < 120:  # party hat reds
                    a[y, x, 3] = 0
                elif r > 180 and g > 150 and b < 100:  # yellow brim
                    a[y, x, 3] = 0

    # Paint blank fur head over facial features (eyes/nose/mouth)
    for y in range(max(0, head_cy - head_ry), min(H, head_cy + head_ry + 1)):
        for x in range(max(0, cx - head_rx), min(W, cx + head_rx + 1)):
            u = (x - cx) / head_rx
            v = (y - head_cy) / head_ry
            d2 = u * u + v * v
            if d2 > 1.0:
                continue
            z = np.sqrt(max(0.0, 1.0 - d2))
            lit = 0.2 + 0.8 * max(0.0, 0.45 * (-u) + 0.3 * (-v) + 0.55 * z)
            base = fur_hi if lit > 0.78 else fur
            if v > 0.45:
                base = fur_lo
            r, g, b = shade(base, lit - 0.5)
            n = ((x * 13 + y * 23) % 7) - 3
            r, g, b = [int(np.clip(c + n, 0, 255)) for c in (r, g, b)]
            # Strong overwrite in face centre; soft blend at edges
            face_w = 1.0 if d2 < 0.55 else max(0.0, 1.0 - (d2 - 0.55) / 0.45)
            # Always opaque fur on dome
            edge = 1.0 if d2 < 0.9 else max(0.0, 1.0 - (d2 - 0.9) / 0.1)
            prev = a[y, x]
            if prev[3] < 40:
                a[y, x] = (r, g, b, int(255 * edge))
            else:
                t = 0.55 + 0.45 * face_w
                a[y, x, 0] = int(prev[0] * (1 - t) + r * t)
                a[y, x, 1] = int(prev[1] * (1 - t) + g * t)
                a[y, x, 2] = int(prev[2] * (1 - t) + b * t)
                a[y, x, 3] = 255

    # Ensure no light beige paddle: darken any remaining light belly strip in lower torso
    for y in range(int(H * 0.55), H):
        for x in range(W):
            if a[y, x, 3] < 40:
                continue
            r, g, b = [int(v) for v in a[y, x, :3]]
            if r > 150 and g > 130 and b > 100:
                a[y, x, 0] = int(r * 0.55 + fur_lo[0] * 0.45)
                a[y, x, 1] = int(g * 0.5 + fur_lo[1] * 0.5)
                a[y, x, 2] = int(b * 0.45 + fur_lo[2] * 0.55)

    img = Image.fromarray(a, "RGBA")
    # Feather bottom edge slightly so it sinks into the well
    bottom = Image.new("L", (W, H), 255)
    bd = ImageDraw.Draw(bottom)
    bd.rectangle((0, H - 28, W, H), fill=0)
    bottom = bottom.filter(ImageFilter.GaussianBlur(10))
    ba = np.array(img)
    ba[:, :, 3] = (ba[:, :, 3].astype(np.float32) * (np.asarray(bottom) / 255.0)).astype(np.uint8)
    # keep mid-body fully opaque
    ba[ba[:, :, 3] > 200, 3] = 255
    img = Image.fromarray(ba, "RGBA")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    prev = Image.new("RGB", (W, H), (28, 18, 14))
    prev.paste(img, (0, 0), img)
    prev.save(Path(r"C:\Users\user\Documents\whack-a-name\_mole_body_preview.png"))
    print("wrote", OUT, img.size, "head_cy", head_cy, "head_from_top", round(head_cy / H, 3))


if __name__ == "__main__":
    main()
