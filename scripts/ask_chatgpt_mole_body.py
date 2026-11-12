"""Ask ChatGPT Desktop to generate a fairground mole BODY sprite (blank head)."""
from __future__ import annotations

import ctypes
import time
from pathlib import Path

import pyautogui
import pyperclip
from PIL import ImageGrab

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
GetWindowTextW = user32.GetWindowTextW
IsWindowVisible = user32.IsWindowVisible
GetWindowTextLengthW = user32.GetWindowTextLengthW
ShowWindow = user32.ShowWindow
SetForegroundWindow = user32.SetForegroundWindow

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")

PROMPT = """Generate ONE image now (game sprite):

Carnival fairground WHACK-A-MOLE character BODY.
Front view. Plump soft chocolate-brown furry mole with rounded shoulders and chubby torso.
HEAD = blank smooth brown fur dome only — NO eyes, NO nose, NO mouth, NO whiskers, NO hat, NO accessories.
We overlay a photo face later. Cute painted plush carnival-booth art. Transparent or solid dark background.
NOT a peg, NOT a cylinder stick, NOT geometric primitives. No text.

Generate the image."""


def enum_windows():
    hits = []

    def foreach(hwnd, _lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                hits.append((hwnd, buf.value))
        return True

    EnumWindows(EnumWindowsProc(foreach), 0)
    return hits


def main() -> None:
    # Minimize Opera so it cannot steal focus / screenshots
    for hwnd, name in enum_windows():
        if "Opera" in name or "YouTube" in name:
            ShowWindow(hwnd, 6)  # SW_MINIMIZE
    time.sleep(0.4)

    chatgpt = [h for h, n in enum_windows() if n == "ChatGPT" or n.startswith("ChatGPT")]
    if not chatgpt:
        chatgpt = [h for h, n in enum_windows() if "ChatGPT" in n]
    if not chatgpt:
        raise SystemExit("no ChatGPT")
    hwnd = chatgpt[0]
    ShowWindow(hwnd, 3)  # maximize
    time.sleep(0.3)
    SetForegroundWindow(hwnd)
    time.sleep(0.8)

    # Confirm focus
    ImageGrab.grab().save(ROOT / "_chatgpt_mole_focus.png")

    pyautogui.hotkey("ctrl", "n")
    time.sleep(1.4)
    # Composer near bottom of maximized ChatGPT on 1440p-ish / 2560
    sw, sh = pyautogui.size()
    pyautogui.click(sw // 2, int(sh * 0.90))
    time.sleep(0.35)
    pyperclip.copy(PROMPT)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.45)
    pyautogui.press("enter")
    time.sleep(1.0)
    ImageGrab.grab().save(ROOT / "_chatgpt_mole_body_sent.png")
    print("sent")

    time.sleep(70)
    SetForegroundWindow(hwnd)
    time.sleep(0.4)
    ImageGrab.grab().save(ROOT / "_chatgpt_mole_body_wait.png")
    print("waited")


if __name__ == "__main__":
    main()
