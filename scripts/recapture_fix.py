"""Focus Opera, open pose mode, crop the Phaser canvas, save proof shots."""
from __future__ import annotations

import ctypes
import time
from pathlib import Path

import pyautogui
from PIL import Image, ImageGrab

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
STORE = Path(
    r"C:\Users\user\AppData\Local\Cursor\AgentStores\cursor_agent_stores"
    r"\bc-f617877b-eaec-4432-8db1-768b13c985e8\files\media\whack-a-name"
)
STORE.mkdir(parents=True, exist_ok=True)

user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
GetWindowTextW = user32.GetWindowTextW
IsWindowVisible = user32.IsWindowVisible
GetWindowTextLengthW = user32.GetWindowTextLengthW


def find_hwnd(substr: str):
    found = []

    def foreach(hwnd, _lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                if substr in buf.value:
                    found.append((hwnd, buf.value))
        return True

    EnumWindows(EnumWindowsProc(foreach), 0)
    return found


def minimize_chatgpt():
    for hwnd, name in find_hwnd("ChatGPT"):
        print("minimize", name)
        user32.ShowWindow(hwnd, 6)
        time.sleep(0.25)


def focus_hwnd(hwnd):
    fg = user32.GetForegroundWindow()
    user32.AttachThreadInput(
        user32.GetWindowThreadProcessId(fg, None),
        user32.GetWindowThreadProcessId(hwnd, None),
        True,
    )
    user32.ShowWindow(hwnd, 9)
    user32.ShowWindow(hwnd, 3)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(
        user32.GetWindowThreadProcessId(fg, None),
        user32.GetWindowThreadProcessId(hwnd, None),
        False,
    )
    time.sleep(0.6)


def navigate(url: str):
    pyautogui.hotkey("ctrl", "l")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    # paste is more reliable than typewrite for URLs
    import subprocess

    subprocess.run(["powershell", "-NoProfile", "-Command", f'Set-Clipboard -Value "{url}"'], check=True)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.15)
    pyautogui.press("enter")


def find_canvas_box(img: Image.Image):
    """Locate 1280:720 Phaser canvas by matching backdrop awning red stripe band."""
    w, h = img.size
    arr_w_step = 3
    # Red scalloped awning near top of canvas — strong red pixels in a horizontal band
    best = None
    for y in range(40, min(400, h - 100)):
        reds = []
        for x in range(0, w, arr_w_step):
            r, g, b = img.getpixel((x, y))[:3]
            if r > 160 and g < 90 and b < 90:
                reds.append(x)
        if len(reds) > 60:
            # contiguous-ish span
            span = max(reds) - min(reds)
            if span > 400:
                best = (min(reds), y, max(reds), len(reds))
                break
    if not best:
        # try wooden table brown band lower
        for y in range(int(h * 0.45), int(h * 0.75)):
            browns = []
            for x in range(0, w, arr_w_step):
                r, g, b = img.getpixel((x, y))[:3]
                if 90 < r < 180 and 50 < g < 130 and b < 90 and r > g > b:
                    browns.append(x)
            if len(browns) > 80:
                left = min(browns)
                right = max(browns)
                span = right - left
                if span > 500:
                    # estimate: table spans most of canvas width
                    scale = span / 1280.0
                    # table y ~ 450-600 in game; use mid
                    top = int(y - 520 * scale)
                    left_c = int(left - 0 * scale)
                    return (
                        max(0, left_c),
                        max(0, top),
                        min(w, left_c + int(1280 * scale)),
                        min(h, top + int(720 * scale)),
                        scale,
                    )
        raise SystemExit("canvas not found")

    left_awning, y_awning, right_awning, _n = best
    # Awning spans nearly full canvas width (~1280)
    span = right_awning - left_awning
    scale = span / 1280.0 if span > 200 else 1.0
    # awning top edge is near y~0-40 of canvas
    top = int(y_awning - 20 * scale)
    left = int(left_awning)
    right = int(left + 1280 * scale)
    bottom = int(top + 720 * scale)
    # clamp
    left = max(0, left)
    top = max(0, top)
    right = min(w, right)
    bottom = min(h, bottom)
    # If aspect drifted, force 16:9 from width
    if right - left > 100:
        bottom = min(h, top + int((right - left) * 720 / 1280))
    print(f"canvas box=({left},{top},{right},{bottom}) scale={scale:.3f} awning_y={y_awning}")
    return left, top, right, bottom, scale


def crop_canvas(full: Image.Image) -> Image.Image:
    left, top, right, bottom, _ = find_canvas_box(full)
    crop = full.crop((left, top, right, bottom)).resize((1280, 720), Image.Resampling.LANCZOS)
    return crop


def save(name: str, crop: Image.Image, also_store_names: list[str] | None = None):
    path = ROOT / f"_fix_{name}.png"
    crop.save(path)
    print("saved", path, crop.size)
    targets = also_store_names or [f"_fix_{name}.png"]
    for t in targets:
        dest = STORE / t
        crop.save(dest)
        print("store", dest)


def main():
    minimize_chatgpt()
    hits = find_hwnd("Opera")
    # Prefer Whack / localhost titles
    preferred = [h for h in hits if "Whack" in h[1] or "localhost" in h[1].lower() or "5188" in h[1]]
    hwnd = (preferred or hits)[0][0]
    print("focus", (preferred or hits)[0][1])
    focus_hwnd(hwnd)

    # Pose mode for all-moles-up proof
    navigate("http://localhost:5188/?pose=1")
    time.sleep(3.5)
    # hard reload once to pick up HMR
    pyautogui.hotkey("ctrl", "shift", "r")
    time.sleep(3.5)

    full = ImageGrab.grab()
    full.save(ROOT / "_fix_desktop_pose.png")
    print("desktop", full.size, "center", full.getpixel((full.size[0] // 2, full.size[1] // 2))[:3])

    # Sanity: must NOT be magenta ChatGPT sheet
    cx, cy = full.size[0] // 2, full.size[1] // 2
    r, g, b = full.getpixel((cx, cy))[:3]
    if r > 200 and b > 200 and g < 80:
        raise SystemExit("Captured ChatGPT magenta sheet — wrong window")

    pose = crop_canvas(full)
    save("pose", pose, ["_fix_pose.png", "play-aligned.png", "play.png"])

    # Also capture normal menu + short play
    navigate("http://localhost:5188/")
    time.sleep(2.8)
    full_m = ImageGrab.grab()
    menu = crop_canvas(full_m)
    save("menu", menu, ["_fix_menu.png", "menu.png"])

    # Start play via Space
    pyautogui.press("space")
    time.sleep(1.5)
    # grab a few frames hoping moles are up
    best = None
    best_skin = -1
    for i in range(10):
        time.sleep(0.55)
        full_p = ImageGrab.grab()
        play = crop_canvas(full_p)
        skin = 0
        pw, ph = play.size
        for yy in range(int(ph * 0.35), int(ph * 0.85), 5):
            for xx in range(int(pw * 0.2), int(pw * 0.95), 5):
                rr, gg, bb = play.getpixel((xx, yy))[:3]
                if rr > 130 and 70 < gg < 210 and bb < 170 and rr > gg and rr > bb:
                    skin += 1
        print(f"play frame {i} skin={skin}")
        if skin > best_skin:
            best_skin = skin
            best = play
        if skin > 80:
            break
    if best is None:
        raise SystemExit("no play frames")
    save("play", best, ["_fix_play.png", "play2.png"])

    # End card: wait out is long; jump via console not available — skip or click through
    # Navigate pose again as secondary hats proof already saved
    print("done skin_best", best_skin)


if __name__ == "__main__":
    main()
