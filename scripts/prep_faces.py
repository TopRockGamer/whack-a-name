"""Prep TopRock face PNGs: strip black bg, circular soft mask, sized for holes."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SRC = Path(r"C:\Users\user\Downloads\Face_Pop_8_Separate_PNGs")
OUT = Path(r"C:\Users\user\Documents\whack-a-name\public\assets\faces")
SIZE = 256


def prep_one(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGBA")
    # Remove near-black corners outside the white ring
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r < 18 and g < 18 and b < 18:
                px[x, y] = (0, 0, 0, 0)

    # Soft circular mask inset slightly from edges
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    inset = int(min(w, h) * 0.03)
    draw.ellipse((inset, inset, w - inset, h - inset), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.5))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)

    # Normalize size
    out = out.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f"wrote {dst.name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC.glob("face_*.png")):
        prep_one(src, OUT / src.name)


if __name__ == "__main__":
    main()
