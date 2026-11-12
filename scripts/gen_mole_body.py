"""Paint a stronger 2.5D fairground mole: round head + shaded cylinder torso."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\art\mole_body.png")
W, H = 256, 320


def shade(base, t):
    r, g, b = base
    if t >= 0:
        return (
            int(r + (255 - r) * t * 0.4),
            int(g + (255 - g) * t * 0.4),
            int(b + (255 - b) * t * 0.4),
        )
    t = -t
    return (int(r * (1 - 0.5 * t)), int(g * (1 - 0.5 * t)), int(b * (1 - 0.5 * t)))


def main() -> None:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()

    cx = W // 2
    head_cy = 78
    head_rx, head_ry = 82, 76
    cyl_top = head_cy + 22
    cyl_bot = H - 12
    cyl_rx = 74

    fur = (176, 118, 76)
    belly = (222, 178, 128)

    # Cylinder with clear left/right rim shading (reads as round at game scale)
    for y in range(cyl_top, cyl_bot):
        taper = 1.0 - 0.1 * ((y - cyl_top) / max(1, cyl_bot - cyl_top))
        rx = max(8, int(cyl_rx * taper))
        for x in range(cx - rx, cx + rx + 1):
            u = (x - cx) / max(1, rx)
            # Stronger Lambert cylinder: dark edges, bright front-left
            lit = 0.25 + 0.75 * max(0.0, 0.85 * np.sqrt(max(0.0, 1 - u * u)) + 0.15 * (-u))
            base = belly if abs(u) < 0.32 else fur
            depth = (y - cyl_top) / max(1, cyl_bot - cyl_top)
            base = shade(base, -0.3 * depth)
            r, g, b = shade(base, lit - 0.55)
            n = ((x * 17 + y * 31) % 9) - 4
            r = int(np.clip(r + n, 0, 255))
            g = int(np.clip(g + n // 2, 0, 255))
            b = int(np.clip(b + n // 3, 0, 255))
            edge = 1.0 if abs(u) < 0.9 else max(0.0, 1.0 - (abs(u) - 0.9) / 0.1)
            a = int(255 * edge)
            if a > 0:
                px[x, y] = (r, g, b, a)

    # Spherical head — clearly round
    for y in range(head_cy - head_ry, head_cy + head_ry + 1):
        for x in range(cx - head_rx, cx + head_rx + 1):
            u = (x - cx) / head_rx
            v = (y - head_cy) / head_ry
            d2 = u * u + v * v
            if d2 > 1.0:
                continue
            z = np.sqrt(max(0.0, 1.0 - d2))
            lit = 0.2 + 0.8 * max(0.0, 0.5 * (-u) + 0.35 * (-v) + 0.65 * z)
            base = shade(fur, -0.25) if v > 0.4 else fur
            r, g, b = shade(base, lit - 0.5)
            n = ((x * 13 + y * 19) % 9) - 4
            r = int(np.clip(r + n, 0, 255))
            g = int(np.clip(g + n // 2, 0, 255))
            b = int(np.clip(b + n // 3, 0, 255))
            edge = 1.0 if d2 < 0.86 else max(0.0, 1.0 - (d2 - 0.86) / 0.14)
            a = int(255 * edge)
            if a <= 0:
                continue
            prev = px[x, y]
            if prev[3] > 180 and y > head_cy + 18:
                t = 0.4
                px[x, y] = (
                    int(prev[0] * (1 - t) + r * t),
                    int(prev[1] * (1 - t) + g * t),
                    int(prev[2] * (1 - t) + b * t),
                    255,
                )
            else:
                px[x, y] = (r, g, b, a)

    # Specular on head
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((cx - 40, head_cy - 48, cx - 4, head_cy - 12), fill=(255, 235, 200, 70))
    img = Image.alpha_composite(img, overlay.filter(ImageFilter.GaussianBlur(3)))

    # Face plate (subtle) — where the photo decal sits
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.ellipse((cx - 54, head_cy - 42, cx + 54, head_cy + 50), fill=(80, 48, 30, 40))
    img = Image.alpha_composite(img, plate)

    # Contact shadow at feet
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((cx - 68, cyl_bot - 16, cx + 68, cyl_bot + 12), fill=(15, 8, 4, 120))
    img = Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)), img)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print("wrote", OUT, img.size)


if __name__ == "__main__":
    main()
