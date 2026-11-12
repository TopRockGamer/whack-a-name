from pathlib import Path
import json
from PIL import Image, ImageDraw

im = Image.open(r"C:\Users\user\Documents\whack-a-name\_fix_pose.png").convert("RGBA")
d = ImageDraw.Draw(im)
dump = json.load(open(r"C:\Users\user\Documents\whack-a-name\_pose_dump.json"))
for m in dump:
    hx, hy = m["hole"]["x"], m["hole"]["y"]
    fx, fy = m["root"]["x"], m["root"]["y"]
    hw = m["hat"]["worldY"]
    hh = m["hat"]["displayH"]
    oy = m["hat"]["originY"]
    top = hw - oy * hh
    bot = hw + (1 - oy) * hh
    d.ellipse([hx - 45, hy - 30, hx + 45, hy + 30], outline=(255, 0, 0, 255), width=2)
    r = m["face"]["w"] / 2
    d.ellipse([fx - r, fy - r, fx + r, fy + r], outline=(0, 255, 0, 255), width=2)
    d.line([(fx - 25, hw), (fx + 25, hw)], fill=(0, 150, 255, 255), width=3)
    d.rectangle([fx - 30, top, fx + 30, bot], outline=(255, 0, 255, 255), width=2)
    print(f"mole {m['i']}: face=({fx},{fy}) hat_attach={hw:.0f} hat_box=[{top:.0f},{bot:.0f}]")

out = Path(r"C:\Users\user\Documents\whack-a-name\_fix_pose_marked.png")
im.convert("RGB").save(out)
store = Path(
    r"C:\Users\user\AppData\Local\Cursor\AgentStores\cursor_agent_stores"
    r"\bc-f617877b-eaec-4432-8db1-768b13c985e8\files\media\whack-a-name"
)
im.convert("RGB").save(store / "_fix_pose_marked.png")
im.convert("RGB").save(store / "play-aligned.png")
im.convert("RGB").save(store / "play.png")
print("saved", out)
