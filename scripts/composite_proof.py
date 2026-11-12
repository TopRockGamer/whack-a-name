"""Ground-truth composite: backdrop + faces + hats at Phaser dump coords."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
STORE = Path(
    r"C:\Users\user\AppData\Local\Cursor\AgentStores\cursor_agent_stores"
    r"\bc-f617877b-eaec-4432-8db1-768b13c985e8\files\media\whack-a-name"
)
dump = json.loads((ROOT / "_pose_dump.json").read_text(encoding="utf-8"))
bg = Image.open(ROOT / "public/assets/art/backdrop.png").convert("RGBA")
hat_src = Image.open(ROOT / "public/assets/art/party_hat.png").convert("RGBA")
faces_dir = ROOT / "public/assets/faces"
face_files = sorted(faces_dir.glob("face_*.png"))

out = bg.copy()
draw = ImageDraw.Draw(out)

for m in dump:
    i = m["i"]
    fx, fy = m["root"]["x"], m["root"]["y"]
    face_px = m["face"]["w"]
    face = Image.open(face_files[i % len(face_files)]).convert("RGBA")
    face = face.resize((face_px, face_px), Image.Resampling.LANCZOS)
    # circular alpha
    mask = Image.new("L", (face_px, face_px), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, face_px - 1, face_px - 1], fill=255)
    face.putalpha(mask)
    out.alpha_composite(face, (int(fx - face_px / 2), int(fy - face_px / 2)))

    # hat at dump transform
    scale = m["hat"]["scale"]
    oy = m["hat"]["originY"]
    ox = 0.5
    angle = -8
    hw = int(hat_src.width * scale)
    hh = int(hat_src.height * scale)
    hat = hat_src.resize((hw, hh), Image.Resampling.LANCZOS).rotate(
        -angle, expand=True, resample=Image.Resampling.BICUBIC
    )
    # After rotate, origin shifts — approximate: place so origin point = world attach
    # Simpler: paste with origin before rotate using affine
    hat2 = hat_src.resize((hw, hh), Image.Resampling.LANCZOS)
    # origin pixel
    ox_px, oy_px = ox * hw, oy * hh
    # rotate around origin
    hat2 = hat2.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True, center=(ox_px, oy_px))
    # After expand+center rotate, the origin stays roughly at center of new image? 
    # PIL rotate with center keeps that point in place within expanded canvas... actually not guaranteed.
    # Use dump worldY and root x
    attach_x = fx + m["hat"]["x"]
    attach_y = m["hat"]["worldY"]
    # Find opaque centroid bottom as brim fallback: paste so bottom-ish at attach
    arr = np.array(hat2)
    a = arr[:, :, 3]
    ys, xs = np.where(a > 20)
    if len(xs):
        # use configured origin fraction on unrotated; for rotated use bbox bottom-center * 0.86 of height from top
        top, bot = ys.min(), ys.max()
        left, right = xs.min(), xs.max()
        brim_x = (left + right) / 2
        brim_y = top + (bot - top) * oy
        paste_x = int(attach_x - brim_x)
        paste_y = int(attach_y - brim_y)
        out.alpha_composite(hat2, (paste_x, paste_y))
        draw.ellipse([attach_x - 3, attach_y - 3, attach_x + 3, attach_y + 3], fill=(0, 180, 255, 255))

    # hole marker
    hx, hy = m["hole"]["x"], m["hole"]["y"]
    draw.ellipse([hx - 4, hy - 4, hx + 4, hy + 4], outline=(255, 0, 0, 255))

out_rgb = out.convert("RGB")
out_rgb.save(ROOT / "_composite_proof.png")
STORE.mkdir(parents=True, exist_ok=True)
out_rgb.save(STORE / "_composite_proof.png")
# crops
for m in dump:
    hx, hy = m["hole"]["x"], m["hole"]["y"]
    out_rgb.crop((hx - 90, hy - 140, hx + 90, hy + 70)).save(ROOT / f"_comp_{m['i']}.png")
print("wrote composite proof")
