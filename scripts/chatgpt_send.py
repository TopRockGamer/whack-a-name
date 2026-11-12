"""Send a prompt to ChatGPT Desktop and optionally wait/screenshot."""
from __future__ import annotations

import argparse
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


def find_chatgpt() -> int:
    hwnds: list[int] = []

    def foreach(hwnd, _lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                if buf.value == "ChatGPT":
                    hwnds.append(hwnd)
        return True

    EnumWindows(EnumWindowsProc(foreach), 0)
    if not hwnds:
        raise SystemExit("ChatGPT window not found")
    return hwnds[0]


def focus(hwnd: int) -> None:
    user32.ShowWindow(hwnd, 3)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.45)


def send_prompt(text: str, shot: Path | None = None) -> None:
    hwnd = find_chatgpt()
    focus(hwnd)
    pyperclip.copy(text)
    # click composer
    pyautogui.click(1280, 1260)
    time.sleep(0.25)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.35)
    pyautogui.press("enter")
    time.sleep(1.0)
    if shot:
        ImageGrab.grab().save(shot)
        print(f"saved {shot}")
    print("sent")


def screenshot(path: Path) -> None:
    hwnd = find_chatgpt()
    focus(hwnd)
    ImageGrab.grab().save(path)
    print(f"saved {path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, help="Prompt file to send")
    ap.add_argument("--text", type=str, help="Prompt text to send")
    ap.add_argument("--shot", type=Path, help="Screenshot path after send/focus")
    ap.add_argument("--screenshot-only", action="store_true")
    args = ap.parse_args()
    if args.screenshot_only:
        screenshot(args.shot or Path("_chatgpt_shot.png"))
        return
    text = args.text
    if args.file:
        text = args.file.read_text(encoding="utf-8")
    if not text:
        raise SystemExit("Need --file or --text")
    send_prompt(text, args.shot)


if __name__ == "__main__":
    main()
