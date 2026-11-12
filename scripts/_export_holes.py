from pathlib import Path
import json
from PIL import Image

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
im = Image.open(ROOT / "_shot_pose.png")
dump = json.loads((ROOT / "_pose_dump.json").read_text())
out = ROOT / "_holes"
out.mkdir(exist_ok=True)
for h in dump:
    # Crop around the painted hole centre (not body origin / feet)
    hole = h["hole"]
    x, y = int(hole["x"]), int(hole["y"])
    box = (x - 85, y - 95, x + 85, y + 85)
    im.crop(box).save(out / f"hole_{h['i']}.png")
    print("wrote", h["i"], box)
