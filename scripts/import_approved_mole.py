"""Import TopRock-approved mole body JPG → transparent PNG + head metrics."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = Path(
    r"C:\Users\user\AppData\Local\Cursor\AgentStores\cursor_agent_stores"
    r"\bc-f617877b-eaec-4432-8db1-768b13c985e8\files\media\whack-a-name"
    r"\whack-a-mole-body-blank-head.jpg"
)
OUT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\art\mole_body.png")
PREV = Path(r"C:\Users\user\Documents\whack-a-name\_mole_body_preview.png")
METRICS = Path(r"C:\Users\user\Documents\whack-a-name\_mole_body_metrics.txt")

# Final game sprite size (keep aspect, trim empty)
TARGET_W = 512


def main() -> None:
    raw = Image.open(SRC).convert("RGB")
    arr = np.asarray(raw).astype(np.float32)
    h, w = arr.shape[:2]

    # Checkerboard / light studio BG → alpha. Subject is chocolate fur (dark-mid brown).
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = (r + g + b) / 3.0
    sat = arr.max(axis=2) - arr.min(axis=2)

    # Near-white / light gray / pale checker
    pale = (lum > 210) | ((lum > 175) & (sat < 28))
    # Soft near-white fringes
    pale_soft = (lum > 155) & (sat < 22) & (r > 140) & (g > 140) & (b > 140)

    alpha = np.full((h, w), 255, dtype=np.uint8)
    alpha[pale] = 0
    alpha[pale_soft] = 0

    # Also kill any remaining pure checker mid-grays in corners
    # (light gray ~180 with low sat)
    grayish = (sat < 18) & (lum > 160) & (lum < 230)
    alpha[grayish] = 0

    rgba = np.dstack([arr.astype(np.uint8), alpha])
    img = Image.fromarray(rgba, "RGBA")

    # Crop to opaque bbox
    ys, xs = np.where(alpha > 40)
    pad = 6
    x0, x1 = max(0, int(xs.min()) - pad), min(w, int(xs.max()) + pad + 1)
    y0, y1 = max(0, int(ys.min()) - pad), min(h, int(ys.max()) + pad + 1)
    img = img.crop((x0, y0, x1, y1))

    # Soften matte edge slightly
    a = np.array(img)
    edge = Image.fromarray(a[:, :, 3], "L").filter(ImageFilter.GaussianBlur(0.8))
    ea = np.array(edge)
    # Keep interior fully opaque
    solid = ea > 90
    ea[solid] = 255
    a[:, :, 3] = ea
    img = Image.fromarray(a, "RGBA")

    # Resize to TARGET_W
    scale = TARGET_W / img.width
    nh = int(round(img.height * scale))
    img = img.resize((TARGET_W, nh), Image.Resampling.LANCZOS)

    # Find blank head dome centre (upper fur mass — brightest brown sphere region)
    a = np.array(img)
    opaque = a[:, :, 3] > 120
    ys, xs = np.where(opaque)
    top = int(ys.min())
    bot = int(ys.max())
    height = bot - top + 1
    # Head is roughly the top ~38% of the character
    head_band = opaque.copy()
    head_band[int(top + height * 0.42) :, :] = False
    hys, hxs = np.where(head_band)
    if len(hxs) < 50:
        raise SystemExit("could not locate head dome")
    head_cx = float(np.median(hxs))
    head_cy = float(np.percentile(hys, 45))  # centre of head mass
    # Estimate head radius from horizontal span at head_cy
    row = opaque[int(head_cy)]
    cols = np.where(row)[0]
    head_rx = (cols.max() - cols.min()) / 2.0 * 0.92
    head_ry = head_rx * 0.95

    head_from_top = head_cy / img.height  # origin-bottom body uses (1 - headFromTop) for headY
    # Face should cover ~78% of head diameter (decal on dome, not whole body)
    face_frac_of_body_h = (2 * head_rx * 0.78) / img.height

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)

    # Preview on dark + mark head/face circle
    prev = Image.new("RGB", img.size, (22, 12, 8))
    prev.paste(img, (0, 0), img)
    d = ImageDraw.Draw(prev)
    d.ellipse(
        (
            head_cx - head_rx,
            head_cy - head_ry,
            head_cx + head_rx,
            head_cy + head_ry,
        ),
        outline=(0, 255, 120),
        width=2,
    )
    fr = head_rx * 0.78
    d.ellipse(
        (head_cx - fr, head_cy - fr, head_cx + fr, head_cy + fr),
        outline=(255, 220, 0),
        width=2,
    )
    prev.save(PREV)

    metrics = "\n".join(
        [
            f"size={img.size}",
            f"head_cx={head_cx:.1f}",
            f"head_cy={head_cy:.1f}",
            f"head_rx={head_rx:.1f}",
            f"head_ry={head_ry:.1f}",
            f"headFromTop={head_from_top:.4f}",
            f"faceFracOfBodyH={face_frac_of_body_h:.4f}",
            f"aspect={img.width / img.height:.4f}",
        ]
    )
    METRICS.write_text(metrics, encoding="utf-8")
    print(metrics)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
