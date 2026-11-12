"""Open http://localhost:5188/?pose=1 in Opera (reuse tab) and capture canvas."""
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
URL = "http://localhost:5188/?pose=1"

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
        time.sleep(0.2)


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


def crop_game(full: Image.Image) -> Image.Image:
    """Crop centered 16:9 game canvas from Opera content area."""
    w, h = full.size
    # Opera GX maximized: left sidebar ~56-72, top chrome ~100-140, bottom taskbar ~48
    # Prefer locating parchment banner cream band near top of canvas
    best = None
    for y in range(90, 280):
        creams = []
        for x in range(200, w - 200, 3):
            r, g, b = full.getpixel((x, y))[:3]
            # parchment cream
            if r > 200 and 160 < g < 230 and 100 < b < 190 and r >= g >= b:
                creams.append(x)
        if len(creams) > 40:
            best = (min(creams), y, max(creams))
            break
    if best:
        bx0, by, bx1 = best
        # Banner ~650px wide centered at game x=640, game y~105
        banner_w = bx1 - bx0
        scale = banner_w / 650.0
        left = int(bx0 - 315 * scale)
        top = int(by - 105 * scale)
        right = int(left + 1280 * scale)
        bottom = int(top + 720 * scale)
        left, top = max(0, left), max(0, top)
        right, bottom = min(w, right), min(h, bottom)
        print(f"banner crop scale={scale:.3f} box=({left},{top},{right},{bottom})")
        return full.crop((left, top, right, bottom)).resize((1280, 720), Image.Resampling.LANCZOS)

    # Fallback: content region aspect-fit
    content_left, content_top = 70, 110
    content_right, content_bottom = w - 20, h - 55
    cw = content_right - content_left
    ch = content_bottom - content_top
    # largest 16:9 inside content
    if cw / ch > 16 / 9:
        gh = ch
        gw = int(gh * 16 / 9)
        left = content_left + (cw - gw) // 2
        top = content_top
    else:
        gw = cw
        gh = int(gw * 9 / 16)
        left = content_left
        top = content_top + (ch - gh) // 2
    print(f"fallback crop box=({left},{top},{left+gw},{top+gh})")
    return full.crop((left, top, left + gw, top + gh)).resize((1280, 720), Image.Resampling.LANCZOS)


def has_play_button(img: Image.Image) -> bool:
    """Gold PLAY button near bottom center of 1280x720 crop."""
    gold = 0
    for y in range(580, 680, 2):
        for x in range(560, 720, 2):
            r, g, b = img.getpixel((x, y))[:3]
            if r > 180 and 120 < g < 220 and b < 80:
                gold += 1
    return gold > 40


def has_pose_timer(img: Image.Image) -> bool:
    """POSE text is top-right HUD in pose mode (light cream glyphs)."""
    # crude: look for non-menu — no PLAY gold + some face-ish pixels in hole band
    if has_play_button(img):
        return False
    faceish = 0
    for y in range(330, 520, 3):
        for x in range(400, 1200, 3):
            r, g, b = img.getpixel((x, y))[:3]
            # circular face sprites have varied color; count non-wood saturated pixels in hole zone
            if abs(r - g) > 25 or abs(g - b) > 25:
                if 40 < r < 250 and 30 < g < 230:
                    faceish += 1
    return faceish > 200


def main():
    minimize_chatgpt()
    ops = find_hwnd("Opera")
    if not ops:
        raise SystemExit("Opera not found")
    pref = [h for h in ops if "Whack" in h[1] or "localhost" in h[1].lower() or "5188" in h[1]]
    hwnd, title = (pref or ops)[0]
    print("focus", title)
    focus_hwnd(hwnd)

    # Type URL explicitly so ?pose=1 is not stripped
    pyautogui.hotkey("ctrl", "l")
    time.sleep(0.25)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.08)
    pyautogui.press("backspace")
    time.sleep(0.05)
    pyautogui.typewrite(URL, interval=0.02)
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(4.0)
    # Force reload to ensure POSE_MODE module evaluates with query
    pyautogui.hotkey("ctrl", "shift", "r")
    time.sleep(4.0)

    full = ImageGrab.grab()
    full.save(ROOT / "_pose_full.png")
    print("desktop", full.size, "center", full.getpixel((full.size[0] // 2, full.size[1] // 2))[:3])

    pose = crop_game(full)
    pose.save(ROOT / "_fix_pose.png")
    print("play_btn", has_play_button(pose), "poseish", has_pose_timer(pose))

    if has_play_button(pose):
        # Still on menu — try once more with enter after selecting omnibox
        print("WARN still menu — retrying navigation")
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.2)
        pyautogui.typewrite(URL, interval=0.025)
        pyautogui.press("enter")
        time.sleep(4.5)
        full = ImageGrab.grab()
        full.save(ROOT / "_pose_full.png")
        pose = crop_game(full)
        pose.save(ROOT / "_fix_pose.png")
        print("retry play_btn", has_play_button(pose), "poseish", has_pose_timer(pose))

    pose.save(STORE / "_fix_pose.png")
    pose.save(STORE / "play-aligned.png")
    pose.save(STORE / "play.png")
    print("saved", STORE / "_fix_pose.png", pose.size)


if __name__ == "__main__":
    main()
